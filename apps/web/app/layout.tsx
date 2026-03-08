import './globals.css';
import type React from 'react';
import { AppToaster } from '@/components/toaster';

export const metadata = {
  title: 'SMCC',
  description: 'Social Media Control Center',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang='en'>
      <body>
        {children}
        <AppToaster />
      </body>
    </html>
  );
}
