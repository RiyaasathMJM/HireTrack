// ── types/index.ts ─────────────────────────────────────────────────────────────

export type PipelineStage = 'applied' | 'screening' | 'interview' | 'offer' | 'rejected';

export interface Candidate {
  id: number;
  name: string;
  email: string;
  phone: string;
  skills: string[];
  stage: PipelineStage;
  star_rating: number;
  notes: string;
  resume_text: string;
  file_name: string;
  match_score: number;
  jd_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface JobDescription {
  id: number;
  title: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface MatchResult {
  id: number;
  name: string;
  match_score: number;
  matched: string[];
  missing: string[];
}

export interface SkillGapResult {
  score: number;
  matched: string[];
  missing: string[];
}

export interface SummarizeResult {
  summary: string;
  strengths?: string[];
  concerns?: string[];
}

export interface HealthStatus {
  status: string;
  database: string;
  db_host: string;
  db_name: string;
  ai_available: boolean;
  pypdf: boolean;
  docx: boolean;
}
