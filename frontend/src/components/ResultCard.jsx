import React from 'react';

export default function ResultCard({ result }) {
  const isAi = result.verdict === 'AI';
  const pct = Math.max(0, Math.min(100, Math.round((result.confidence || 0) * 100)));

  const verdictTitle = isAi ? 'Likely AI-generated' : 'Likely real';
  const accent = isAi
    ? { text: 'text-rose-600', bar: 'bg-rose-500', chipBg: 'bg-rose-50', chipBorder: 'border-rose-100', dot: 'bg-rose-500' }
    : { text: 'text-emerald-600', bar: 'bg-emerald-500', chipBg: 'bg-emerald-50', chipBorder: 'border-emerald-100', dot: 'bg-emerald-500' };

  return (
    <div className="card p-6 sm:p-8 animate-fade-up">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-6">
        <div>
          <div className="text-xs font-semibold tracking-widest uppercase text-ink-400 mb-1.5">
            Result
          </div>
          <h3 className={`text-2xl sm:text-3xl font-semibold ${accent.text}`}>{verdictTitle}</h3>
        </div>
        <span
          className={`text-[11px] font-medium px-2.5 py-1 rounded-full border ${accent.chipBg} ${accent.chipBorder} text-ink-700 inline-flex items-center gap-1.5`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${accent.dot}`} />
          {result.type} · {result.service}
        </span>
      </div>

      <div className="space-y-2.5">
        <div className="flex items-baseline justify-between">
          <span className="text-sm text-ink-600">Confidence</span>
          <span className="text-2xl font-semibold text-ink-900 tabular-nums">{pct}%</span>
        </div>
        <div className="h-2 rounded-full bg-ink-100 overflow-hidden">
          <div
            className={`h-full rounded-full ${accent.bar} animate-progress`}
            style={{ '--bar-w': `${pct}%`, width: `${pct}%` }}
          />
        </div>
        <p className="text-xs text-ink-500 pt-1">
          {isAi
            ? 'High confidence the media is generated or significantly modified by AI.'
            : 'Detector found no strong indicators of AI generation in this media.'}
        </p>
      </div>

      {result.details && (
        <details className="mt-6 group">
          <summary className="cursor-pointer text-xs text-ink-500 hover:text-ink-700 select-none flex items-center gap-1.5">
            <svg className="h-3 w-3 transition-transform group-open:rotate-90" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M7.5 4.5l6 5.5-6 5.5V4.5z" clipRule="evenodd" />
            </svg>
            View raw response
          </summary>
          <pre className="mt-3 p-4 rounded-xl bg-ink-50 border border-ink-100 overflow-x-auto text-[11px] text-ink-700 leading-relaxed">
            {JSON.stringify(result, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}
