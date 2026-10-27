// ── components/ui/MatchScoreBar.tsx ───────────────────────────────────────────

interface MatchScoreBarProps {
  score: number;
  showLabel?: boolean;
}

function getScoreColor(score: number): string {
  if (score >= 75) return 'score-high';
  if (score >= 50) return 'score-mid';
  return 'score-low';
}

export default function MatchScoreBar({ score, showLabel = true }: MatchScoreBarProps) {
  const pct = Math.min(100, Math.max(0, Math.round(score)));
  const colorClass = getScoreColor(pct);

  return (
    <div className="score-bar-wrapper">
      {showLabel && (
        <span className={`score-label ${colorClass}`}>{pct}%</span>
      )}
      <div className="score-track">
        <div
          className={`score-fill ${colorClass}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
