export const PLATFORMS = ['facebook', 'linkedin', 'x', 'instagram'] as const;
export type Platform = (typeof PLATFORMS)[number];

export const TARGET_STATUSES = ['queued', 'publishing', 'success', 'failed', 'rate_limited', 'needs_reauth'] as const;
export type TargetStatus = (typeof TARGET_STATUSES)[number];
