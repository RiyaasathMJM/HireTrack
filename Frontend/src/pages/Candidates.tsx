// ── pages/Candidates.tsx ──────────────────────────────────────────────────────

import { useEffect, useState, useCallback } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { Search, SlidersHorizontal, Trash2, Eye, ArrowUpDown } from 'lucide-react';
import toast from 'react-hot-toast';
import TopBar from '../components/layout/TopBar';
import StageTag from '../components/ui/StageTag';
import StarRating from '../components/ui/StarRating';
import MatchScoreBar from '../components/ui/MatchScoreBar';
import Spinner from '../components/ui/Spinner';
import EmptyState from '../components/ui/EmptyState';
import candidatesApi from '../api/candidates';
import type { Candidate, PipelineStage } from '../types';

const STAGES: PipelineStage[] = ['applied', 'screening', 'interview', 'offer', 'rejected'];
const SORT_OPTIONS = [
  { value: 'created_at', label: 'Date Added' },
  { value: 'match_score', label: 'Match Score' },
  { value: 'star_rating', label: 'Star Rating' },
  { value: 'name',        label: 'Name' },
];

export default function Candidates() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);

  const keyword  = searchParams.get('keyword')  ?? '';
  const stage    = searchParams.get('stage')    ?? '';
  const sort     = searchParams.get('sort')     ?? 'created_at';
  const order    = (searchParams.get('order')   ?? 'desc') as 'asc' | 'desc';

  const [searchInput, setSearchInput] = useState(keyword);

  const fetchCandidates = useCallback(() => {
    setLoading(true);
    candidatesApi.list({ keyword, stage, sort, order })
      .then(res => setCandidates(res.data))
      .catch(() => toast.error('Failed to load candidates'))
      .finally(() => setLoading(false));
  }, [keyword, stage, sort, order]);

  useEffect(() => { fetchCandidates(); }, [fetchCandidates]);

  const setParam = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    setSearchParams(next);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setParam('keyword', searchInput);
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Delete ${name || 'this candidate'}?`)) return;
    await toast.promise(candidatesApi.delete(id), {
      loading: 'Deleting…',
      success: 'Candidate deleted',
      error:   'Failed to delete',
    });
    setCandidates(prev => prev.filter(c => c.id !== id));
  };

  const handleRating = async (id: number, star_rating: number) => {
    try {
      const res = await candidatesApi.update(id, { star_rating });
      setCandidates(prev => prev.map(c => c.id === id ? res.data : c));
    } catch {
      toast.error('Failed to update rating');
    }
  };

  const toggleOrder = () => setParam('order', order === 'desc' ? 'asc' : 'desc');

  return (
    <div className="page">
      <TopBar title="Candidates" subtitle={`${candidates.length} candidates found`} />
      <div className="page-content">

        {/* Filter bar */}
        <div className="filter-bar">
          <form className="filter-search" onSubmit={handleSearch}>
            <Search size={15} className="filter-search-icon" />
            <input
              type="text"
              className="filter-search-input"
              placeholder="Search by name, skill, email…"
              value={searchInput}
              onChange={e => setSearchInput(e.target.value)}
            />
            <button type="submit" className="btn btn-sm btn-primary">Search</button>
          </form>

          <div className="filter-controls">
            <SlidersHorizontal size={15} />
            <select
              className="filter-select"
              value={stage}
              onChange={e => setParam('stage', e.target.value)}
            >
              <option value="">All Stages</option>
              {STAGES.map(s => (
                <option key={s} value={s}>
                  {s.charAt(0).toUpperCase() + s.slice(1)}
                </option>
              ))}
            </select>

            <select
              className="filter-select"
              value={sort}
              onChange={e => setParam('sort', e.target.value)}
            >
              {SORT_OPTIONS.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>

            <button className="icon-btn" onClick={toggleOrder} title="Toggle order">
              <ArrowUpDown size={15} />
              <span className="sr-only">{order}</span>
            </button>
          </div>
        </div>

        {/* Table */}
        {loading ? (
          <Spinner label="Loading candidates…" />
        ) : candidates.length === 0 ? (
          <EmptyState
            icon={Search}
            title="No candidates found"
            description="Try adjusting your filters or upload some resumes."
            action={
              <Link to="/upload" className="btn btn-primary">Upload Resumes</Link>
            }
          />
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th>Stage</th>
                  <th>Skills</th>
                  <th>Match Score</th>
                  <th>Rating</th>
                  <th>Added</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {candidates.map(c => (
                  <tr key={c.id} className="table-row">
                    <td>
                      <div className="candidate-cell">
                        <div className="candidate-avatar">
                          {(c.name || '?').charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="candidate-name">{c.name || '—'}</p>
                          <p className="candidate-email">{c.email || '—'}</p>
                        </div>
                      </div>
                    </td>
                    <td><StageTag stage={c.stage} /></td>
                    <td>
                      <div className="skills-cell">
                        {(c.skills ?? []).slice(0, 3).map(s => (
                          <span key={s} className="skill-chip skill-chip--default">{s}</span>
                        ))}
                        {(c.skills ?? []).length > 3 && (
                          <span className="skill-more">+{c.skills.length - 3}</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <MatchScoreBar score={c.match_score} />
                    </td>
                    <td>
                      <StarRating
                        value={c.star_rating}
                        onChange={val => handleRating(c.id, val)}
                        size={14}
                      />
                    </td>
                    <td className="text-muted text-sm">
                      {new Date(c.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <div className="row-actions">
                        <Link
                          to={`/candidates/${c.id}`}
                          className="icon-btn"
                          title="View"
                        >
                          <Eye size={15} />
                        </Link>
                        <button
                          className="icon-btn icon-btn--danger"
                          title="Delete"
                          onClick={() => handleDelete(c.id, c.name)}
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
