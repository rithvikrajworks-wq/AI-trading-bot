// src/app/layout.tsx
import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'AI Stock Analyzer',
  description: 'Real‑time AI powered stock analysis dashboard',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full bg-slate-950 text-slate-100">
      <body className="h-full antialiased">
        {children}
      </body>
    </html>
  );
}
