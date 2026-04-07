'use client';

import { useSyncExternalStore } from 'react';
import { getToken } from '@/lib/api';

function subscribe(onStoreChange: () => void) {
  window.addEventListener('storage', onStoreChange);
  return () => window.removeEventListener('storage', onStoreChange);
}

function getSnapshot() {
  return getToken();
}

function getServerSnapshot() {
  return '';
}

export function useAuthToken() {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
