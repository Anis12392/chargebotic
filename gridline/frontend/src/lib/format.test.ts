import { describe, expect, it } from 'vitest';

import {
  compassPoint,
  confidenceLabel,
  formatCurrentRange,
  formatDistance,
  formatMeasurement,
  formatVoltageList,
  formatVolts,
  titleCase,
  voltageClassColor,
} from './format';

describe('formatVolts', () => {
  it('renders kilovolts above 1 kV', () => {
    expect(formatVolts(12470)).toBe('12.47 kV');
    expect(formatVolts(115000)).toBe('115 kV');
    expect(formatVolts(34500)).toBe('34.5 kV');
  });

  it('renders volts below 1 kV', () => {
    expect(formatVolts(480)).toBe('480 V');
  });

  it('says "unknown" rather than showing a dash that reads as zero', () => {
    expect(formatVolts(null)).toBe('unknown');
    expect(formatVolts(undefined)).toBe('unknown');
  });
});

describe('formatVoltageList', () => {
  it('joins multiple candidates', () => {
    expect(formatVoltageList([12470, 4160])).toBe('12.47 kV / 4.16 kV');
  });

  it('is explicit when there are no candidates', () => {
    expect(formatVoltageList([])).toBe('none identified');
  });
});

describe('formatCurrentRange', () => {
  it('always renders a range, never a single figure', () => {
    expect(formatCurrentRange(35.7, 196.4)).toBe('36–196 A');
  });

  it('refuses to invent a range from a partial estimate', () => {
    expect(formatCurrentRange(null, 196)).toBe('not estimated');
    expect(formatCurrentRange(35, null)).toBe('not estimated');
    expect(formatCurrentRange(null, null)).toBe('not estimated');
  });
});

describe('formatDistance', () => {
  it('uses metres under a kilometre and kilometres above', () => {
    expect(formatDistance(42.4)).toBe('42 m');
    expect(formatDistance(2400)).toBe('2.40 km');
    expect(formatDistance(null)).toBe('—');
  });
});

describe('confidenceLabel', () => {
  it('maps the full range onto words', () => {
    expect(confidenceLabel(0.95)).toBe('high');
    expect(confidenceLabel(0.65)).toBe('moderate');
    expect(confidenceLabel(0.4)).toBe('low');
    expect(confidenceLabel(0.1)).toBe('very low');
    expect(confidenceLabel(0)).toBe('none');
  });
});

describe('voltageClassColor', () => {
  it('gives every class a distinct colour', () => {
    const classes = ['secondary', 'distribution', 'subtransmission', 'transmission', 'ehv'];
    const colors = classes.map(voltageClassColor);
    expect(new Set(colors).size).toBe(classes.length);
  });

  it('falls back to the unknown colour for anything unrecognised', () => {
    expect(voltageClassColor('gibberish')).toBe(voltageClassColor('unknown'));
    expect(voltageClassColor(null)).toBe(voltageClassColor('unknown'));
  });
});

describe('compassPoint', () => {
  it('maps bearings onto sixteen points', () => {
    expect(compassPoint(0)).toBe('N');
    expect(compassPoint(90)).toBe('E');
    expect(compassPoint(180)).toBe('S');
    expect(compassPoint(270)).toBe('W');
    expect(compassPoint(45)).toBe('NE');
  });

  it('wraps past 360 and handles negatives', () => {
    expect(compassPoint(370)).toBe('N');
    expect(compassPoint(-90)).toBe('W');
  });

  it('returns a placeholder with no bearing', () => {
    expect(compassPoint(null)).toBe('—');
  });
});

describe('titleCase', () => {
  it('turns snake_case enum values into readable labels', () => {
    expect(titleCase('transmission_tower')).toBe('Transmission Tower');
    expect(titleCase('suspension_disc')).toBe('Suspension Disc');
  });

  it('handles missing values', () => {
    expect(titleCase(null)).toBe('Unknown');
    expect(titleCase('')).toBe('Unknown');
  });
});

describe('formatMeasurement', () => {
  it('prefers a range over a point value', () => {
    expect(
      formatMeasurement({ value: 180, low: 160, high: 200, unit: 'mm' }),
    ).toBe('160–200 mm');
  });

  it('falls back to a point value when there is no range', () => {
    expect(formatMeasurement({ value: 180, low: null, high: null, unit: 'mm' })).toBe('180 mm');
  });

  it('is explicit when nothing was estimated', () => {
    expect(formatMeasurement({ value: null, low: null, high: null, unit: 'mm' })).toBe(
      'not estimated',
    );
    expect(formatMeasurement(null)).toBe('not estimated');
  });
});
