'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { ProtectedPage } from '@/components/protected-page';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { apiFetch, getErrorMessage } from '@/lib/api';
import { OAuthAccount } from '@/lib/types';

const manualSchema = z.object({
  platform: z.enum(['facebook', 'linkedin', 'x', 'instagram']),
  display_name: z.string().min(1),
  external_account_id: z.string().min(1),
  access_token: z.string().min(1),
  refresh_token: z.string().optional(),
  scopes: z.string().optional(),
});

type ManualForm = z.infer<typeof manualSchema>;
type FacebookPage = { id: string; name: string; access_token?: string | null };

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<OAuthAccount[]>([]);
  const [selectingPageAccountId, setSelectingPageAccountId] = useState<number | null>(null);
  const [facebookPages, setFacebookPages] = useState<FacebookPage[]>([]);
  const [selectedPageId, setSelectedPageId] = useState<string>('');
  const [savingPage, setSavingPage] = useState(false);

  const devMode = process.env.NEXT_PUBLIC_DEV_MODE === 'true';
  const { register, handleSubmit, reset, formState } = useForm<ManualForm>({
    resolver: zodResolver(manualSchema),
    defaultValues: { platform: 'facebook' },
  });

  const loadAccounts = useCallback(async () => {
    const data = await apiFetch<OAuthAccount[]>('/accounts', { auth: true });
    setAccounts(data);
  }, []);

  const activeFacebookAccount = useMemo(
    () => accounts.find((a) => a.platform === 'facebook' && (selectingPageAccountId ? a.id === selectingPageAccountId : true)),
    [accounts, selectingPageAccountId],
  );

  useEffect(() => {
    loadAccounts().catch(() => setAccounts([]));
  }, [loadAccounts]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams(window.location.search);
    const connected = params.get('connected');
    if (connected === '1') {
      toast.success('Account connected');
    }
    const oauthError = params.get('oauth_error');
    if (oauthError) {
      const errorPlatform = params.get('platform');
      toast.error(`${errorPlatform ? `${errorPlatform} OAuth failed` : 'OAuth failed'}: ${oauthError}`);
    }
    const needsPageSelect = params.get('needs_page_select');
    const platform = params.get('platform');
    const accountId = Number(params.get('account_id') || 0);
    if (platform === 'facebook' && needsPageSelect === '1' && accountId > 0) {
      setSelectingPageAccountId(accountId);
      apiFetch<FacebookPage[]>(`/oauth/facebook/pages?account_id=${accountId}`, { auth: true })
        .then((pages) => {
          setFacebookPages(pages);
          if (pages[0]) {
            setSelectedPageId(pages[0].id);
          }
        })
        .catch((e: Error) => toast.error(e.message));
    }
    if (typeof window !== 'undefined' && window.location.search) {
      window.history.replaceState({}, '', '/accounts');
    }
  }, []);

  const oauthStart = async (platform: string) => {
    try {
      const res = await apiFetch<{ redirect_url: string }>(`/oauth/${platform}/start`, { auth: true });
      window.location.href = res.redirect_url;
    } catch (e: unknown) {
      toast.error(getErrorMessage(e));
    }
  };

  const onManual = async (data: ManualForm) => {
    try {
      await apiFetch('/accounts/dev', { method: 'POST', auth: true, body: JSON.stringify(data) });
      toast.success('Connected account in developer mode');
      reset();
      await loadAccounts();
    } catch (e: unknown) {
      toast.error(getErrorMessage(e));
    }
  };

  const onSelectFacebookPage = async () => {
    if (!selectingPageAccountId || !selectedPageId) {
      return;
    }
    setSavingPage(true);
    try {
      await apiFetch('/oauth/facebook/pages/select', {
        method: 'POST',
        auth: true,
        body: JSON.stringify({ account_id: selectingPageAccountId, page_id: selectedPageId }),
      });
      toast.success('Facebook Page selected');
      setSelectingPageAccountId(null);
      setFacebookPages([]);
      setSelectedPageId('');
      await loadAccounts();
    } catch (e: unknown) {
      toast.error(getErrorMessage(e));
    } finally {
      setSavingPage(false);
    }
  };

  return (
    <ProtectedPage>
      <h1 className='mb-4 text-2xl font-semibold'>Connected Accounts</h1>

      <Card className='mb-6'>
        <h2 className='mb-2 text-lg font-semibold'>Connect via OAuth</h2>
        <div className='flex flex-wrap gap-2'>
          <Button onClick={() => oauthStart('facebook')}>Connect Facebook</Button>
          <Button onClick={() => oauthStart('linkedin')}>Connect LinkedIn</Button>
          <Button onClick={() => oauthStart('x')}>Connect X</Button>
        </div>
      </Card>

      {devMode && (
        <Card className='mb-6'>
          <h2 className='mb-2 text-lg font-semibold'>Developer Mode: Paste Access Token</h2>
          <form onSubmit={handleSubmit(onManual)} className='grid grid-cols-1 gap-2 md:grid-cols-2'>
            <Input placeholder='platform: facebook|linkedin|x|instagram' {...register('platform')} />
            <Input placeholder='Display name' {...register('display_name')} />
            <Input placeholder='External account id' {...register('external_account_id')} />
            <Input placeholder='Access token' {...register('access_token')} />
            <Input placeholder='Refresh token (optional)' {...register('refresh_token')} />
            <Input placeholder='Scopes (optional)' {...register('scopes')} />
            <Button type='submit' disabled={formState.isSubmitting} className='md:col-span-2'>
              {formState.isSubmitting ? 'Saving...' : 'Add account'}
            </Button>
          </form>
        </Card>
      )}

      <Card>
        <h2 className='mb-3 text-lg font-semibold'>Your Accounts</h2>
        <div className='space-y-2'>
          {accounts.map((a) => (
            <div key={a.id} className='flex items-start justify-between rounded border border-border p-3'>
              <div className='space-y-1'>
                <div className='flex items-center gap-2'>
                  <Badge>{a.platform}</Badge>
                  <p className='font-medium'>{a.display_name || a.external_account_id}</p>
                </div>
                <p className='text-sm text-gray-600'>Account ID: {a.external_account_id}</p>
                <p className='text-sm text-gray-600'>
                  Capabilities: {a.capabilities.supports_link ? 'link ' : ''}{a.capabilities.supports_image ? 'image' : 'no image'}
                </p>
                <p className='text-sm text-gray-600'>
                  Token expiry: {a.expires_at ? new Date(a.expires_at).toLocaleString() : 'Not provided'}
                </p>
              </div>
              <Button
                variant='outline'
                onClick={async () => {
                  try {
                    await apiFetch(`/accounts/${a.id}`, { method: 'DELETE', auth: true });
                    toast.success('Disconnected');
                    await loadAccounts();
                  } catch (e: unknown) {
                    toast.error(getErrorMessage(e, 'Disconnect failed'));
                  }
                }}
              >
                Disconnect
              </Button>
            </div>
          ))}
          {accounts.length === 0 && <p className='text-sm text-gray-600'>No accounts connected yet.</p>}
        </div>
      </Card>

      {selectingPageAccountId && facebookPages.length > 1 && (
        <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4'>
          <Card className='w-full max-w-lg'>
            <h3 className='mb-2 text-lg font-semibold'>Select Facebook Page</h3>
            <p className='mb-3 text-sm text-gray-600'>
              Multiple Pages were found for {activeFacebookAccount?.display_name || `account #${selectingPageAccountId}`}.
            </p>
            <div className='space-y-2'>
              {facebookPages.map((page) => (
                <label key={page.id} className='flex items-center gap-2 rounded border border-border p-2'>
                  <input
                    type='radio'
                    checked={selectedPageId === page.id}
                    onChange={() => setSelectedPageId(page.id)}
                  />
                  <span>{page.name}</span>
                </label>
              ))}
            </div>
            <div className='mt-4 flex gap-2'>
              <Button onClick={onSelectFacebookPage} disabled={!selectedPageId || savingPage}>
                {savingPage ? 'Saving...' : 'Use Selected Page'}
              </Button>
              <Button
                variant='outline'
                disabled={savingPage}
                onClick={() => {
                  setSelectingPageAccountId(null);
                  setFacebookPages([]);
                  setSelectedPageId('');
                }}
              >
                Cancel
              </Button>
            </div>
          </Card>
        </div>
      )}
    </ProtectedPage>
  );
}
