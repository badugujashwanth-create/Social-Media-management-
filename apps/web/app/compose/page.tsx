'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { ProtectedPage } from '@/components/protected-page';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { apiFetch, getToken, resolveApiUrl } from '@/lib/api';
import { OAuthAccount, Post } from '@/lib/types';

const schema = z.object({
  text: z.string().min(1).max(5000),
  link_url: z.string().url().optional().or(z.literal('')),
});

type FormData = z.infer<typeof schema>;

export default function ComposePage() {
  const router = useRouter();
  const [accounts, setAccounts] = useState<OAuthAccount[]>([]);
  const [selected, setSelected] = useState<Record<number, boolean>>({});
  const [postToAll, setPostToAll] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [mediaUrl, setMediaUrl] = useState<string | null>(null);
  const [uploadFileName, setUploadFileName] = useState<string | null>(null);
  const { register, handleSubmit, formState, watch } = useForm<FormData>({ resolver: zodResolver(schema) });

  const linkValue = watch('link_url');

  useEffect(() => {
    apiFetch<OAuthAccount[]>('/accounts', { auth: true })
      .then((accs) => {
        setAccounts(accs);
        setSelected(Object.fromEntries(accs.map((a) => [a.id, true])));
      })
      .catch(() => {
        setAccounts([]);
        setSelected({});
      });
  }, []);

  const selectedAccounts = useMemo(() => {
    if (postToAll) return accounts;
    return accounts.filter((account) => selected[account.id]);
  }, [accounts, postToAll, selected]);

  const targetIds = useMemo(() => selectedAccounts.map((account) => account.id), [selectedAccounts]);

  const unsupportedImageTargets = useMemo(() => {
    if (!mediaUrl) return [];
    return selectedAccounts.filter((account) => !account.capabilities.supports_image);
  }, [mediaUrl, selectedAccounts]);

  const unsupportedLinkTargets = useMemo(() => {
    if (!linkValue) return [];
    return selectedAccounts.filter((account) => !account.capabilities.supports_link);
  }, [linkValue, selectedAccounts]);

  const upload = async (file: File) => {
    const token = getToken();
    const fd = new FormData();
    fd.append('file', file);
    setUploading(true);
    try {
      const res = await fetch(resolveApiUrl('/media/upload'), {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        body: fd,
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || 'Upload failed');
      }
      const body = await res.json();
      setMediaUrl(body.media_url);
      setUploadFileName(file.name);
      toast.success('Uploaded image');
    } finally {
      setUploading(false);
    }
  };

  const deselectUnsupportedImage = () => {
    const unsupportedIds = new Set(unsupportedImageTargets.map((item) => item.id));
    setPostToAll(false);
    setSelected((previous) => {
      const next: Record<number, boolean> = {};
      for (const account of accounts) {
        next[account.id] = Boolean(previous[account.id]) && !unsupportedIds.has(account.id);
      }
      return next;
    });
  };

  const onSubmit = async (data: FormData) => {
    try {
      const res = await apiFetch<Post>('/posts', {
        method: 'POST',
        auth: true,
        body: JSON.stringify({
          text: data.text,
          link_url: data.link_url || null,
          media_url: mediaUrl,
          post_to_all: postToAll,
          target_account_ids: targetIds,
        }),
      });
      toast.success('Post queued for publishing');
      router.push(`/posts?postId=${res.id}`);
    } catch (e: any) {
      toast.error(e.message);
    }
  };

  const canSubmit =
    selectedAccounts.length > 0 &&
    unsupportedImageTargets.length === 0 &&
    unsupportedLinkTargets.length === 0;

  return (
    <ProtectedPage>
      <h1 className='mb-4 text-2xl font-semibold'>Post Composer</h1>
      <Card className='mb-6'>
        <form className='space-y-4' onSubmit={handleSubmit(onSubmit)}>
          <Textarea placeholder='Write your post' {...register('text')} />
          <Input placeholder='Optional link URL' {...register('link_url')} />

          <div className='space-y-2'>
            <input
              type='file'
              accept='image/*'
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  upload(file).catch((err) => toast.error(err.message || 'Upload failed'));
                }
              }}
            />
            {mediaUrl && (
              <div className='rounded border border-border p-2 text-sm'>
                <p className='font-medium'>Image attached: {uploadFileName || 'uploaded image'}</p>
                <p className='truncate text-gray-600'>{mediaUrl}</p>
                <Button
                  type='button'
                  className='mt-2'
                  variant='outline'
                  onClick={() => {
                    setMediaUrl(null);
                    setUploadFileName(null);
                  }}
                >
                  Remove image
                </Button>
              </div>
            )}
          </div>

          <label className='flex items-center gap-2 text-sm'>
            <input type='checkbox' checked={postToAll} onChange={(e) => setPostToAll(e.target.checked)} />
            Post to all connected accounts
          </label>

          <div className='grid gap-2'>
            {accounts.map((a) => (
              <label key={a.id} className='flex items-center gap-2 rounded border border-border p-2'>
                <input
                  type='checkbox'
                  disabled={postToAll}
                  checked={postToAll ? true : !!selected[a.id]}
                  onChange={(e) => setSelected((p) => ({ ...p, [a.id]: e.target.checked }))}
                />
                <span className='font-medium'>
                  {a.platform} - {a.display_name || a.external_account_id}
                </span>
                <span className='ml-auto text-xs text-gray-600'>
                  {a.capabilities.supports_link ? 'link' : 'no-link'} | {a.capabilities.supports_image ? 'image' : 'no-image'}
                </span>
              </label>
            ))}
          </div>

          {unsupportedImageTargets.length > 0 && (
            <div className='rounded border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900'>
              <p>
                Selected targets do not support image publishing yet:{' '}
                {unsupportedImageTargets.map((a) => `${a.platform}:${a.display_name || a.external_account_id}`).join(', ')}.
              </p>
              <div className='mt-2 flex gap-2'>
                <Button type='button' variant='outline' onClick={() => setMediaUrl(null)}>
                  Remove image
                </Button>
                <Button type='button' variant='outline' onClick={deselectUnsupportedImage}>
                  Deselect unsupported targets
                </Button>
              </div>
            </div>
          )}

          {unsupportedLinkTargets.length > 0 && (
            <div className='rounded border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900'>
              <p>
                Selected targets do not support link publishing:{' '}
                {unsupportedLinkTargets.map((a) => `${a.platform}:${a.display_name || a.external_account_id}`).join(', ')}.
              </p>
            </div>
          )}

          <Button type='submit' disabled={formState.isSubmitting || uploading || !canSubmit}>
            {formState.isSubmitting ? 'Publishing...' : postToAll ? 'Post to All' : 'Post to Selected'}
          </Button>
        </form>
      </Card>
    </ProtectedPage>
  );
}
