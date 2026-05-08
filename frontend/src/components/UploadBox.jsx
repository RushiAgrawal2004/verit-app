import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Upload } from 'lucide-react';

export default function UploadBox({ mode, file, onFileSelected, onClear, onAnalyze, loading }) {
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const accept = mode === 'video' ? 'video/*' : 'image/*';

  const acceptsType = (type, name = '') => {
    const t = (type || '').toLowerCase();
    const n = name.toLowerCase();
    if (mode === 'video') {
      return t.startsWith('video/') || /\.(mp4|mov|mkv|avi|webm|m4v)$/i.test(n);
    }
    return t.startsWith('image/') || /\.(jpg|jpeg|png|webp|gif|bmp|tiff)$/i.test(n);
  };

  const handleFiles = useCallback((files) => {
    if (!files || files.length === 0) return;
    const f = files[0];
    if (!acceptsType(f.type, f.name)) return;
    onFileSelected(f);
  }, [mode, onFileSelected]);

  if (file) {
    const isVideo = (file.type || '').startsWith('video/');
    return (
      <div className="card overflow-hidden animate-fade-up">
        <div className="bg-ink-900 max-h-[440px] flex items-center justify-center">
          {isVideo ? (
            <video src={previewUrl} controls className="w-full max-h-[440px] object-contain" />
          ) : (
            <img src={previewUrl} alt="preview" className="w-full max-h-[440px] object-contain" />
          )}
        </div>
        <div className="flex items-center justify-between p-4 border-t border-ink-100">
          <div className="min-w-0">
            <div className="text-sm font-medium text-ink-900 truncate">{file.name}</div>
            <div className="text-xs text-ink-500 mt-0.5">
              {(file.size / 1024 / 1024).toFixed(2)} MB · {file.type || 'unknown'}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={onClear} disabled={loading} className="btn-ghost">
              Replace
            </button>
            <button onClick={onAnalyze} disabled={loading} className="btn-primary">
              {loading ? (
                <>
                  <Spinner /> Analyzing
                </>
              ) : (
                <>
                  Run detection
                  <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </>
              )}
            </button>
          </div>
        </div>
        {loading && <ProgressShimmer mode={mode} />}
      </div>
    );
  }

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
      className={`bg-white border-2 border-dashed rounded-2xl p-10 cursor-pointer text-center transition
        ${dragOver
          ? 'border-brand-400 bg-brand-50/40 scale-[1.005]'
          : 'border-gray-200 hover:bg-gray-50 hover:border-gray-300'}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      <div className="mx-auto h-14 w-14 rounded-2xl bg-gray-100 border border-gray-200 flex items-center justify-center mb-5">
        <Upload className="h-6 w-6 text-gray-700" strokeWidth={2} />
      </div>
      <h3 className="text-lg font-semibold text-ink-900 mb-1">
        Drop {mode === 'video' ? 'a video' : 'an image'} or click to browse
      </h3>
      <p className="text-sm text-ink-500">
        {mode === 'video' ? 'MP4, MOV, AVI, MKV, WebM' : 'JPG, PNG, WebP, GIF'} · up to ~100 MB
      </p>
    </div>
  );
}

function Spinner() {
  return (
    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.25" />
      <path d="M22 12a10 10 0 0 1-10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

function ProgressShimmer({ mode }) {
  return (
    <div className="px-4 py-3 border-t border-ink-100 flex items-center gap-3 bg-ink-50/60">
      <div className="flex-1 h-1.5 rounded-full bg-ink-200 overflow-hidden">
        <div className="h-full w-2/3 bg-gradient-to-r from-brand-500 to-brand-300 animate-pulse-soft" />
      </div>
      <span className="text-xs text-ink-500 whitespace-nowrap">
        {mode === 'video' ? 'Video analysis · 1–3 min' : 'Analyzing image…'}
      </span>
    </div>
  );
}
