import type { FailureCluster, TraceSummary } from '@/types';

const PASS_THRESHOLD = 0.7;

export function isTracePassing(overallScore: number): boolean {
  return overallScore >= PASS_THRESHOLD;
}

export function formatDimensionName(dimension: string): string {
  return dimension.replace(/_/g, ' ');
}

export function worstDimension(
  scores: TraceSummary['scores'] | undefined,
): { dimension: string; score: number } | null {
  if (!scores?.length) return null;
  return scores.reduce((min, score) => (score.score < min.score ? score : min));
}

export function formatClusterLabel(
  clusterId: string | null | undefined,
  clusters?: FailureCluster[],
): string {
  if (!clusterId) return '—';
  const match = clusters?.find((cluster) => cluster.cluster_id === clusterId);
  if (match?.label) return match.label;

  const parts = clusterId.split('|').filter(Boolean);
  if (parts.length === 1) {
    return `${formatDimensionName(parts[0])} failures`;
  }
  return `Failures in: ${parts.map(formatDimensionName).join(', ')}`;
}

export function formatWorstDimensionHint(scores: TraceSummary['scores'] | undefined): string | null {
  const worst = worstDimension(scores);
  if (!worst) return null;
  return `worst: ${formatDimensionName(worst.dimension)} ${(worst.score * 100).toFixed(0)}%`;
}
