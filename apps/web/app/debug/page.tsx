'use client';

import { useState } from 'react';
import { API_BASE, getErrorMessage, resolveApiUrl } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function DebugPage() {
  const [lastResponse, setLastResponse] = useState<string>('');
  const [lastError, setLastError] = useState<string>('');

  const ping = async () => {
    const url = resolveApiUrl('/health');
    setLastError('');
    try {
      const res = await fetch(url, { cache: 'no-store' });
      const body = await res.json();
      setLastResponse(JSON.stringify(body));
    } catch (err: unknown) {
      setLastError(getErrorMessage(err, `Ping failed for ${url}`));
      setLastResponse('');
    }
  };

  return (
    <main className='mx-auto max-w-3xl space-y-4 p-4'>
      <h1 className='text-2xl font-semibold'>Debug</h1>
      <Card className='space-y-2'>
        <p><strong>Resolved API_BASE:</strong> {API_BASE}</p>
        <p><strong>Health URL:</strong> {resolveApiUrl('/health')}</p>
        <Button onClick={ping}>Ping API</Button>
      </Card>

      {lastResponse && (
        <Card>
          <h2 className='mb-2 text-lg font-semibold'>Ping Response</h2>
          <pre className='overflow-auto text-sm'>{lastResponse}</pre>
        </Card>
      )}

      {lastError && (
        <Card>
          <h2 className='mb-2 text-lg font-semibold text-red-600'>Last Error</h2>
          <pre className='overflow-auto text-sm text-red-700'>{lastError}</pre>
        </Card>
      )}
    </main>
  );
}
