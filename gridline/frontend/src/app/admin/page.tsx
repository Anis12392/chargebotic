'use client';

import { useCallback, useEffect, useState } from 'react';

import { BarChart } from '@/components/BarChart';
import { InspectionCard } from '@/components/InspectionCard';
import { ApiError, getAdminStats, trainingDataUrl } from '@/lib/api';
import { titleCase, voltageClassColor } from '@/lib/format';
import type { AdminStats } from '@/lib/types';

const STORAGE_KEY = 'gridline-admin-key';

export default function AdminPage() {
  const [adminKey, setAdminKey] = useState('');
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // sessionStorage, not localStorage: the key should not outlive the tab on
    // a device that may be shared between crews.
    const stored = sessionStorage.getItem(STORAGE_KEY);
    if (stored) setAdminKey(stored);
  }, []);

  const load = useCallback(
    async (key: string) => {
      setLoading(true);
      setError(null);
      try {
        const result = await getAdminStats(key || undefined);
        setStats(result);
        if (key) sessionStorage.setItem(STORAGE_KEY, key);
      } catch (err) {
        if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
          setError('That admin key was rejected.');
          sessionStorage.removeItem(STORAGE_KEY);
        } else if (err instanceof ApiError && err.status === 503) {
          setError('The admin API is disabled: no ADMIN_API_KEY is configured on the server.');
        } else {
          setError(err instanceof ApiError ? err.userMessage : 'Could not load statistics.');
        }
        setStats(null);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    void load(adminKey);
    // Intentionally runs once on mount with whatever key was restored.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="px-4 pt-4">
      <h1 className="text-xl font-bold text-slate-50">Admin dashboard</h1>

      <form
        onSubmit={(event) => {
          event.preventDefault();
          void load(adminKey);
        }}
        className="mt-3 flex gap-2"
      >
        <input
          type="password"
          value={adminKey}
          onChange={(event) => setAdminKey(event.target.value)}
          placeholder="Admin key"
          aria-label="Admin key"
          className="field flex-1"
        />
        <button type="submit" className="btn-secondary px-4">
          Load
        </button>
      </form>

      {error && (
        <p role="alert" className="mt-3 text-sm text-signal-danger">
          {error}
        </p>
      )}
      {loading && <p className="mt-3 text-sm text-slate-500">Loading…</p>}

      {stats && (
        <div className="mt-4 space-y-4">
          <section className="card">
            <h2 className="label mb-3">Fleet</h2>
            <dl className="grid grid-cols-2 gap-4">
              <Metric label="Inspections" value={stats.total_inspections} />
              <Metric label="Verifications" value={stats.total_verifications} />
              <Metric
                label="Verified"
                value={`${Math.round(stats.verified_fraction * 100)}%`}
              />
              <Metric
                label="Success rate"
                value={
                  stats.prediction_success_rate === null
                    ? 'no data'
                    : `${Math.round(stats.prediction_success_rate * 100)}%`
                }
                hint={
                  stats.total_verifications < 20
                    ? `Only ${stats.total_verifications} verifications — not yet meaningful`
                    : undefined
                }
              />
              <Metric
                label="Mean confidence"
                value={`${Math.round(stats.mean_confidence * 100)}%`}
              />
              <Metric
                label="Mean perch score"
                value={stats.mean_perch_score === null ? '—' : stats.mean_perch_score.toFixed(0)}
              />
            </dl>
          </section>

          <Panel title="Voltage class distribution">
            <BarChart
              data={stats.voltage_class_distribution}
              colorFor={(key) => voltageClassColor(key)}
            />
          </Panel>

          <Panel title="Confidence histogram">
            <BarChart data={stats.confidence_histogram} />
          </Panel>

          <Panel title="Utilities">
            <BarChart data={stats.utility_distribution} />
          </Panel>

          <Panel title="Pole materials">
            <BarChart data={stats.pole_material_distribution} />
          </Panel>

          <Panel title="Structure types">
            <BarChart data={stats.structure_type_distribution} />
          </Panel>

          <Panel title="Most common hardware">
            <BarChart data={stats.hardware_frequency} />
          </Panel>

          <Panel title="Perch score distribution">
            <BarChart data={stats.perch_score_distribution} />
          </Panel>

          <Panel title="Inspections per day">
            <BarChart data={stats.inspections_per_day} emptyMessage="No captures in this window." />
          </Panel>

          <ConfusionMatrix confusion={stats.confusion} />

          {stats.top_perch_sites.length > 0 && (
            <Panel title="Top perch sites">
              <ul className="space-y-3">
                {stats.top_perch_sites.map((inspection) => (
                  <li key={inspection.id}>
                    <InspectionCard inspection={inspection} />
                  </li>
                ))}
              </ul>
            </Panel>
          )}

          <Panel title="Training data">
            <p className="mb-3 text-xs leading-relaxed text-slate-400">
              Verified inspections exported as newline-delimited JSON. Each row pairs the stored
              photograph and features with the engineer&apos;s ground truth and a frozen snapshot of
              what the model predicted at the time.
            </p>
            <div className="flex gap-2">
              <a href={trainingDataUrl(false)} className="btn-secondary flex-1 text-xs">
                All verified
              </a>
              <a href={trainingDataUrl(true)} className="btn-secondary flex-1 text-xs">
                Corrections only
              </a>
            </div>
          </Panel>
        </div>
      )}
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="card">
      <h2 className="label mb-3">{title}</h2>
      {children}
    </section>
  );
}

function Metric({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <div>
      <dt className="label">{label}</dt>
      <dd className="mt-0.5 font-mono text-2xl font-bold text-slate-100">{value}</dd>
      {hint && <p className="mt-0.5 text-[10px] leading-tight text-slate-600">{hint}</p>}
    </div>
  );
}

function ConfusionMatrix({ confusion }: { confusion: Record<string, Record<string, number>> }) {
  const predictedClasses = Object.keys(confusion);
  if (!predictedClasses.length) {
    return (
      <Panel title="Predicted vs verified">
        <p className="text-sm text-slate-500">
          No verified inspections yet. The matrix fills in as engineers record ground truth.
        </p>
      </Panel>
    );
  }

  const actualClasses = Array.from(
    new Set(predictedClasses.flatMap((predicted) => Object.keys(confusion[predicted] ?? {}))),
  ).sort();

  return (
    <Panel title="Predicted vs verified">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[22rem] border-collapse text-xs">
          <caption className="sr-only">
            Rows are predicted voltage classes, columns are verified classes.
          </caption>
          <thead>
            <tr>
              <th scope="col" className="p-1.5 text-left text-slate-500">
                pred \ actual
              </th>
              {actualClasses.map((actual) => (
                <th key={actual} scope="col" className="p-1.5 text-slate-400">
                  {titleCase(actual).slice(0, 8)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {predictedClasses.map((predicted) => (
              <tr key={predicted} className="border-t border-surface-800">
                <th scope="row" className="p-1.5 text-left font-medium text-slate-300">
                  {titleCase(predicted).slice(0, 12)}
                </th>
                {actualClasses.map((actual) => {
                  const count = confusion[predicted]?.[actual] ?? 0;
                  const onDiagonal = predicted === actual;
                  return (
                    <td
                      key={actual}
                      className={`p-1.5 text-center font-mono ${
                        count === 0
                          ? 'text-slate-700'
                          : onDiagonal
                            ? 'text-signal-ok'
                            : 'text-signal-danger'
                      }`}
                    >
                      {count}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-[11px] leading-relaxed text-slate-600">
        Green on the diagonal is a correct class call. Off-diagonal counts show which classes the
        engine confuses — that is where the rule weights need work.
      </p>
    </Panel>
  );
}
