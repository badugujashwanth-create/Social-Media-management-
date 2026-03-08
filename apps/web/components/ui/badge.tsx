import type React from 'react';
import { cn } from '@/lib/utils';

export function Badge({ className, children }: { className?: string; children: React.ReactNode }) {
  return <span className={cn('inline-flex items-center rounded-md border border-border px-2 py-1 text-xs', className)}>{children}</span>;
}
