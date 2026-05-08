import React from 'react';

const subscores = [
  { label: 'Diffusion · MidJourney', value: 98, group: 'diffusion' },
  { label: 'Diffusion · Stable Diffusion', value: 12, group: 'diffusion' },
  { label: 'GAN · StyleGAN', value: 4, group: 'gan' },
  { label: 'Face manipulation', value: 1, group: 'manipulation' },
];

export default function DemoResult() {
  return (
    <section className="py-20 sm:py-28 bg-ink-50">
      <div className="container-narrow">
        <div className="max-w-2xl mb-12">
          <span className="section-eyebrow">Detail</span>
          <h2 className="section-heading">More than just a yes or no.</h2>
          <p className="mt-6 text-ink-600 leading-relaxed">
            Each scan returns a top-level verdict plus per-generator scores so you can see
            <em> which</em> tool likely produced the content. Useful for review queues,
            citations, and audit trails.
          </p>
        </div>

        {/* Browser mockup frame */}
        <div className="rounded-2xl bg-white shadow-card border border-ink-200 overflow-hidden max-w-5xl mx-auto animate-fade-up">
          <div className="flex items-center gap-2 px-4 py-3 border-b border-ink-100 bg-ink-50">
            <div className="flex gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-rose-300" />
              <span className="h-2.5 w-2.5 rounded-full bg-amber-300" />
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-300" />
            </div>
            <div className="flex-1 mx-4">
              <div className="bg-white border border-ink-200 rounded-md px-3 py-1 text-xs text-ink-500 inline-flex items-center gap-2 max-w-md w-full">
                <svg className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd"/></svg>
                verit.app/detect
              </div>
            </div>
            <div className="hidden sm:flex gap-1.5">
              <span className="h-5 w-5 rounded bg-ink-100" />
              <span className="h-5 w-5 rounded bg-ink-100" />
            </div>
          </div>

          <div className="p-6 sm:p-10 grid md:grid-cols-2 gap-8 items-center">
            <div className="rounded-xl overflow-hidden bg-ink-100 aspect-square">
              <img
                src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&q=80&auto=format&fit=crop"
                alt="Sample"
                className="w-full h-full object-cover"
              />
            </div>

            <div>
              <div className="flex items-start justify-between gap-3 mb-5">
                <div>
                  <h3 className="text-2xl sm:text-3xl font-semibold text-rose-600">Likely AI-generated</h3>
                </div>
                <div className="px-3 py-2 rounded-lg bg-ink-900 text-white">
                  <div className="text-2xl font-bold tabular-nums leading-none">99%</div>
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-xs text-ink-600 mb-1">
                    <span className="font-medium text-ink-700">GenAI</span>
                    <span className="tabular-nums">99%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-ink-100 overflow-hidden">
                    <div className="h-full rounded-full bg-rose-500" style={{ width: '99%' }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs text-ink-600 mb-1">
                    <span className="font-medium text-ink-700">Face manipulation</span>
                    <span className="tabular-nums">1%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-ink-100 overflow-hidden">
                    <div className="h-full rounded-full bg-ink-300" style={{ width: '1%' }} />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-x-6 gap-y-2 mt-6 pt-5 border-t border-ink-100">
                <div className="text-xs font-semibold text-ink-700 col-span-2 mb-1">Diffusion</div>
                {subscores.filter(s => s.group === 'diffusion').map(s => <Sub key={s.label} {...s} />)}
                <div className="text-xs font-semibold text-ink-700 col-span-2 mt-2 mb-1">GAN</div>
                {subscores.filter(s => s.group === 'gan').map(s => <Sub key={s.label} {...s} />)}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Sub({ label, value }) {
  const short = label.split(' · ').pop();
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-ink-600 flex-1 truncate">{short}</span>
      <div className="h-1 w-20 rounded-full bg-ink-100 overflow-hidden">
        <div className={`h-full rounded-full ${value > 50 ? 'bg-rose-400' : 'bg-ink-300'}`} style={{ width: `${value}%` }} />
      </div>
      <span className="text-xs tabular-nums text-ink-500 w-9 text-right">{value}%</span>
    </div>
  );
}
