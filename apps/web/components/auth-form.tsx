'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { apiFetch, getErrorMessage, setToken } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
});

type FormData = z.infer<typeof schema>;

export function AuthForm({ mode }: { mode: 'login' | 'signup' }) {
  const router = useRouter();
  const { register, handleSubmit, formState } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    try {
      const res = await apiFetch<{ access_token: string }>(`/auth/${mode}`, {
        method: 'POST',
        body: JSON.stringify(data),
      });
      setToken(res.access_token);
      toast.success(mode === 'login' ? 'Logged in' : 'Account created');
      router.push('/dashboard');
    } catch (e: unknown) {
      toast.error(getErrorMessage(e, 'Authentication failed'));
    }
  };

  return (
    <div className='flex min-h-screen items-center justify-center px-4'>
      <Card className='w-full max-w-md space-y-4'>
        <h1 className='text-xl font-semibold'>{mode === 'login' ? 'Login' : 'Sign up'}</h1>
        <form onSubmit={handleSubmit(onSubmit)} className='space-y-3'>
          <Input placeholder='Email' type='email' {...register('email')} />
          <Input placeholder='Password' type='password' {...register('password')} />
          <Button type='submit' disabled={formState.isSubmitting} className='w-full'>
            {formState.isSubmitting ? 'Please wait...' : mode === 'login' ? 'Login' : 'Create account'}
          </Button>
        </form>
        <p className='text-sm text-gray-600'>
          {mode === 'login' ? 'No account?' : 'Already have an account?'}{' '}
          <Link href={mode === 'login' ? '/signup' : '/login'} className='text-primary underline'>
            {mode === 'login' ? 'Sign up' : 'Login'}
          </Link>
        </p>
      </Card>
    </div>
  );
}
