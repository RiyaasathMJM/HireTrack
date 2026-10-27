// ── pages/Jobs.tsx ────────────────────────────────────────────────────────────

import { useEffect, useState } from 'react';
import {
  Plus,
  Briefcase,
  Pencil,
  Trash2,
  Zap,
  Loader2,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import toast from 'react-hot-toast';
import TopBar from '../components/layout/TopBar';
import Modal from '../components/ui/Modal';
import MatchScoreBar from '../components/ui/MatchScoreBar';
import EmptyState from '../components/ui/EmptyState';
import Spinner from '../components/ui/Spinner';
import jobsApi from '../api/jobs';
import type { JobDescription, MatchResult } from '../types';

export default function Jobs() {
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [loading, setLoading] = useState(true);

  // Create/Edit modal
  const [formModal, setFormModal] = useState(false);
  const [editingJob, setEditingJob] = useState<JobDescription | null>(null);
  const [formTitle, setFormTitle] = useState('');
  const [formDesc, setFormDesc] = useState('');
  const [formSaving, setFormSaving] = useState(false);

  // Match-all modal
  const [matchModal, setMatchModal] = useState(false);
  const [matchingJob, setMatchingJob] = useState<JobDescription | null>(null);
  const [matchLoading, setMatchLoading] = useState(false);
  const [matchResults, setMatchResults] = useState<MatchResult[]>([]);

  const load = () => {
    setLoading(true);
    jobsApi.list()
      .then(r => setJobs(r.data))
      .catch(() => toast.error('Failed to load jobs'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const openCreate = () => {
    setEditingJob(null);
    setFormTitle('');
    setFormDesc('');
    setFormModal(true);
  };

  const openEdit = (job: JobDescription) => {
    setEditingJob(job);
    setFormTitle(job.title);
    setFormDesc(job.description);
    setFormModal(true);
  };

  const handleFormSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formTitle.trim() || !formDesc.trim()) return;
    setFormSaving(true);
    try {
      if (editingJob) {
        const res = await jobsApi.update(editingJob.id, { title: formTitle, description: formDesc });
        setJobs(prev => prev.map(j => j.id === editingJob.id ? res.data : j));
        toast.success('Job updated');
      } else {
        const res = await jobsApi.create(formTitle, formDesc);
        setJobs(prev => [res.data, ...prev]);
        toast.success('Job created');
      }
      setFormModal(false);
    } catch {
      toast.error('Failed to save');
    } finally {
      setFormSaving(false);
    }
  };

  const handleDelete = async (job: JobDescription) => {
    if (!confirm(`Delete "${job.title}"?`)) return;
    await toast.promise(jobsApi.delete(job.id), {
      loading: 'Deleting…',
      success: 'Deleted',
      error:   'Failed to delete',
    });
    setJobs(prev => prev.filter(j => j.id !== job.id));
  };

  const openMatchAll = (job: JobDescription) => {
    setMatchingJob(job);
    setMatchResults([]);
    setMatchModal(true);
  };

  const runMatchAll = async () => {
    if (!matchingJob) return;
    setMatchLoading(true);
    try {
      const res = await jobsApi.matchAll(matchingJob.id);
      setMatchResults(res.data);
      toast.success(`Scored ${res.data.length} candidates`);
    } catch {
      toast.error('Match-all failed');
    } finally {
      setMatchLoading(false);
    }
  };

  return (
    <div className="page">
      <TopBar title="Job Descriptions" subtitle="Manage and match your job postings" />
      <div className="page-content">

        <div className="page-actions">
          <button className="btn btn-primary" onClick={openCreate}>
            <Plus size={16} /> New Job
          </button>
        </div>

        {loading ? (
          <Spinner label="Loading jobs…" />
        ) : jobs.length === 0 ? (
          <EmptyState
            icon={Briefcase}
            title="No job descriptions yet"
            description="Create your first job description to start matching candidates."
            action={
              <button className="btn btn-primary" onClick={openCreate}>
                <Plus size={15} /> Create Job
              </button>
            }
          />
        ) : (
          <div className="jobs-grid">
            {jobs.map(job => (
              <div key={job.id} className="card job-card">
                <div className="job-card-header">
                  <div className="job-card-icon">
                    <Briefcase size={18} />
                  </div>
                  <div className="job-card-meta">
                    <h3 className="job-title">{job.title}</h3>
                    <p className="text-sm text-muted">
                      Created {new Date(job.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <p className="job-description">{job.description.slice(0, 200)}{job.description.length > 200 ? '…' : ''}</p>

                <div className="job-card-actions">
                  <button className="btn btn-primary btn-sm" onClick={() => openMatchAll(job)}>
                    <Zap size={13} /> Match All
                  </button>
                  <button className="btn btn-ghost btn-sm" onClick={() => openEdit(job)}>
                    <Pencil size={13} /> Edit
                  </button>
                  <button className="btn btn-danger btn-sm" onClick={() => handleDelete(job)}>
                    <Trash2 size={13} /> Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      <Modal
        open={formModal}
        onClose={() => setFormModal(false)}
        title={editingJob ? 'Edit Job Description' : 'New Job Description'}
        width="640px"
      >
        <form className="modal-content-stack" onSubmit={handleFormSave}>
          <div className="field-group">
            <label className="field-label" htmlFor="job-title">Title</label>
            <input
              id="job-title"
              type="text"
              className="field-input"
              placeholder="e.g. Senior Python Developer"
              value={formTitle}
              onChange={e => setFormTitle(e.target.value)}
              required
            />
          </div>
          <div className="field-group">
            <label className="field-label" htmlFor="job-desc">Description</label>
            <textarea
              id="job-desc"
              className="notes-textarea"
              rows={8}
              placeholder="Paste the full job description…"
              value={formDesc}
              onChange={e => setFormDesc(e.target.value)}
              required
            />
          </div>
          <div className="modal-footer-actions">
            <button type="button" className="btn btn-ghost" onClick={() => setFormModal(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={formSaving}>
              {formSaving ? <Loader2 size={15} className="spin" /> : null}
              {editingJob ? 'Save Changes' : 'Create Job'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Match-All Modal */}
      <Modal
        open={matchModal}
        onClose={() => setMatchModal(false)}
        title={`Match All Candidates — ${matchingJob?.title ?? ''}`}
        width="720px"
      >
        <div className="modal-content-stack">
          {matchResults.length === 0 ? (
            <div className="match-all-start">
              <p className="text-muted">
                This will score all candidates against <strong>{matchingJob?.title}</strong> and update their match scores.
              </p>
              <button
                className="btn btn-primary"
                onClick={runMatchAll}
                disabled={matchLoading}
              >
                {matchLoading
                  ? <><Loader2 size={15} className="spin" /> Matching…</>
                  : <><Zap size={15} /> Start Matching</>
                }
              </button>
              {matchLoading && <Spinner label="Scoring candidates…" size={32} />}
            </div>
          ) : (
            <div className="match-all-results">
              <p className="text-muted text-sm">{matchResults.length} candidates scored</p>
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Candidate</th>
                      <th>Match Score</th>
                      <th>Matched Skills</th>
                      <th>Missing Skills</th>
                    </tr>
                  </thead>
                  <tbody>
                    {matchResults.map(r => (
                      <tr key={r.id}>
                        <td className="font-medium">{r.name}</td>
                        <td><MatchScoreBar score={r.match_score} showLabel /></td>
                        <td>
                          <div className="skills-cell">
                            {r.matched.slice(0, 3).map(s => (
                              <span key={s} className="skill-chip skill-chip--matched">{s}</span>
                            ))}
                            {r.matched.length > 3 && (
                              <CheckCircle2 size={13} className="icon-green" />
                            )}
                          </div>
                        </td>
                        <td>
                          <div className="skills-cell">
                            {r.missing.slice(0, 3).map(s => (
                              <span key={s} className="skill-chip skill-chip--missing">{s}</span>
                            ))}
                            {r.missing.length > 3 && (
                              <XCircle size={13} className="icon-red" />
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
}
