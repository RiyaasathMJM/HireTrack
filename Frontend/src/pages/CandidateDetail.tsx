// ── pages/CandidateDetail.tsx ─────────────────────────────────────────────────

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Mail,
  Phone,
  FileText,
  Zap,
  BarChart3,
  Save,
  Loader2,
  Trash2,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import toast from 'react-hot-toast';
import TopBar from '../components/layout/TopBar';
import StageTag from '../components/ui/StageTag';
import StarRating from '../components/ui/StarRating';
import MatchScoreBar from '../components/ui/MatchScoreBar';
import SkillChip from '../components/ui/SkillChip';
import Modal from '../components/ui/Modal';
import Spinner from '../components/ui/Spinner';
import candidatesApi from '../api/candidates';
import jobsApi from '../api/jobs';
import type { Candidate, JobDescription, PipelineStage, SkillGapResult, SummarizeResult } from '../types';

const STAGES: PipelineStage[] = ['applied', 'screening', 'interview', 'offer', 'rejected'];

export default function CandidateDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [loading, setLoading] = useState(true);

  // Editing state
  const [editNotes, setEditNotes] = useState('');
  const [editStage, setEditStage] = useState<PipelineStage>('applied');
  const [editStarRating, setEditStarRating] = useState(0);
  const [savingEdit, setSavingEdit] = useState(false);

  // Match modal
  const [matchModal, setMatchModal] = useState(false);
  const [matchJd, setMatchJd] = useState('');
  const [matchLoading, setMatchLoading] = useState(false);
  const [matchResult, setMatchResult] = useState<SkillGapResult | null>(null);

  // Summarize modal
  const [summaryModal, setSummaryModal] = useState(false);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryResult, setSummaryResult] = useState<SummarizeResult | null>(null);

  useEffect(() => {
    const cid = Number(id);
    if (!cid) return;
    Promise.all([
      candidatesApi.getById(cid),
      jobsApi.list(),
    ]).then(([cRes, jRes]) => {
      setCandidate(cRes.data);
      setEditNotes(cRes.data.notes ?? '');
      setEditStage(cRes.data.stage);
      setEditStarRating(cRes.data.star_rating);
      setJobs(jRes.data);
    }).catch(() => toast.error('Failed to load candidate'))
      .finally(() => setLoading(false));
  }, [id]);

  const saveEdit = async () => {
    if (!candidate) return;
    setSavingEdit(true);
    try {
      const res = await candidatesApi.update(candidate.id, {
        notes: editNotes,
        stage: editStage,
        star_rating: editStarRating,
      });
      setCandidate(res.data);
      toast.success('Saved!');
    } catch {
      toast.error('Failed to save');
    } finally {
      setSavingEdit(false);
    }
  };

  const handleDelete = async () => {
    if (!candidate) return;
    if (!confirm(`Delete ${candidate.name}? This cannot be undone.`)) return;
    await toast.promise(candidatesApi.delete(candidate.id), {
      loading: 'Deleting…',
      success: 'Candidate deleted',
      error:   'Delete failed',
    });
    navigate('/candidates');
  };

  const runMatch = async () => {
    if (!candidate) return;
    setMatchLoading(true);
    try {
      const res = await candidatesApi.match(candidate.id, matchJd);
      setMatchResult(res.data);
      setCandidate(prev => prev ? { ...prev, match_score: res.data.score } : prev);
    } catch {
      toast.error('Match failed');
    } finally {
      setMatchLoading(false);
    }
  };

  const runSummarize = async () => {
    if (!candidate) return;
    setSummaryLoading(true);
    try {
      const res = await candidatesApi.summarize(candidate.id);
      setSummaryResult(res.data);
    } catch {
      toast.error('Summarize failed');
    } finally {
      setSummaryLoading(false);
    }
  };

  const openSummaryModal = () => {
    setSummaryModal(true);
    setSummaryResult(null);
    runSummarize();
  };

  if (loading) {
    return (
      <div className="page">
        <TopBar title="Candidate" />
        <div className="page-content">
          <Spinner size={40} label="Loading candidate…" />
        </div>
      </div>
    );
  }

  if (!candidate) {
    return (
      <div className="page">
        <TopBar title="Candidate" />
        <div className="page-content">
          <p className="text-muted">Candidate not found.</p>
        </div>
      </div>
    );
  }

  const selectedJob = jobs.find(j => j.id === candidate.jd_id);

  return (
    <div className="page">
      <TopBar title={candidate.name || 'Candidate'} subtitle={candidate.email || ''} />
      <div className="page-content">

        <button className="back-btn" onClick={() => navigate(-1)}>
          <ArrowLeft size={15} /> Back
        </button>

        <div className="detail-grid">
          {/* Left: Profile card */}
          <div className="detail-left">
            <div className="card profile-card">
              <div className="profile-avatar">
                {(candidate.name || '?').charAt(0).toUpperCase()}
              </div>
              <h2 className="profile-name">{candidate.name || '—'}</h2>
              {candidate.email && (
                <a href={`mailto:${candidate.email}`} className="profile-contact">
                  <Mail size={14} /> {candidate.email}
                </a>
              )}
              {candidate.phone && (
                <a href={`tel:${candidate.phone}`} className="profile-contact">
                  <Phone size={14} /> {candidate.phone}
                </a>
              )}

              <div className="profile-divider" />

              <div className="profile-field">
                <label className="profile-label">Stage</label>
                <select
                  className="filter-select w-full"
                  value={editStage}
                  onChange={e => setEditStage(e.target.value as PipelineStage)}
                >
                  {STAGES.map(s => (
                    <option key={s} value={s}>
                      {s.charAt(0).toUpperCase() + s.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="profile-field">
                <label className="profile-label">Star Rating</label>
                <StarRating value={editStarRating} onChange={setEditStarRating} size={20} />
              </div>

              <div className="profile-field">
                <label className="profile-label">Match Score</label>
                <MatchScoreBar score={candidate.match_score} showLabel />
              </div>

              <div className="profile-field">
                <label className="profile-label">Linked Job</label>
                <p className="text-sm text-muted">
                  {selectedJob ? selectedJob.title : 'None'}
                </p>
              </div>

              <div className="profile-divider" />

              <div className="profile-actions">
                <button
                  className="btn btn-primary w-full"
                  onClick={saveEdit}
                  disabled={savingEdit}
                >
                  {savingEdit ? <Loader2 size={15} className="spin" /> : <Save size={15} />}
                  Save Changes
                </button>
                <button
                  className="btn btn-ghost w-full"
                  onClick={() => { setMatchModal(true); setMatchResult(null); }}
                >
                  <BarChart3 size={15} /> Run Match
                </button>
                <button
                  className="btn btn-ghost w-full"
                  onClick={openSummaryModal}
                >
                  <Zap size={15} /> AI Summary
                </button>
                <button
                  className="btn btn-danger w-full"
                  onClick={handleDelete}
                >
                  <Trash2 size={15} /> Delete
                </button>
              </div>
            </div>
          </div>

          {/* Right: Details */}
          <div className="detail-right">
            {/* Skills */}
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Skills</h2>
              </div>
              <div className="skills-cloud">
                {(candidate.skills ?? []).length > 0 ? (
                  candidate.skills.map(s => (
                    <SkillChip key={s} skill={s} />
                  ))
                ) : (
                  <p className="text-muted text-sm">No skills detected.</p>
                )}
              </div>
            </div>

            {/* Notes */}
            <div className="card">
              <div className="card-header">
                <FileText size={16} className="card-header-icon" />
                <h2 className="card-title">Notes</h2>
              </div>
              <textarea
                className="notes-textarea"
                placeholder="Add notes about this candidate…"
                value={editNotes}
                onChange={e => setEditNotes(e.target.value)}
                rows={5}
              />
            </div>

            {/* Resume Text */}
            {candidate.resume_text && (
              <div className="card">
                <div className="card-header">
                  <FileText size={16} className="card-header-icon" />
                  <h2 className="card-title">Resume Text</h2>
                  <span className="card-badge">{candidate.file_name}</span>
                </div>
                <pre className="resume-text">{candidate.resume_text}</pre>
              </div>
            )}
          </div>
        </div>

        {/* Match Modal */}
        <Modal open={matchModal} onClose={() => setMatchModal(false)} title="Match Against Job Description">
          <div className="modal-content-stack">
            <div className="field-group">
              <label className="field-label">Select a saved JD</label>
              <select
                className="filter-select w-full"
                onChange={e => {
                  const jd = jobs.find(j => j.id === Number(e.target.value));
                  if (jd) setMatchJd(jd.description);
                }}
                defaultValue=""
              >
                <option value="">— Choose a job description —</option>
                {jobs.map(j => (
                  <option key={j.id} value={j.id}>{j.title}</option>
                ))}
              </select>
            </div>
            <div className="field-group">
              <label className="field-label">Or paste a job description</label>
              <textarea
                className="notes-textarea"
                rows={6}
                placeholder="Paste the job description here…"
                value={matchJd}
                onChange={e => setMatchJd(e.target.value)}
              />
            </div>
            <button
              className="btn btn-primary"
              onClick={runMatch}
              disabled={matchLoading || !matchJd.trim()}
            >
              {matchLoading ? <Loader2 size={15} className="spin" /> : <BarChart3 size={15} />}
              Run Match
            </button>

            {matchResult && (
              <div className="match-result">
                <div className="match-score-big">
                  <span>Match Score</span>
                  <strong className="score-number">{Math.round(matchResult.score)}%</strong>
                </div>
                <div className="match-sections">
                  <div>
                    <p className="match-section-label">
                      <CheckCircle2 size={14} className="icon-green" /> Matched
                    </p>
                    <div className="skills-cloud">
                      {matchResult.matched.map(s => (
                        <SkillChip key={s} skill={s} variant="matched" />
                      ))}
                      {matchResult.matched.length === 0 && <p className="text-muted text-sm">None</p>}
                    </div>
                  </div>
                  <div>
                    <p className="match-section-label">
                      <XCircle size={14} className="icon-red" /> Missing
                    </p>
                    <div className="skills-cloud">
                      {matchResult.missing.map(s => (
                        <SkillChip key={s} skill={s} variant="missing" />
                      ))}
                      {matchResult.missing.length === 0 && <p className="text-muted text-sm">None</p>}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </Modal>

        {/* Summary Modal */}
        <Modal open={summaryModal} onClose={() => setSummaryModal(false)} title="AI Resume Summary" width="640px">
          {summaryLoading ? (
            <Spinner label="Generating summary…" size={36} />
          ) : summaryResult ? (
            <div className="summary-result">
              <p className="summary-text">{summaryResult.summary}</p>
              {summaryResult.strengths && summaryResult.strengths.length > 0 && (
                <div className="summary-section">
                  <p className="summary-section-label">
                    <CheckCircle2 size={14} className="icon-green" /> Strengths
                  </p>
                  <ul className="summary-list">
                    {summaryResult.strengths.map((s, i) => <li key={i}>{s}</li>)}
                  </ul>
                </div>
              )}
              {summaryResult.concerns && summaryResult.concerns.length > 0 && (
                <div className="summary-section">
                  <p className="summary-section-label">
                    <XCircle size={14} className="icon-red" /> Concerns
                  </p>
                  <ul className="summary-list">
                    {summaryResult.concerns.map((s, i) => <li key={i}>{s}</li>)}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <p className="text-muted">No summary available.</p>
          )}
        </Modal>

      </div>
    </div>
  );
}
