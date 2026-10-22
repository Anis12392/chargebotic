'use client';

import Link from 'next/link';
import { useState } from 'react';

import { ConfidenceBar } from '@/components/ConfidenceBar';
import { EvidenceList } from '@/components/EvidenceList';
import { PerchCard } from '@/components/PerchCard';
import { VerifyForm } from '@/components/VerifyForm';
import { WarningList } from '@/components/WarningList';
import {
  compassPoint,
  formatCoords,
  formatCurrentRange,
  formatDistance,
  formatMeasurement,
  formatTimestamp,
  formatVolts,
  formatVoltageList,
  titleCase,
  voltageClassColor,
} from '@/lib/format';
import type { EngineeringReport } from '@/lib/types';

export function ReportView({
  report,
  localPhotoUrl,
  showVerify = true,
}: {
  report: EngineeringReport;
  localPhotoUrl?: string | null;
  showVerify?: boolean;
}) {
  const [verified, setVerified] = useState(false);
  const classColor = voltageClassColor(report.voltage.voltage_class);
  const photo = localPhotoUrl ?? report.photo_url;
  const detected = report.vision.detections.filter((d) => d.present);

  return (
    <article className="space-y-4 pb-6">
      {/* --- Headline ---------------------------------------------------- */}
      <header className="card">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="label">Voltage class</p>
            <h1
              className="mt-0.5 truncate text-xl font-bold"
              style={{ color: classColor }}
              title={report.voltage.class_label}
            >
              {report.voltage.class_label}
            </h1>
          </div>
          <span
            className={`shrink-0 rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide ${
              report.voltage.is_confirmed
                ? 'bg-signal-ok/15 text-signal-ok'
                : 'bg-surface-700 text-slate-400'
            }`}
          >
            {report.voltage.is_confirmed ? 'GIS confirmed' : 'Estimated'}
          </span>
        </div>

        <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3">
          <Field label="Most likely nominal">
            {formatVolts(report.voltage.most_likely_nominal_v)}
          </Field>
          <Field label="Utility">{report.utility.name ?? 'Not attributed'}</Field>
          <Field label="Possible nominals" span>
            {formatVoltageList(report.voltage.possible_nominal_v)}
          </Field>
          <Field label="Conductor">
            {report.conductor.most_likely_codeword
              ? `${report.conductor.most_likely_codeword} · ${report.conductor.most_likely_size ?? ''}`
              : 'Not identified'}
          </Field>
          <Field label="Thermal rating">
            {report.conductor.thermal_rating_a ? `${report.conductor.thermal_rating_a} A` : '—'}
          </Field>
        </dl>

        <ConfidenceBar value={report.overall_confidence} label="Overall confidence" />
        {report.voltage.confirmation_source && (
          <p className="mt-2 text-[11px] leading-relaxed text-slate-500">
            Confirmed by {report.voltage.confirmation_source}
          </p>
        )}
      </header>

      {/* --- Current, with the caveat attached ---------------------------- */}
      <section className="card" aria-labelledby="current-heading">
        <h2 id="current-heading" className="label">
          Operating current
        </h2>
        <p className="mt-1 font-mono text-2xl font-bold text-slate-100">
          {formatCurrentRange(report.current.low_a, report.current.high_a)}
        </p>
        <p className="mt-1 text-xs text-slate-500">{report.current.basis}</p>
        <p
          className={`mt-2 rounded-lg border p-2.5 text-xs leading-relaxed ${
            report.current.is_measured
              ? 'border-signal-ok/40 bg-signal-ok/5 text-signal-ok'
              : 'border-signal-warn/40 bg-signal-warn/5 text-signal-warn'
          }`}
        >
          {report.current.is_measured
            ? `Measured value from ${report.current.measurement_source ?? 'a verified field reading'}.`
            : report.current.caveat}
        </p>
      </section>

      {/* --- Photo ------------------------------------------------------- */}
      {photo && (
        /* The source is a blob URL or a presigned S3 URL. Neither can go
           through the Next image optimiser, which needs a stable, fetchable
           path at build or request time. */
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={photo}
          alt="Captured structure"
          className="w-full rounded-xl border border-surface-700 object-cover"
        />
      )}

      {/* --- Warnings ---------------------------------------------------- */}
      <WarningList warnings={report.warnings} />

      {/* --- Reasoning --------------------------------------------------- */}
      <section className="card" aria-labelledby="reasoning-heading">
        <h2 id="reasoning-heading" className="label mb-2">
          Reasoning
        </h2>
        <ol className="space-y-2">
          {report.reasoning.map((line, index) => (
            <li
              key={`${index}-${line.slice(0, 20)}`}
              className={`text-sm leading-relaxed ${
                index === 0 ? 'font-medium text-slate-100' : 'text-slate-400'
              }`}
            >
              {index > 0 && <span className="mr-1.5 text-slate-600">·</span>}
              {line}
            </li>
          ))}
        </ol>
      </section>

      {/* --- Evidence ---------------------------------------------------- */}
      <section className="card" aria-labelledby="evidence-heading">
        <h2 id="evidence-heading" className="label mb-2">
          Evidence
        </h2>
        <EvidenceList evidence={report.evidence} />
      </section>

      {/* --- Perch ------------------------------------------------------- */}
      {report.perch && <PerchCard perch={report.perch} />}

      {/* --- Vision inventory -------------------------------------------- */}
      <section className="card" aria-labelledby="vision-heading">
        <h2 id="vision-heading" className="label mb-2">
          Detected hardware
        </h2>
        {report.vision.model_name === 'vision_disabled' ? (
          <p className="text-sm text-slate-500">
            Image analysis was unavailable for this capture. Everything above rests on GIS data.
          </p>
        ) : (
          <>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-3">
              <Field label="Structure">{titleCase(report.vision.structure_type)}</Field>
              <Field label="Material">{titleCase(report.vision.pole_material)}</Field>
              <Field label="Phases">{report.vision.phase_count ?? '—'}</Field>
              <Field label="Conductors">{report.vision.conductor_count ?? '—'}</Field>
              <Field label="Crossarm">{titleCase(report.vision.crossarm_config)}</Field>
              <Field label="Insulator">{titleCase(report.vision.insulator_type)}</Field>
              <Field label="Discs in string">{report.vision.insulator_disc_count ?? '—'}</Field>
              <Field label="Covering">{titleCase(report.vision.conductor_covering)}</Field>
              <Field label="Insulator length">
                {formatMeasurement(report.vision.insulator_length)}
              </Field>
              <Field label="Phase spacing">
                {formatMeasurement(report.vision.conductor_spacing)}
              </Field>
              <Field label="Conductor dia.">
                {formatMeasurement(report.vision.conductor_diameter)}
              </Field>
              <Field label="Image quality">
                {Math.round(report.vision.image_quality * 100)}%
              </Field>
            </dl>

            {detected.length > 0 && (
              <ul className="mt-4 flex flex-wrap gap-1.5" aria-label="Detected objects">
                {detected.map((item) => (
                  <li key={item.label} className="chip">
                    {titleCase(item.label)}
                    <span className="font-mono text-[10px] text-slate-500">
                      {Math.round(item.confidence * 100)}%
                    </span>
                  </li>
                ))}
              </ul>
            )}

            {report.vision.raw_notes && (
              <p className="mt-3 text-xs italic leading-relaxed text-slate-500">
                {report.vision.raw_notes}
              </p>
            )}
          </>
        )}
      </section>

      {/* --- Nearby assets ----------------------------------------------- */}
      <section className="card" aria-labelledby="assets-heading">
        <div className="mb-2 flex items-baseline justify-between">
          <h2 id="assets-heading" className="label">
            Nearby mapped assets
          </h2>
          <Link
            href={`/map?lat=${report.capture.latitude}&lon=${report.capture.longitude}`}
            className="text-xs font-medium text-grid-distribution"
          >
            Open map →
          </Link>
        </div>
        {report.nearby_assets.length === 0 ? (
          <p className="text-sm text-slate-500">
            Nothing mapped within the search radius. OpenStreetMap distribution coverage is sparse
            outside cities.
          </p>
        ) : (
          <ul className="space-y-1.5">
            {report.nearby_assets.slice(0, 8).map((asset) => (
              <li
                key={`${asset.source}-${asset.element_type}-${asset.element_id}`}
                className="flex items-baseline justify-between gap-2 border-b border-surface-800 pb-1.5 last:border-0"
              >
                <span className="min-w-0 truncate text-sm text-slate-300">
                  {titleCase(asset.asset_kind)}
                  {asset.name ? ` · ${asset.name}` : ''}
                  {asset.operator ? ` · ${asset.operator}` : ''}
                </span>
                <span className="shrink-0 font-mono text-xs text-slate-500">
                  {asset.voltage_v.length > 0 && `${formatVoltageList(asset.voltage_v)} · `}
                  {formatDistance(asset.distance_m)} {compassPoint(asset.bearing_deg)}
                </span>
              </li>
            ))}
          </ul>
        )}
        {report.gis_sources.length > 0 && (
          <p className="mt-2 text-[11px] text-slate-600">
            Sources queried: {report.gis_sources.join(', ')}
          </p>
        )}
      </section>

      {/* --- Capture metadata -------------------------------------------- */}
      <section className="card" aria-labelledby="capture-heading">
        <h2 id="capture-heading" className="label mb-2">
          Capture
        </h2>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-3">
          <Field label="Coordinates" span>
            {formatCoords(report.capture.latitude, report.capture.longitude)}
          </Field>
          <Field label="GPS accuracy">
            {report.capture.accuracy_m ? `±${report.capture.accuracy_m.toFixed(0)} m` : '—'}
          </Field>
          <Field label="Heading">
            {report.capture.heading_deg !== null && report.capture.heading_deg !== undefined
              ? `${report.capture.heading_deg.toFixed(0)}° ${compassPoint(report.capture.heading_deg)}`
              : '—'}
          </Field>
          <Field label="Altitude">
            {report.capture.altitude_m !== null && report.capture.altitude_m !== undefined
              ? `${report.capture.altitude_m.toFixed(0)} m`
              : '—'}
          </Field>
          <Field label="Captured">{formatTimestamp(report.capture.captured_at)}</Field>
          <Field label="Processing">{report.processing_ms} ms</Field>
          <Field label="Inspection ID" span>
            <span className="font-mono text-xs">{report.inspection_id}</span>
          </Field>
        </dl>
        {report.capture.notes && (
          <p className="mt-3 text-sm italic text-slate-400">“{report.capture.notes}”</p>
        )}
      </section>

      {/* --- Verification ------------------------------------------------ */}
      {showVerify && (
        <section className="card" aria-labelledby="verify-heading">
          <h2 id="verify-heading" className="label mb-1">
            Engineer verification
          </h2>
          <p className="mb-3 text-xs leading-relaxed text-slate-500">
            Correcting a prediction is how the system improves. Every verification is stored with a
            frozen copy of what the model said, and becomes training data.
          </p>
          {verified ? (
            <p className="rounded-lg border border-signal-ok/40 bg-signal-ok/5 p-3 text-sm text-signal-ok">
              Verification recorded. Thank you — this correction feeds the next model.
            </p>
          ) : (
            <VerifyForm
              inspectionId={report.inspection_id}
              detections={report.vision.detections}
              onVerified={() => setVerified(true)}
            />
          )}
        </section>
      )}

      <p className="px-1 text-[11px] leading-relaxed text-slate-600">{report.disclaimer}</p>
    </article>
  );
}

function Field({
  label,
  children,
  span = false,
}: {
  label: string;
  children: React.ReactNode;
  span?: boolean;
}) {
  return (
    <div className={span ? 'col-span-2' : ''}>
      <dt className="label">{label}</dt>
      <dd className="value mt-0.5 break-words">{children}</dd>
    </div>
  );
}
