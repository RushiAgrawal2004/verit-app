import React, { useState } from 'react';

const faqs = [
  {
    q: 'How is it possible to tell if an image or video is AI-generated?',
    a: 'AI generators leave subtle statistical signatures in the pixel content — frequency artifacts, texture inconsistencies, lighting anomalies. Our models are trained on millions of paired real and synthetic samples to learn these signatures across a wide range of generators.',
  },
  {
    q: 'Can an AI media detector replace human judgment?',
    a: 'No. These tools are decision-support, not adjudicators. Use them to triage at scale and flag content for human review — especially when stakes are high (legal, journalism, identity verification).',
  },
  {
    q: 'What are the limitations?',
    a: 'Heavily compressed, cropped, or upscaled media can lose the signal. New generators that haven\'t appeared in training can also slip through. Confidence scores are an estimate — treat anything in the 40–60% range as uncertain.',
  },
  {
    q: 'What does the confidence score actually mean?',
    a: 'It\'s the model\'s estimated probability that the input is AI-generated. A score of 90% means the model is highly confident; 50% means it\'s a coin flip and the result should not be trusted in isolation.',
  },
  {
    q: 'How do you keep up with new AI generators?',
    a: 'We continuously fine-tune on outputs from newly released models (MidJourney, SDXL, Flux, GPT-4o image, etc.) and rotate detection ensembles to maintain coverage as the landscape shifts.',
  },
];

export default function FAQ() {
  const [open, setOpen] = useState(0);
  return (
    <section className="py-20 sm:py-28 border-t border-ink-100">
      <div className="container-narrow max-w-4xl">
        <div className="mb-12">
          <span className="section-eyebrow">FAQ</span>
          <h2 className="section-heading">Frequently asked questions.</h2>
        </div>
        <div className="divide-y divide-ink-100 border-t border-ink-100">
          {faqs.map((f, i) => {
            const isOpen = open === i;
            return (
              <div key={f.q}>
                <button
                  onClick={() => setOpen(isOpen ? -1 : i)}
                  className="w-full flex items-center justify-between gap-4 py-5 text-left group"
                >
                  <span className={`text-base sm:text-lg font-medium transition-colors ${isOpen ? 'text-ink-900' : 'text-ink-700 group-hover:text-ink-900'}`}>
                    {f.q}
                  </span>
                  <span className={`flex-none h-8 w-8 rounded-full border flex items-center justify-center transition-all ${isOpen ? 'border-brand-200 bg-brand-50 rotate-45' : 'border-ink-200 bg-white group-hover:border-ink-300'}`}>
                    <svg className={`h-3.5 w-3.5 ${isOpen ? 'text-brand-600' : 'text-ink-500'}`} viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd"/>
                    </svg>
                  </span>
                </button>
                <div
                  className="grid transition-all duration-300 ease-out"
                  style={{ gridTemplateRows: isOpen ? '1fr' : '0fr' }}
                >
                  <div className="overflow-hidden">
                    <p className="pb-6 pr-12 text-ink-600 leading-relaxed text-sm sm:text-base">{f.a}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
