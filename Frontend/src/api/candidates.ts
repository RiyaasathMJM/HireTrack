// ── api/candidates.ts ──────────────────────────────────────────────────────────

import apiClient from './client';
import type { Candidate, SkillGapResult, SummarizeResult } from '../types';

export interface ListCandidatesParams {
  stage?: string;
  keyword?: string;
  sort?: string;
  order?: 'asc' | 'desc';
}

export const candidatesApi = {
  list: (params: ListCandidatesParams = {}) =>
    apiClient.get<Candidate[]>('/api/candidates', { params }),

  getById: (id: number) =>
    apiClient.get<Candidate>(`/api/candidates/${id}`),

  upload: (files: File[]) => {
    const formData = new FormData();
    files.forEach(f => formData.append('resumes', f));
    return apiClient.post<Candidate[]>('/api/candidates', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  update: (id: number, data: Partial<Pick<Candidate, 'name' | 'email' | 'phone' | 'stage' | 'star_rating' | 'notes' | 'skills' | 'match_score' | 'jd_id'>>) =>
    apiClient.patch<Candidate>(`/api/candidates/${id}`, data),

  delete: (id: number) =>
    apiClient.delete<{ deleted: number }>(`/api/candidates/${id}`),

  match: (id: number, jobDescription: string) =>
    apiClient.post<SkillGapResult>(`/api/candidates/${id}/match`, { job_description: jobDescription }),

  summarize: (id: number, jobDescription?: string) =>
    apiClient.post<SummarizeResult>(`/api/candidates/${id}/summarize`, { job_description: jobDescription || '' }),
};

export default candidatesApi;
