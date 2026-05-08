import React from 'react';

const cases = [
  {
    title: 'Fake profiles',
    desc: 'Block AI-generated profile photos used in dating apps, marketplaces, and social platforms.',
    image: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=900&q=80&auto=format&fit=crop',
  },
  {
    title: 'Insurance fraud',
    desc: 'Detect fabricated incident photos and AI-generated damage submitted with claims.',
    image: 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=900&q=80&auto=format&fit=crop',
  },
  {
    title: 'Misinformation & fake news',
    desc: 'Stop synthesized images from being used to mislead readers and manipulate public opinion.',
    image: 'https://images.unsplash.com/photo-1495020689067-958852a7765e?w=900&q=80&auto=format&fit=crop',
  },
  {
    title: 'Deepfakes & impersonation',
    desc: 'Flag videos where a real person\'s face has been swapped or digitally manipulated.',
    image: 'https://images.unsplash.com/photo-1535930891776-0c2dfb7fda1a?w=900&q=80&auto=format&fit=crop',
  },
  {
    title: 'Marketplace spam',
    desc: 'Identify auto-generated product photos flooding listings and review sections.',
    image: 'https://images.unsplash.com/photo-1556742502-ec7c0e9f34b1?w=900&q=80&auto=format&fit=crop',
  },
  {
    title: 'Identity & KYC fraud',
    desc: 'Catch synthetic IDs and selfies before they slip through your verification flow.',
    image: 'https://images.unsplash.com/photo-1620207418302-439b387441b0?w=900&q=80&auto=format&fit=crop',
  },
];

export default function UseCases() {
  return (
    <section id="use-cases" className="py-20 sm:py-28">
      <div className="container-narrow">
        <div className="max-w-2xl">
          <span className="section-eyebrow">Use cases</span>
          <h2 className="section-heading">Wherever generative content creates risk.</h2>
          <p className="mt-6 text-ink-600 leading-relaxed">
            Trust & safety, fraud, news, marketplaces — anywhere a single fabricated image
            can cause real damage. Plug Verit into your moderation pipeline.
          </p>
        </div>

        <div className="mt-12 grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {cases.map((c) => (
            <article
              key={c.title}
              className="card overflow-hidden hover:shadow-card hover:-translate-y-1 transition-all duration-300 group"
            >
              <div className="aspect-[16/10] overflow-hidden bg-ink-100">
                <img
                  src={c.image}
                  alt={c.title}
                  loading="lazy"
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                />
              </div>
              <div className="p-6">
                <h3 className="text-base font-semibold text-ink-900 mb-1.5">{c.title}</h3>
                <p className="text-sm text-ink-500 leading-relaxed">{c.desc}</p>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
