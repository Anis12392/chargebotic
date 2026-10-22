'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';

import { ReportView } from '@/components/ReportView';
import { ApiError, getInspection } from '@/lib/api';
import { formatTimestamp, titleCase } from '@/lib/format';
import type { InspectionDetail } from '@/lib/types';

export default function InspectionPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id;

  const [detail, setDetail] = useState<InspectionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setLoading(true);
    getInspection(id)
      .then((result) => {
        if (!cancelled) setDetail(result);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof ApiError
              ? err.status === 404
                ? 'That inspection does not exist.'
                : err.userMessage
              : 'Could not load the inspection.',
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) {
    return <p className="px-4 pt-8 text-sm text-slate-500">Loading inspection…</p>;
  }

  if (error || !detail) {
    return (
      <div className="px-4 pt-8">
        <p role="alert" className="text-sm text-signal-danger">
          {error ?? 'Inspection unavailable.'}
        </p>
        <Link href="/history" className="btn-secondary mt-4 w-full">
          Back to inspections
        </Link>
      </div>
    );
  }

  return (
    <div className="px-4 pt-4">
      <Link href="/history" className="btn-ghost mb-2 px-0 text-xs">
        ← All inspections
      </Link>

      <ReportView report={detail.report} showVerify={!detail.is_verified} />

      {detail.verifications.length > 0 && (
        <section className="card mb-6" aria-labelledby="verifications-heading">
          <h2 id="verifications-heading" className="label mb-2">
            Recorded ground truth
          </h2>
          <ul className="space-y-3">
            {detail.verifications.map((verification) => (
              <li key={verification.id} className="card-tight">
                <div className="flex items-baseline justify-between gap-2">
                  <span className="text-sm font-semibold text-slate-200">
                    {verification.verified_by}
                  </span>
                  <span className="font-mono text-[11px] text-slate-500">
                    {formatTimestamp(verification.created_at)}
                  </span>
                </div>

                <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
                  {verification.actual_voltage_v !== null && (
                    <Row label="Actual voltage">{verification.actual_voltage_v} V</Row>
                  )}
                  {verification.actual_utility && (
                    <Row label="Actual utility">{verification.actual_utility}</Row>
                  )}
                  {verification.actual_conductor && (
                    <Row label="Conductor">{verification.actual_conductor}</Row>
                  )}
                  {verification.measured_current_a !== null && (
                    <Row label="Measured current">{verification.measured_current_a} A</Row>
                  )}
                  {verification.measured_field_ut !== null && (
                    <Row label="Measured field">{verification.measured_field_ut} µT</Row>
                  )}
                  {verification.harvested_power_w !== null && (
                    <Row label="Harvested">{verification.harvested_power_w} W</Row>
                  )}
                  {verification.perch_outcome && (
                    <Row label="Perch outcome">{titleCase(verification.perch_outcome)}</Row>
                  )}
                  {verification.prediction_was_correct !== null && (
                    <Row label="Prediction">
                      <span
                        className={
                          verification.prediction_was_correct
                            ? 'text-signal-ok'
                            : 'text-signal-danger'
                        }
                      >
                        {verification.prediction_was_correct ? 'Correct' : 'Incorrect'}
                      </span>
                    </Row>
                  )}
                </dl>

                {verification.drone_notes && (
                  <Note label="Drone notes">{verification.drone_notes}</Note>
                )}
                {verification.pilot_notes && (
                  <Note label="Pilot notes">{verification.pilot_notes}</Note>
                )}
                {verification.comments && <Note label="Comments">{verification.comments}</Note>}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="label">{label}</dt>
      <dd className="mt-0.5 text-slate-200">{children}</dd>
    </div>
  );
}

function Note({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="mt-2">
      <p className="label">{label}</p>
      <p className="mt-0.5 text-xs leading-relaxed text-slate-400">{children}</p>
    </div>
  );
}
