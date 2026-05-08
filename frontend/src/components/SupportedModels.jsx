import React from 'react';

const models = [
  { name: 'Midjourney', short: 'MJ' },
  { name: 'Stable Diffusion', short: 'SD' },
  { name: 'DALL·E', short: 'D·E' },
  { name: 'GPT-4o', short: '4o' },
  { name: 'Flux', short: 'FX' },
  { name: 'Ideogram', short: 'ID' },
  { name: 'Bing Creator', short: 'BG' },
  { name: 'GANs', short: 'GAN' },
];

export default function SupportedModels() {
  return (
    <section id="models" className="py-20 sm:py-28 border-t border-ink-100">
      <div className="container-narrow">
        <div className="max-w-2xl">
          <span className="section-eyebrow">Coverage</span>
          <h2 className="section-heading">Detects content from every major generator.</h2>
          <p className="mt-6 text-ink-600 leading-relaxed">
            Detection runs on the pixel signal — not on watermarks or metadata — so it
            still works after stripping, re-compression, or screenshots.
          </p>
        </div>

        <div className="mt-12 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          {models.map((m) => (
            <div
              key={m.name}
              className="card aspect-square flex flex-col items-center justify-center text-center p-3 hover:shadow-card hover:-translate-y-0.5 transition-all duration-200"
            >
              <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-ink-100 to-ink-50 flex items-center justify-center text-ink-700 font-semibold text-xs mb-2 border border-ink-100">
                {m.short}
              </div>
              <div className="text-xs text-ink-700 font-medium leading-tight">{m.name}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
