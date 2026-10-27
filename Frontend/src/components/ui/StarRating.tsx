// ── components/ui/StarRating.tsx ──────────────────────────────────────────────

import { Star } from 'lucide-react';
import { useState } from 'react';

interface StarRatingProps {
  value: number;
  onChange?: (val: number) => void;
  readonly?: boolean;
  size?: number;
}

export default function StarRating({
  value,
  onChange,
  readonly = false,
  size = 16,
}: StarRatingProps) {
  const [hovered, setHovered] = useState(0);

  return (
    <div className={`star-rating ${readonly ? 'star-rating--readonly' : ''}`}>
      {[1, 2, 3, 4, 5].map(n => (
        <button
          key={n}
          type="button"
          className={`star-btn ${n <= (hovered || value) ? 'star-btn--filled' : ''}`}
          onClick={() => !readonly && onChange?.(n)}
          onMouseEnter={() => !readonly && setHovered(n)}
          onMouseLeave={() => !readonly && setHovered(0)}
          aria-label={`${n} star${n > 1 ? 's' : ''}`}
          disabled={readonly}
        >
          <Star size={size} />
        </button>
      ))}
    </div>
  );
}
