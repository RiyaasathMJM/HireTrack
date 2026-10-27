// ── components/ui/Spinner.tsx ─────────────────────────────────────────────────

interface SpinnerProps {
  size?: number;
  label?: string;
}

export default function Spinner({ size = 32, label = 'Loading…' }: SpinnerProps) {
  return (
    <div className="spinner-wrapper" role="status" aria-label={label}>
      <div
        className="spinner"
        style={{ width: size, height: size }}
      />
      <span className="spinner-label">{label}</span>
    </div>
  );
}
