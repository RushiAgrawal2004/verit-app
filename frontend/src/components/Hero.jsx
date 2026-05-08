import React from 'react';
import { Image as ImageIcon, Video as VideoIcon } from 'lucide-react';
import UploadBox from './UploadBox.jsx';
import ResultCard from './ResultCard.jsx';

export default function Hero({
  mode, setMode,
  file, setFile,
  loading, result, error,
  onAnalyze, onClear,
}) {
  return (
    <section className="bg-white pt-24 pb-32">
      <div className="max-w-7xl mx-auto px-6">
        {/* Badge */}
        <div
          className="text-center opacity-0 animate-fade-in-up"
          style={{ animationDelay: '0.15s' }}
        >
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gray-100 border border-gray-200 text-xs font-medium text-gray-700">
            <span className="h-1.5 w-1.5 rounded-full bg-brand-500 animate-pulse-soft" />
            New · Now detecting both images and videos
          </span>
        </div>

        {/* Heading */}
        <h1
          className="mt-6 text-center text-6xl md:text-7xl font-semibold tracking-tight leading-[1.05] opacity-0 animate-fade-in-up"
          style={{ animationDelay: '0.2s' }}
        >
          <span className="block text-black">Detect AI-generated</span>
          <span className="block bg-gradient-to-r from-black via-gray-500 to-gray-400 bg-clip-text text-transparent">
            images & videos.
          </span>
        </h1>

        {/* Subheading */}
        <p
          className="mt-6 text-center text-lg md:text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed opacity-0 animate-fade-in-up"
          style={{ animationDelay: '0.3s' }}
        >
          Verify the authenticity of any photo or clip. Get a confident verdict in seconds — no signup required.
        </p>

        {/* Tabs */}
        <div
          className="mt-10 flex justify-center opacity-0 animate-fade-in-up"
          style={{ animationDelay: '0.35s' }}
        >
          <Tabs mode={mode} setMode={setMode} disabled={loading} />
        </div>

        {/* Upload box */}
        <div
          className="mt-8 max-w-2xl mx-auto opacity-0 animate-fade-in-up"
          style={{ animationDelay: '0.4s' }}
        >
          <UploadBox
            mode={mode}
            file={file}
            onFileSelected={setFile}
            onClear={onClear}
            onAnalyze={onAnalyze}
            loading={loading}
          />

          {error && (
            <div className="mt-5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700 animate-fade-in-overlay">
              {error}
            </div>
          )}

          {result && (
            <div className="mt-5">
              <ResultCard result={result} />
            </div>
          )}

          {!file && !result && (
            <p className="mt-6 text-center text-xs text-gray-400">
              We never store or share your files. Analysis happens on demand.
            </p>
          )}
        </div>
      </div>
    </section>
  );
}

function Tabs({ mode, setMode, disabled }) {
  const tabs = [
    { key: 'image', label: 'Images', icon: ImageIcon },
    { key: 'video', label: 'Videos', icon: VideoIcon },
  ];
  return (
    <div className="bg-gray-100 rounded-lg p-1 flex gap-2 justify-center">
      {tabs.map(({ key, label, icon: Icon }) => {
        const active = mode === key;
        return (
          <button
            key={key}
            onClick={() => !disabled && setMode(key)}
            disabled={disabled}
            className={`px-5 py-2 rounded-md text-sm font-medium inline-flex items-center gap-2 transition-all
              ${active ? 'bg-white shadow text-black' : 'text-gray-600 hover:text-black'}
              ${disabled ? 'opacity-60 cursor-not-allowed' : ''}`}
          >
            <Icon className="h-4 w-4" strokeWidth={2} />
            {label}
          </button>
        );
      })}
    </div>
  );
}
