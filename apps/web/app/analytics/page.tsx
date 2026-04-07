'use client';

import { useEffect, useState } from 'react';
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { ProtectedPage } from '@/components/protected-page';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { apiFetch } from '@/lib/api';

type DailyPosts = { day: string; count: number };
type Availability = { oauth_account_id: number; platform: string; available: boolean };
type FollowerDeltaPoint = { snapshot_at: string; delta: number };
type FollowerDeltaSeries = {
  oauth_account_id: number;
  platform: string;
  display_name: string | null;
  points: FollowerDeltaPoint[];
};

export default function AnalyticsPage() {
  const [hasMounted, setHasMounted] = useState(false);
  const [daily, setDaily] = useState<DailyPosts[]>([]);
  const [deltas, setDeltas] = useState<FollowerDeltaSeries[]>([]);
  const [availability, setAvailability] = useState<Availability[]>([]);
  const [submitting, setSubmitting] = useState(false);

  const load = () => {
    apiFetch<DailyPosts[]>('/analytics/daily-posts', { auth: true }).then(setDaily).catch(() => setDaily([]));
    apiFetch<FollowerDeltaSeries[]>('/analytics/follower-deltas', { auth: true }).then(setDeltas).catch(() => setDeltas([]));
    apiFetch<Availability[]>('/analytics/unfollowers-availability', { auth: true }).then(setAvailability).catch(() => setAvailability([]));
  };

  useEffect(() => {
    setHasMounted(true);
    load();
  }, []);

  const triggerSnapshot = async () => {
    setSubmitting(true);
    try {
      await apiFetch('/analytics/snapshot', { method: 'POST', auth: true });
      load();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ProtectedPage>
      <h1 className='mb-4 text-2xl font-semibold'>Analytics</h1>

      <div className='mb-4'>
        <Button disabled={submitting} onClick={triggerSnapshot}>
          {submitting ? 'Running snapshot...' : 'Trigger follower snapshot (dev)'}
        </Button>
      </div>

      <div className='grid grid-cols-1 gap-4 md:grid-cols-2'>
        <Card>
          <h2 className='mb-2 text-lg font-semibold'>Daily Posts</h2>
          <div className='h-64'>
            {hasMounted && (
              <ResponsiveContainer width='100%' height='100%'>
                <BarChart data={daily}>
                  <CartesianGrid strokeDasharray='3 3' />
                  <XAxis dataKey='day' />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey='count' fill='#0ea5e9' />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>

        <Card>
          <h2 className='mb-2 text-lg font-semibold'>Follower Delta Series</h2>
          {deltas.length === 0 && (
            <div className='space-y-2 text-sm text-gray-600'>
              <p>No follower delta data yet.</p>
              <Button disabled={submitting} onClick={triggerSnapshot}>Trigger snapshot now</Button>
            </div>
          )}
          {deltas.length > 0 && (
            <div className='space-y-4'>
              {deltas.map((series) => (
                <div key={series.oauth_account_id}>
                  <p className='mb-1 text-sm font-medium'>
                    {series.platform} - {series.display_name || `Account #${series.oauth_account_id}`}
                  </p>
                  <div className='h-40'>
                    {hasMounted && (
                      <ResponsiveContainer width='100%' height='100%'>
                        <LineChart data={series.points}>
                          <CartesianGrid strokeDasharray='3 3' />
                          <XAxis dataKey='snapshot_at' />
                          <YAxis />
                          <Tooltip />
                          <Line type='monotone' dataKey='delta' stroke='#0284c7' strokeWidth={2} />
                        </LineChart>
                      </ResponsiveContainer>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <Card className='mt-4'>
        <h2 className='mb-2 text-lg font-semibold'>Who Unfollowed Availability</h2>
        <div className='space-y-2 text-sm'>
          {availability.map((a) => (
            <p key={a.oauth_account_id}>
              {a.platform}: {a.available ? 'Available' : 'Not available on this platform/API'}
            </p>
          ))}
        </div>
      </Card>
    </ProtectedPage>
  );
}
