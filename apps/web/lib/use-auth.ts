'use client';

import { useEffect, useState } from 'react';
import { getToken } from '@/lib/api';

export function useAuthToken() {
  const [token, setTokenState] = useState('');

  useEffect(() => {
    setTokenState(getToken());
  }, []);

  return token;
}
