import React from 'react';

// Stable Unsplash photo IDs — diverse subjects so users see we cover anything.
const samples = [
  { url: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=600&q=80&auto=format&fit=crop', alt: 'Portrait' },
  { url: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&q=80&auto=format&fit=crop', alt: 'Man in suit' },
  { url: 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&q=80&auto=format&fit=crop', alt: 'Food' },
  { url: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&q=80&auto=format&fit=crop', alt: 'Mountain landscape' },
  { url: 'https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=600&q=80&auto=format&fit=crop', alt: 'Cityscape' },
  { url: 'https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=600&q=80&auto=format&fit=crop', alt: 'Dog' },
  { url: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=600&q=80&auto=format&fit=crop', alt: 'Face' },
  { url: 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=600&q=80&auto=format&fit=crop', alt: 'Architecture' },
];

export default function SampleGallery() {
  return (
    <section className="py-20 sm:py-24 border-t border-ink-100">
      <div className="container-narrow">
        <div className="flex items-end justify-between flex-wrap gap-4 mb-10">
          <div className="max-w-2xl">
            <span className="section-eyebrow">Coverage</span>
            <h2 className="section-heading">Tested across the content people actually share.</h2>
          </div>
          <p className="text-ink-500 max-w-md text-sm leading-relaxed">
            Portraits, products, landscapes, screenshots — Verit performs reliably on the
            messy, real-world media that flows through your platform.
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
          {samples.map((s, i) => (
            <figure
              key={s.url}
              className="relative aspect-square overflow-hidden rounded-2xl bg-ink-100 group cursor-pointer"
              style={{ animation: `fadeUp 0.5s ${i * 60}ms cubic-bezier(0.22,1,0.36,1) backwards` }}
            >
              <img
                src={s.url}
                alt={s.alt}
                loading="lazy"
                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-ink-900/40 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              <figcaption className="absolute bottom-3 left-3 text-white text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                {s.alt}
              </figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}
