'use client';

import { useState } from 'react';

import { ApiError, submitVerification } from '@/lib/api';
import { titleCase } from '@/lib/format';
import type { Detection, VerifyRequest } from '@/lib/types';

const PERCH_OUTCOMES = ['not_attempted', 'success', 'partial', 'failure'] as const;

/**
 * Ground-truth entry.
 *
 * Deliberately permissive: an engineer who only knows the voltage should not
 * have to fill in eight other fields to record it. Everything except the name
 * is optional, and blank means "no information", not zero.
 */
export function VerifyForm({
  inspectionId,
  detections,
  onVerified,
}: {
  inspectionId: string;
  detections: Detection[];
  onVerified: () => void;
}) {
  const [form, setForm] = useState({
    verified_by: '',
    actual_voltage_v: '',
    actual_utility: '',
    actual_conductor: '',
    measured_current_a: '',
    measured_field_ut: '',
    harvested_power_w: '',
    perch_outcome: 'not_attempted' as (typeof PERCH_OUTCOMES)[number],
    drone_notes: '',
    pilot_notes: '',
    comments: '',
  });
  const [hardware, setHardware] = useState<Record<string, boolean>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);

  const update = (key: keyof typeof form) => (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm((current) => ({ ...current, [key]: event.target.value }));

  const toggleHardware = (label: string, present: boolean) =>
    setHardware((current) => ({ ...current, [label]: present }));

  const numeric = (value: string): number | null => {
    if (!value.trim()) return null;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  };

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!form.verified_by.trim()) {
      setError('Your name or ID is required — corrections have to be attributable.');
      return;
    }

    setSubmitting(true);
    setError(null);

    const body: VerifyRequest = {
      inspection_id: inspectionId,
      verified_by: form.verified_by.trim(),
      actual_voltage_v: numeric(form.actual_voltage_v),
      actual_utility: form.actual_utility.trim() || null,
      actual_conductor: form.actual_conductor.trim() || null,
      measured_current_a: numeric(form.measured_current_a),
      measured_field_ut: numeric(form.measured_field_ut),
      harvested_power_w: numeric(form.harvested_power_w),
      perch_outcome: form.perch_outcome,
      drone_notes: form.drone_notes.trim() || null,
      pilot_notes: form.pilot_notes.trim() || null,
      comments: form.comments.trim() || null,
      corrected_hardware: Object.keys(hardware).length ? hardware : null,
    };

    try {
      await submitVerification(body);
      onVerified();
    } catch (err) {
      setError(err instanceof ApiError ? err.userMessage : 'Could not record the verification.');
    } finally {
      setSubmitting(false);
    }
  };

  const correctable = showAll ? detections : detections.filter((d) => d.present);

  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <Input
        id="verified-by"
        label="Your name or engineer ID"
        required
        value={form.verified_by}
        onChange={update('verified_by')}
        placeholder="Required"
      />

      <div className="grid grid-cols-2 gap-3">
        <Input
          id="actual-voltage"
          label="Actual voltage (V)"
          type="number"
          value={form.actual_voltage_v}
          onChange={update('actual_voltage_v')}
          placeholder="e.g. 12470"
          hint="Line-to-line, in volts"
        />
        <Input
          id="actual-utility"
          label="Actual utility"
          value={form.actual_utility}
          onChange={update('actual_utility')}
        />
        <Input
          id="actual-conductor"
          label="Conductor"
          value={form.actual_conductor}
          onChange={update('actual_conductor')}
          placeholder="e.g. 4/0 ACSR"
        />
        <Input
          id="measured-current"
          label="Measured current (A)"
          type="number"
          value={form.measured_current_a}
          onChange={update('measured_current_a')}
          hint="Only if actually metered"
        />
        <Input
          id="measured-field"
          label="Measured field (µT)"
          type="number"
          value={form.measured_field_ut}
          onChange={update('measured_field_ut')}
        />
        <Input
          id="harvested-power"
          label="Harvested power (W)"
          type="number"
          value={form.harvested_power_w}
          onChange={update('harvested_power_w')}
        />
      </div>

      <div>
        <label className="label" htmlFor="perch-outcome">
          Perch outcome
        </label>
        <select
          id="perch-outcome"
          value={form.perch_outcome}
          onChange={update('perch_outcome')}
          className="field mt-1"
        >
          {PERCH_OUTCOMES.map((outcome) => (
            <option key={outcome} value={outcome}>
              {titleCase(outcome)}
            </option>
          ))}
        </select>
      </div>

      <fieldset>
        <legend className="label mb-1.5">Correct the hardware inventory</legend>
        <ul className="flex flex-wrap gap-1.5">
          {correctable.map((detection) => {
            const override = hardware[detection.label];
            const value = override ?? detection.present;
            return (
              <li key={detection.label}>
                <button
                  type="button"
                  onClick={() => toggleHardware(detection.label, !value)}
                  aria-pressed={value}
                  className={`chip transition-colors ${
                    value
                      ? 'border-signal-ok/50 bg-signal-ok/10 text-signal-ok'
                      : 'text-slate-500 line-through'
                  }`}
                >
                  {titleCase(detection.label)}
                </button>
              </li>
            );
          })}
        </ul>
        <button
          type="button"
          onClick={() => setShowAll((value) => !value)}
          className="btn-ghost mt-1.5 px-0 py-1 text-xs"
        >
          {showAll ? 'Show only detected' : 'Add something the model missed'}
        </button>
      </fieldset>

      <Textarea
        id="drone-notes"
        label="Drone notes"
        value={form.drone_notes}
        onChange={update('drone_notes')}
        placeholder="Approach, perch behaviour, coupler seating"
      />
      <Textarea
        id="pilot-notes"
        label="Pilot notes"
        value={form.pilot_notes}
        onChange={update('pilot_notes')}
        placeholder="Conditions, hazards, anything the next crew needs"
      />
      <Textarea
        id="comments"
        label="Comments"
        value={form.comments}
        onChange={update('comments')}
      />

      {error && (
        <p role="alert" className="text-sm text-signal-danger">
          {error}
        </p>
      )}

      <button type="submit" disabled={submitting} className="btn-primary w-full">
        {submitting ? 'Recording…' : 'Record verification'}
      </button>
    </form>
  );
}

function Input({
  id,
  label,
  hint,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & { id: string; label: string; hint?: string }) {
  return (
    <div>
      <label className="label" htmlFor={id}>
        {label}
      </label>
      <input id={id} className="field mt-1" {...props} />
      {hint && <p className="mt-0.5 text-[10px] text-slate-600">{hint}</p>}
    </div>
  );
}

function Textarea({
  id,
  label,
  ...props
}: React.TextareaHTMLAttributes<HTMLTextAreaElement> & { id: string; label: string }) {
  return (
    <div>
      <label className="label" htmlFor={id}>
        {label}
      </label>
      <textarea id={id} rows={2} className="field mt-1 resize-y" {...props} />
    </div>
  );
}
