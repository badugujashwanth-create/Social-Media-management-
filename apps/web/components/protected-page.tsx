'use client';

import { useEffect } from 'react';
import type React from 'react';
import { useRouter } from 'next/navigation';
import { getToken } from '@/lib/api';
import { TopNav } from '@/components/top-nav';

export function ProtectedPage({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  useEffect(() => {
    if (!getToken()) router.replace('/login');
  }, [router]);

  return (
    <div>
      <TopNav />
      <main className='mx-auto max-w-6xl p-4'>{children}</main>
    </div>
  );
}
