import React from 'react';
import { Hero } from './components/Hero';
import { Features } from './components/Features';

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between">
      <header className="border-b border-slate-200 bg-white py-4 px-6">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <span className="font-extrabold text-xl text-indigo-600 tracking-tight">CloudScale</span>
          <nav className="flex items-center gap-6 text-sm font-semibold text-slate-600">
            <a href="#features" className="hover:text-slate-900 transition-colors">Features</a>
            <a href="#docs" className="hover:text-slate-900 transition-colors">Docs</a>
            <a href="#login" className="px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors">Sign In</a>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <Hero />
        <Features />
      </main>

      <footer className="py-8 bg-white border-t border-slate-200 text-center text-xs text-slate-500">
        <p>&copy; {new Date().getFullYear()} CloudScale Inc. All rights reserved.</p>
      </footer>
    </div>
  );
}
