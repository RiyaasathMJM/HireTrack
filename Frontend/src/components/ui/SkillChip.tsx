// ── components/ui/SkillChip.tsx ───────────────────────────────────────────────

interface SkillChipProps {
  skill: string;
  variant?: 'matched' | 'missing' | 'default';
  onRemove?: () => void;
}

export default function SkillChip({ skill, variant = 'default', onRemove }: SkillChipProps) {
  return (
    <span className={`skill-chip skill-chip--${variant}`}>
      {skill}
      {onRemove && (
        <button
          type="button"
          className="skill-chip-remove"
          onClick={onRemove}
          aria-label={`Remove ${skill}`}
        >
          ×
        </button>
      )}
    </span>
  );
}
