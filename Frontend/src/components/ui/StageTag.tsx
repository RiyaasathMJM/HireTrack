// ── components/ui/StageTag.tsx ────────────────────────────────────────────────

import type { PipelineStage } from '../../types';

const stageConfig: Record<PipelineStage, { label: string; color: string }> = {
  applied:   { label: 'Applied',   color: 'stage-applied' },
  screening: { label: 'Screening', color: 'stage-screening' },
  interview: { label: 'Interview', color: 'stage-interview' },
  offer:     { label: 'Offer',     color: 'stage-offer' },
  rejected:  { label: 'Rejected',  color: 'stage-rejected' },
};

interface StageTagProps {
  stage: PipelineStage;
}

export default function StageTag({ stage }: StageTagProps) {
  const config = stageConfig[stage] ?? { label: stage, color: 'stage-applied' };
  return (
    <span className={`stage-tag ${config.color}`}>{config.label}</span>
  );
}
