// ── api/jobs.ts ───────────────────────────────────────────────────────────────

import apiClient from './client';
import type { JobDescription, MatchResult } from '../types';

export const jobsApi = {
  list: () =>
    apiClient.get<JobDescription[]>('/api/jobs'),

  getById: (id: number) =>
    apiClient.get<JobDescription>(`/api/jobs/${id}`),

  create: (title: string, description: string) =>
    apiClient.post<JobDescription>('/api/jobs', { title, description }),

  update: (id: number, data: { title?: string; description?: string }) =>
    apiClient.patch<JobDescription>(`/api/jobs/${id}`, data),

  delete: (id: number) =>
    apiClient.delete<{ deleted: number }>(`/api/jobs/${id}`),

  matchAll: (id: number) =>
    apiClient.post<MatchResult[]>(`/api/jobs/${id}/match-all`),
};

export default jobsApi;
