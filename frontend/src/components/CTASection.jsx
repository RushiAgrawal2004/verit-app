import React from 'react';

export default function CTASection({ onCTA }) {
  return (
    <section className="py-20 sm:py-28">
      <div className="container-narrow">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-brand-700 via-brand-600 to-brand-500 p-10 sm:p-16 text-center shadow-glow">
          <div className="absolute inset-0 opacity-20 pointer-events-none"
            style={{
              backgroundImage:
                'radial-gradient(circle at 30% 20%, rgba(255,255,255,0.4), transparent 40%), radial-gradient(circle at 80% 80%, rgba(255,255,255,0.3), transparent 50%)',
            }}
          />
          <div className="relative">
            <h2 className="text-3xl sm:text-4xl font-semibold text-white tracking-tight">
              Try it on your own file.
            </h2>
            <p className="mt-4 text-brand-100 max-w-xl mx-auto">
              No account, no setup. Drop a file and get a verdict in seconds.
            </p>
            <div className="mt-8 flex items-center justify-center gap-3 flex-wrap">
              <button
                onClick={onCTA}
                className="px-6 py-3 rounded-lg bg-white text-brand-700 font-semibold text-sm hover:bg-brand-50 active:bg-brand-100 transition-colors shadow-soft"
              >
                Upload your file
              </button>
              <a
                href="#docs"
                className="px-6 py-3 rounded-lg border border-white/30 text-white font-medium text-sm hover:bg-white/10 transition-colors"
              >
                View API docs
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
