#!/usr/bin/env python3
"""
Deploy a static website to wirebird.space on Hostinger.
Usage: python3 execution/deploy_wirebird.py [--dir PATH] [--wait]
"""

import os
import sys
import time
import zipfile
import argparse
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("HOSTINGER_API_TOKEN")
API_BASE = "https://developers.hostinger.com"
DOMAIN = "wirebird.space"
USERNAME = "u114958547"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}
CHUNK_SIZE = 10 * 1024 * 1024  # 10MB


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def wait_for_provisioning(max_minutes=15):
    log(f"Waiting for {DOMAIN} to finish provisioning...")
    for i in range(max_minutes * 4):  # check every 15s
        r = requests.get(
            f"{API_BASE}/api/hosting/v1/websites?domain={DOMAIN}",
            headers=HEADERS,
            timeout=30,
        )
        data = r.json().get("data", [])
        if data:
            log(f"✓ {DOMAIN} is provisioned!")
            return True
        if i % 4 == 0:
            log(f"  Not ready yet... ({i * 15 // 60}m {(i * 15) % 60}s elapsed)")
        time.sleep(15)
    return False


def get_upload_credentials():
    r = requests.post(
        f"{API_BASE}/api/hosting/v1/files/upload-urls",
        headers=HEADERS,
        json={"username": USERNAME, "domain": DOMAIN},
        timeout=30,
    )
    if r.status_code != 200:
        raise Exception(f"Failed to get upload credentials: {r.status_code} {r.text}")
    return r.json()


def create_archive(source_dir, output_path):
    source = Path(source_dir).resolve()
    log(f"Creating archive from {source} → {output_path}")
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        count = 0
        for file_path in source.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(source)
                zf.write(file_path, arcname)
                count += 1
    size_mb = Path(output_path).stat().st_size / (1024 * 1024)
    log(f"✓ Archive created: {count} files, {size_mb:.1f} MB")
    return output_path


def tus_upload(file_path, upload_url, auth_key, rest_auth_key):
    file_path = Path(file_path)
    file_size = file_path.stat().st_size
    filename = file_path.name
    clean_url = upload_url.rstrip("/")
    target_url = f"{clean_url}/{filename}?override=true"

    upload_headers = {
        "X-Auth": auth_key,
        "X-Auth-Rest": rest_auth_key,
        "upload-length": str(file_size),
        "upload-offset": "0",
    }

    log(f"Initiating TUS upload: {filename} ({file_size / 1024 / 1024:.1f} MB)")

    # Step 1: Initialize upload (POST)
    r = requests.post(target_url, data="", headers=upload_headers, timeout=60)
    if r.status_code != 201:
        raise Exception(f"TUS init failed: {r.status_code} {r.text}")
    log("✓ TUS upload initialized")

    # Step 2: Upload in chunks (PATCH)
    offset = 0
    with open(file_path, "rb") as f:
        while offset < file_size:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            patch_headers = {
                "X-Auth": auth_key,
                "X-Auth-Rest": rest_auth_key,
                "Content-Type": "application/offset+octet-stream",
                "upload-offset": str(offset),
                "Content-Length": str(len(chunk)),
            }
            r = requests.patch(target_url, data=chunk, headers=patch_headers, timeout=120)
            if r.status_code not in (200, 204):
                raise Exception(f"TUS chunk upload failed at offset {offset}: {r.status_code} {r.text}")
            offset += len(chunk)
            pct = offset / file_size * 100
            log(f"  Uploaded {offset / 1024 / 1024:.1f} MB / {file_size / 1024 / 1024:.1f} MB ({pct:.0f}%)")

    log(f"✓ Upload complete: {filename}")
    return filename


def trigger_deploy(filename):
    log(f"Triggering deployment for {DOMAIN}...")
    r = requests.post(
        f"{API_BASE}/api/hosting/v1/accounts/{USERNAME}/websites/{DOMAIN}/deploy",
        headers=HEADERS,
        json={"archive_path": filename},
        timeout=60,
    )
    if r.status_code != 200:
        raise Exception(f"Deploy trigger failed: {r.status_code} {r.text}")
    log(f"✓ Deployment triggered!")
    return r.json()


def main():
    parser = argparse.ArgumentParser(description="Deploy wirebird.space to Hostinger")
    parser.add_argument("--dir", default="website", help="Local directory to deploy (default: website/)")
    parser.add_argument("--wait", action="store_true", help="Wait for provisioning if not ready")
    args = parser.parse_args()

    if not API_TOKEN:
        print("ERROR: HOSTINGER_API_TOKEN not set in .env")
        sys.exit(1)

    source_dir = Path(args.dir)
    if not source_dir.exists():
        print(f"ERROR: Directory '{source_dir}' not found")
        sys.exit(1)

    # Check provisioning
    r = requests.get(
        f"{API_BASE}/api/hosting/v1/websites?domain={DOMAIN}",
        headers=HEADERS, timeout=30
    )
    provisioned = bool(r.json().get("data"))

    if not provisioned:
        if args.wait:
            provisioned = wait_for_provisioning()
        else:
            log(f"⚠️  {DOMAIN} is not provisioned yet in the hosting plan.")
            log("   Run with --wait to automatically wait, or add wirebird.space in hPanel first.")
            log(f"   hPanel → Hosting → Manage → Addon Domains → Add {DOMAIN}")
            sys.exit(1)

    if not provisioned:
        log("✗ Provisioning timed out. Add wirebird.space in hPanel manually.")
        sys.exit(1)

    # Create archive
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = f"/tmp/wirebird_{timestamp}.zip"
    create_archive(source_dir, archive_path)

    # Get upload credentials
    log("Getting upload credentials...")
    creds = get_upload_credentials()
    log("✓ Got upload credentials")

    # Upload
    filename = tus_upload(
        archive_path,
        creds["url"],
        creds["auth_key"],
        creds["rest_auth_key"],
    )

    # Deploy
    result = trigger_deploy(filename)
    log(f"✓ Done! wirebird.space should be live in ~1-2 minutes.")
    log(f"   Check: https://wirebird.space")
    return result


if __name__ == "__main__":
    main()
