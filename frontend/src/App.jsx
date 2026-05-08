import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';

import Header from './components/Header.jsx';
import Hero from './components/Hero.jsx';
import SampleGallery from './components/SampleGallery.jsx';
import Stats from './components/Stats.jsx';
import UseCases from './components/UseCases.jsx';
import SupportedModels from './components/SupportedModels.jsx';
import DemoResult from './components/DemoResult.jsx';
import FAQ from './components/FAQ.jsx';
import CTASection from './components/CTASection.jsx';
import Footer from './components/Footer.jsx';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

export default function App() {
  const [mode, setMode] = useState('image');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const heroRef = useRef(null);

  // Reset transient state when the user switches tab
  useEffect(() => {
    setFile(null);
    setResult(null);
    setError(null);
  }, [mode]);

  const onClear = () => {
    setFile(null);
    setResult(null);
    setError(null);
  };

  const onAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    const form = new FormData();
    form.append('file', file);
    try {
      const { data } = await axios.post(`${API_BASE}/detect`, form, {
        timeout: 600_000,
      });
      setResult(data);
    } catch (e) {
      const detail =
        e.response?.data?.detail ||
        e.message ||
        'Detection failed — check that backend services are reachable.';
      setError(typeof detail === 'string' ? detail : JSON.stringify(detail));
    } finally {
      setLoading(false);
    }
  };

  const scrollToHero = () => {
    heroRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="min-h-full flex flex-col bg-white text-ink-900">
      <Header />
      <main className="flex-1">
        <div ref={heroRef}>
          <Hero
            mode={mode}
            setMode={setMode}
            file={file}
            setFile={setFile}
            loading={loading}
            result={result}
            error={error}
            onAnalyze={onAnalyze}
            onClear={onClear}
          />
        </div>
        <SampleGallery />
        <Stats />
        <UseCases />
        <SupportedModels />
        <DemoResult />
        <FAQ />
        <CTASection onCTA={scrollToHero} />
      </main>
      <Footer />
    </div>
  );
}
