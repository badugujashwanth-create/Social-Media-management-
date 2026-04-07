'use client';

import { useEffect, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { apiFetch } from '@/lib/api';

type DashboardAccount = {
  id: number;
  platform: string;
  display_name: string | null;
  token_health: string;
};

type DashboardData = {
  accounts: DashboardAccount[];
  recent_posts: unknown[];
};

const EMPTY_DASHBOARD: DashboardData = { accounts: [], recent_posts: [] };

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData>(EMPTY_DASHBOARD);

  useEffect(() => {
    apiFetch<DashboardData>('/dashboard', { auth: true }).then(setData).catch(() => setData(EMPTY_DASHBOARD));
  }, []);

  return (
    <ProtectedPage>
      <h1 className='mb-4 text-2xl font-semibold'>Unified Dashboard</h1>
      <div className='mb-6 grid grid-cols-1 gap-4 md:grid-cols-3'>
        <Card>
          <p className='text-sm text-gray-500'>Connected Accounts</p>
          <p className='text-3xl font-bold'>{data.accounts.length}</p>
        </Card>
        <Card>
          <p className='text-sm text-gray-500'>Recent Posts</p>
          <p className='text-3xl font-bold'>{data.recent_posts.length}</p>
        </Card>
        <Card>
          <p className='text-sm text-gray-500'>Token Health</p>
          <p className='text-3xl font-bold'>{data.accounts.filter((a) => a.token_health === 'ok').length}</p>
        </Card>
      </div>

      <Card>
        <h2 className='mb-3 text-lg font-semibold'>Connected Accounts</h2>
        <div className='space-y-2'>
          {data.accounts.map((a) => (
            <div key={a.id} className='flex items-center justify-between rounded border border-border p-2'>
              <div>
                <p className='font-medium'>{a.display_name || `Account #${a.id}`}</p>
                <p className='text-sm text-gray-600'>{a.platform}</p>
              </div>
              <Badge>{a.token_health}</Badge>
            </div>
          ))}
        </div>
      </Card>
    </ProtectedPage>
  );
}
