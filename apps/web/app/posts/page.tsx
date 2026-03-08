'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { Card } from '@/components/ui/card';
import { apiFetch } from '@/lib/api';
import { OAuthAccount, Post } from '@/lib/types';

const TERMINAL = new Set(['success', 'failed', 'needs_reauth', 'rate_limited']);
const ERROR_MESSAGES: Record<string, string> = {
  needs_reauth: 'Reconnect this account and retry.',
  rate_limited: 'Platform rate limit reached. Retry later.',
  invalid_payload: 'Post content is not valid for this platform.',
  platform_error: 'Platform API returned an error.',
};

function formatError(code: string | null, message: string | null): string {
  if (!code && !message) return '-';
  if (!code) return message || '-';
  const friendly = ERROR_MESSAGES[code] || 'Publishing failed.';
  return message ? `${friendly} (${message})` : friendly;
}

export default function PostsPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [accounts, setAccounts] = useState<OAuthAccount[]>([]);

  const accountNameById = useMemo(
    () => new Map(accounts.map((acc) => [acc.id, acc.display_name || acc.external_account_id])),
    [accounts],
  );

  const load = useCallback(async () => {
    const [postsData, accountData] = await Promise.all([
      apiFetch<Post[]>('/posts', { auth: true }),
      apiFetch<OAuthAccount[]>('/accounts', { auth: true }),
    ]);
    setPosts(postsData);
    setAccounts(accountData);
    return postsData;
  }, []);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined;
    let isActive = true;

    const tick = async () => {
      try {
        const currentPosts = await load();
        const hasPending = currentPosts.some((post) => post.targets.some((target) => !TERMINAL.has(target.status)));
        if (isActive && hasPending) {
          timer = setTimeout(tick, 2000);
        }
      } catch {
        if (isActive) {
          timer = setTimeout(tick, 2000);
        }
      }
    };

    tick();
    return () => {
      isActive = false;
      if (timer) clearTimeout(timer);
    };
  }, [load]);

  return (
    <ProtectedPage>
      <h1 className='mb-4 text-2xl font-semibold'>Post History</h1>
      <div className='space-y-3'>
        {posts.map((post) => (
          <Card key={post.id}>
            <p className='font-medium'>{post.text}</p>
            <p className='text-xs text-gray-600'>{new Date(post.created_at).toLocaleString()}</p>

            <div className='mt-3 overflow-x-auto'>
              <table className='min-w-full text-sm'>
                <thead>
                  <tr className='border-b text-left'>
                    <th className='py-2 pr-3'>Platform</th>
                    <th className='py-2 pr-3'>Account</th>
                    <th className='py-2 pr-3'>Status</th>
                    <th className='py-2 pr-3'>External Post ID</th>
                    <th className='py-2 pr-3'>Attempts</th>
                    <th className='py-2 pr-3'>Error</th>
                  </tr>
                </thead>
                <tbody>
                  {post.targets.map((target) => (
                    <tr key={target.id} className='border-b align-top'>
                      <td className='py-2 pr-3'>{target.platform}</td>
                      <td className='py-2 pr-3'>{accountNameById.get(target.oauth_account_id) || `Account #${target.oauth_account_id}`}</td>
                      <td className='py-2 pr-3'>{target.status}</td>
                      <td className='py-2 pr-3'>{target.external_post_id || '-'}</td>
                      <td className='py-2 pr-3'>{target.attempts}</td>
                      <td className='py-2 pr-3'>{formatError(target.error_code, target.error_message)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        ))}
        {posts.length === 0 && <Card>No posts yet.</Card>}
      </div>
    </ProtectedPage>
  );
}
