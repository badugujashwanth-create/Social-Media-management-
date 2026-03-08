'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { clearToken } from '@/lib/api';
import { Button } from '@/components/ui/button';

const links = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/accounts', label: 'Accounts' },
  { href: '/compose', label: 'Compose' },
  { href: '/posts', label: 'Posts' },
  { href: '/analytics', label: 'Analytics' },
  { href: '/debug', label: 'Debug' },
];

export function TopNav() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <header className='border-b border-border bg-white'>
      <div className='mx-auto flex max-w-6xl items-center justify-between px-4 py-3'>
        <div className='flex gap-4'>
          {links.map((l) => (
            <Link key={l.href} href={l.href} className={`text-sm ${pathname === l.href ? 'font-bold text-primary' : 'text-gray-600'}`}>
              {l.label}
            </Link>
          ))}
        </div>
        <Button
          variant='outline'
          onClick={() => {
            clearToken();
            router.push('/login');
          }}
        >
          Logout
        </Button>
      </div>
    </header>
  );
}
