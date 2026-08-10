/**
 * Mirror of the backend's pydantic contracts.
 *
 * Kept hand-written rather than generated so the shape stays readable, and so
 * fields the UI must never silently drop (confidence, evidence, warnings) are
 * visible in one place.
 */

export type VoltageClass =
  | 'secondary'
  | 'distribution'
  | 'subtransmission'
  | 'transmission'
  | 'ehv'
  | 'unknown';

export type Severity = 'info' | 'caution' | 'danger';

export type PerchGrade = 'excellent' | 'good' | 'marginal' | 'poor' | 'unsuitable';

export interface CaptureContext {
  latitude: number;
  longitude: number;
  accuracy_m?: number | null;
  altitude_m?: number | null;
  altitude_accuracy_m?: number | null;
  heading_deg?: number | null;
  speed_ms?: number | null;
  captured_at?: string | null;
  device_model?: string | null;
  notes?: string | null;
}

export interface Detection {
  label: string;
  present: boolean;
  confidence: number;
  count?: number | null;
  note?: string | null;
}

export interface MeasurementEstimate {
  value: number | null;
  low: number | null;
  high: number | null;
  unit: string;
  confidence: number;
  basis: string | null;
}

export interface VisionAnalysis {
  phase_count: number | null;
  conductor_count: number | null;
  pole_material: string;
  structure_type: string;
  crossarm_config: string;
  crossarm_count: number | null;
  insulator_type: string;
  insulator_disc_count: number | null;
  insulator_length: MeasurementEstimate;
  conductor_spacing: MeasurementEstimate;
  conductor_diameter: MeasurementEstimate;
  conductor_covering: string;
  bundled_subconductors: number | null;
  detections: Detection[];
  image_quality: number;
  obstructed: boolean;
  is_power_infrastructure: boolean;
  overall_confidence: number;
  model_name: string;
  raw_notes: string | null;
}

export interface GISAsset {
  source: string;
  element_type: string;
  element_id: string;
  asset_kind: string;
  name?: string | null;
  operator?: string | null;
  voltage_v: number[];
  circuits?: number | null;
  cables?: number | null;
  ref?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  distance_m?: number | null;
  bearing_deg?: number | null;
  tags: Record<string, unknown>;
  geometry?: { type: string; coordinates: unknown } | null;
}

export interface EvidenceItem {
  source: 'vision' | 'gis' | 'standards' | 'physics' | 'history' | 'user';
  observation: string;
  implication: string;
  weight: number;
  confidence: number;
  reference?: string | null;
}

export interface VoltageEstimate {
  voltage_class: VoltageClass;
  class_label: string;
  class_confidence: number;
  possible_nominal_v: number[];
  most_likely_nominal_v: number | null;
  is_confirmed: boolean;
  confirmation_source: string | null;
  alternatives: Array<{
    voltage_class: string;
    label: string;
    relative_score: number;
    top_reason: string | null;
  }>;
}

export interface ConductorEstimate {
  candidates: Array<{
    codeword: string;
    material: string;
    size: string;
    diameter_mm: number;
    ampacity_75c_a: number;
    ampacity_100c_a: number | null;
  }>;
  most_likely_codeword: string | null;
  most_likely_material: string | null;
  most_likely_size: string | null;
  estimated_diameter_mm: number | null;
  thermal_rating_a: number | null;
  thermal_rating_basis: string | null;
  confidence: number;
}

export interface CurrentEstimate {
  low_a: number | null;
  high_a: number | null;
  basis: string;
  is_measured: boolean;
  measurement_source: string | null;
  confidence: number;
  caveat: string;
}

export interface UtilityEstimate {
  name: string | null;
  confidence: number;
  source: string | null;
  region: string | null;
  known_standard: boolean;
  alternatives: string[];
}

export interface Warning {
  severity: Severity;
  code: string;
  message: string;
}

export interface PerchFactor {
  key: string;
  label: string;
  score: number;
  weight: number;
  confidence: number;
  rationale: string;
}

export interface PerchSuitability {
  score: number;
  grade: PerchGrade;
  confidence: number;
  factors: PerchFactor[];
  estimated_flux_density_ut: number | null;
  estimated_harvest_power_w: number | null;
  harvest_assumptions: string[];
  blockers: string[];
  recommendation: string;
}

export interface EngineeringReport {
  inspection_id: string;
  created_at: string;
  capture: CaptureContext;
  photo_url: string | null;
  thumbnail_url: string | null;
  utility: UtilityEstimate;
  voltage: VoltageEstimate;
  conductor: ConductorEstimate;
  current: CurrentEstimate;
  perch: PerchSuitability | null;
  overall_confidence: number;
  reasoning: string[];
  evidence: EvidenceItem[];
  nearby_assets: GISAsset[];
  warnings: Warning[];
  vision: VisionAnalysis;
  gis_sources: string[];
  processing_ms: number;
  disclaimer: string;
}

export interface InspectionSummary {
  id: string;
  created_at: string;
  latitude: number;
  longitude: number;
  photo_url: string | null;
  thumbnail_url: string | null;
  predicted_voltage_class: string | null;
  predicted_nominal_v: number | null;
  predicted_utility: string | null;
  overall_confidence: number;
  perch_score: number | null;
  is_verified: boolean;
}

export interface InspectionDetail extends InspectionSummary {
  heading_deg: number | null;
  altitude_m: number | null;
  accuracy_m: number | null;
  captured_at: string | null;
  device_model: string | null;
  report: EngineeringReport;
  vision: VisionAnalysis;
  gis: Record<string, unknown>;
  verifications: VerificationRead[];
}

export interface VerificationRead {
  id: string;
  inspection_id: string;
  verified_by: string;
  created_at: string;
  actual_voltage_v: number | null;
  actual_utility: string | null;
  actual_conductor: string | null;
  measured_current_a: number | null;
  measured_field_ut: number | null;
  harvested_power_w: number | null;
  prediction_was_correct: boolean | null;
  perch_outcome: string | null;
  drone_notes: string | null;
  pilot_notes: string | null;
  comments: string | null;
  corrected_hardware: Record<string, boolean> | null;
  field_measurements: Record<string, unknown> | null;
}

export interface VerifyRequest {
  inspection_id: string;
  verified_by: string;
  actual_voltage_v?: number | null;
  actual_utility?: string | null;
  actual_conductor?: string | null;
  measured_current_a?: number | null;
  measured_field_ut?: number | null;
  harvested_power_w?: number | null;
  corrected_hardware?: Record<string, boolean> | null;
  prediction_was_correct?: boolean | null;
  perch_outcome?: 'success' | 'partial' | 'failure' | 'not_attempted' | null;
  drone_notes?: string | null;
  pilot_notes?: string | null;
  field_measurements?: Record<string, unknown> | null;
  comments?: string | null;
}

export interface MapResponse {
  center: { lat: number; lon: number };
  radius_m: number;
  assets: GISAsset[];
  inspections: InspectionSummary[];
  sources: string[];
  errors: string[];
}

export interface AdminStats {
  total_inspections: number;
  total_verifications: number;
  verified_fraction: number;
  prediction_success_rate: number | null;
  mean_confidence: number;
  confidence_histogram: Record<string, number>;
  voltage_class_distribution: Record<string, number>;
  utility_distribution: Record<string, number>;
  pole_material_distribution: Record<string, number>;
  structure_type_distribution: Record<string, number>;
  hardware_frequency: Record<string, number>;
  perch_score_distribution: Record<string, number>;
  mean_perch_score: number | null;
  top_perch_sites: InspectionSummary[];
  inspections_per_day: Record<string, number>;
  confusion: Record<string, Record<string, number>>;
}
