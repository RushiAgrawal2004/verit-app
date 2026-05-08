import React from 'react';

export default function Footer() {
  return (
    <footer className="border-t border-ink-100 py-12">
      <div className="container-narrow">
        <div className="grid sm:grid-cols-4 gap-10">
          <div className="sm:col-span-2">
            <div className="flex items-center gap-2.5">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-brand-600 to-brand-400 flex items-center justify-center text-white font-bold text-sm">
                V
              </div>
              <span className="font-semibold text-ink-900 tracking-tight">Verit</span>
            </div>
            <p className="mt-4 text-sm text-ink-500 max-w-sm">
              AI-generated media detection for trust & safety, fraud, and content moderation teams.
            </p>
          </div>

          <FooterCol title="Product" links={['Detection API', 'Pricing', 'Changelog', 'Status']} />
          <FooterCol title="Company" links={['About', 'Blog', 'Contact', 'Terms']} />
        </div>

        <div className="mt-10 pt-6 border-t border-ink-100 flex flex-col sm:flex-row justify-between items-center gap-3 text-xs text-ink-400">
          <span>© {new Date().getFullYear()} Verit. All rights reserved.</span>
          <span>Built on DeepSafe + AI-Generated-Video-Detector.</span>
        </div>
      </div>
    </footer>
  );
}

function FooterCol({ title, links }) {
  return (
    <div>
      <div className="text-xs font-semibold tracking-widest uppercase text-ink-700 mb-4">{title}</div>
      <ul className="space-y-2.5">
        {links.map((l) => (
          <li key={l}>
            <a href="#" className="text-sm text-ink-500 hover:text-ink-900 transition-colors">{l}</a>
          </li>
        ))}
      </ul>
    </div>
  );
}
