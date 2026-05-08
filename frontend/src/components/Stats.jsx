import React from 'react';

const benchmark = [
  { name: 'Verit', score: 98.3, ours: true },
  { name: 'Competitor A', score: 86.2 },
  { name: 'Competitor B', score: 76.3 },
  { name: 'Competitor C', score: 57.6 },
  { name: 'Competitor D', score: 47.1 },
];

export default function Stats() {
  return (
    <section id="accuracy" className="py-20 sm:py-28 bg-ink-50">
      <div className="container-narrow grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
        <div className="animate-fade-up">
          <span className="section-eyebrow">Accuracy</span>
          <h2 className="section-heading">Built for the highest accuracy.</h2>
          <p className="mt-6 text-ink-600 leading-relaxed">
            Verit ensembles state-of-the-art detectors trained across diverse generators —
            from diffusion to GANs — and benchmarks above leading alternatives in third-party
            evaluations.
          </p>
          <div className="mt-8 grid grid-cols-3 gap-6">
            <Metric value="98.3%" label="Detection accuracy" />
            <Metric value="<2s" label="Avg image latency" />
            <Metric value="15+" label="Generators covered" />
          </div>
        </div>

        <div className="card p-6 sm:p-8 animate-fade-up">
          <div className="flex items-center justify-between mb-5">
            <div>
              <div className="text-sm font-semibold text-ink-900">AI image detection</div>
              <div className="text-xs text-ink-500 mt-0.5">Independent benchmark</div>
            </div>
            <span className="text-[11px] text-ink-500 px-2 py-1 rounded-full border border-ink-200 bg-white">
              Higher is better
            </span>
          </div>

          <div className="space-y-3.5">
            {benchmark.map((b) => (
              <div key={b.name} className="space-y-1.5">
                <div className="flex justify-between text-sm">
                  <span className={b.ours ? 'font-semibold text-ink-900' : 'text-ink-600'}>
                    {b.name}
                  </span>
                  <span className={`tabular-nums ${b.ours ? 'font-semibold text-ink-900' : 'text-ink-500'}`}>
                    {b.score.toFixed(1)}%
                  </span>
                </div>
                <div className="h-2.5 rounded-full bg-ink-100 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${b.ours ? 'bg-gradient-to-r from-brand-600 to-brand-400' : 'bg-ink-300'}`}
                    style={{ width: `${b.score}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function Metric({ value, label }) {
  return (
    <div>
      <div className="text-2xl sm:text-3xl font-semibold text-ink-900 tabular-nums">{value}</div>
      <div className="text-xs text-ink-500 mt-1">{label}</div>
    </div>
  );
}
