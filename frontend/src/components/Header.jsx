import React from 'react';

export default function Header() {
  return (
    <header
      className="sticky top-0 z-30 bg-white/85 backdrop-blur-md border-b border-ink-100 opacity-0 animate-fade-in-up"
      style={{ animationDelay: '0.1s' }}
    >
      <div className="max-w-7xl mx-auto px-6 flex items-center justify-between h-16">
        <a href="#" className="flex items-center gap-2.5 group">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-brand-600 to-brand-400 flex items-center justify-center text-white font-bold text-sm shadow-glow">
            V
          </div>
          <span className="font-semibold text-ink-900 tracking-tight">Verit</span>
        </a>

        <nav className="hidden md:flex items-center gap-8 text-sm text-ink-600">
          <a href="#use-cases" className="hover:text-ink-900 transition-colors">Use cases</a>
          <a href="#accuracy" className="hover:text-ink-900 transition-colors">Accuracy</a>
          <a href="#models" className="hover:text-ink-900 transition-colors">Models</a>
          <a href="#docs" className="hover:text-ink-900 transition-colors">Docs</a>
        </nav>

        <div className="flex items-center gap-2">
          <a href="#login" className="hidden sm:inline-block text-sm text-ink-600 hover:text-ink-900 px-3 py-2">
            Log in
          </a>
          <a href="#try" className="btn-primary text-sm">Sign up</a>
        </div>
      </div>
    </header>
  );
}
