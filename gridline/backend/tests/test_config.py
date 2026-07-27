"""Settings must survive the environment variables we actually ship.

Regression cover for a boot-time crash: `CORS_ORIGINS=http://localhost:3000` —
the exact value set in docker-compose.yml and the k8s ConfigMap — made
pydantic-settings try to JSON-decode a complex-typed field and raise before the
app could import.
"""

from app.config import Settings


class TestCorsOrigins:
    def test_single_origin_from_env(self, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
        assert Settings(_env_file=None).cors_origins == ["http://localhost:3000"]

    def test_comma_separated_origins_from_env(self, monkeypatch):
        monkeypatch.setenv(
            "CORS_ORIGINS", "https://gridline.chargebotic.com, http://localhost:3000"
        )
        assert Settings(_env_file=None).cors_origins == [
            "https://gridline.chargebotic.com",
            "http://localhost:3000",
        ]

    def test_blank_entries_are_dropped(self, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", "http://a.test,,  ,http://b.test")
        assert Settings(_env_file=None).cors_origins == ["http://a.test", "http://b.test"]

    def test_default_when_unset(self, monkeypatch):
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
        assert Settings(_env_file=None).cors_origins == ["http://localhost:3000"]

    def test_a_json_array_still_works(self, monkeypatch):
        # Some deployment tooling emits JSON for list-valued settings.
        monkeypatch.setenv("CORS_ORIGINS", '["http://a.test","http://b.test"]')
        origins = Settings(_env_file=None).cors_origins
        assert "http://a.test" in origins[0]


class TestDerivedFlags:
    def test_storage_is_s3_requires_both_credentials(self, monkeypatch):
        monkeypatch.setenv("S3_ACCESS_KEY_ID", "key")
        monkeypatch.delenv("S3_SECRET_ACCESS_KEY", raising=False)
        assert Settings(_env_file=None).storage_is_s3 is False

        monkeypatch.setenv("S3_SECRET_ACCESS_KEY", "secret")
        assert Settings(_env_file=None).storage_is_s3 is True

    def test_is_production_accepts_both_spellings(self, monkeypatch):
        for value, expected in (("production", True), ("prod", True), ("staging", False)):
            monkeypatch.setenv("ENVIRONMENT", value)
            assert Settings(_env_file=None).is_production is expected

    def test_empty_admin_key_is_falsy(self, monkeypatch):
        # docker-compose passes ADMIN_API_KEY= when the operator leaves it unset.
        monkeypatch.setenv("ADMIN_API_KEY", "")
        assert not Settings(_env_file=None).admin_api_key
