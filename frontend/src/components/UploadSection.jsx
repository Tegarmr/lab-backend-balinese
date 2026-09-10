import { useState, useRef, useCallback } from 'react';
import { transliterateImage } from '../api/client';

/**
 * Upload section with drag & drop and file input.
 */
export default function UploadSection({ onUpload, onProcessingStart, onError, isProcessing }) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [preview, setPreview] = useState(null);
  const fileInputRef = useRef(null);

  const handleFile = useCallback(async (file) => {
    if (!file) return;

    // Validate file type
    const allowed = ['image/jpeg', 'image/png', 'image/bmp', 'image/tiff'];
    if (!allowed.includes(file.type)) {
      onError('Format file tidak didukung. Gunakan JPG, PNG, BMP, atau TIFF.');
      return;
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      onError('Ukuran file terlalu besar. Maksimal 10MB.');
      return;
    }

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(file);

    // Start processing
    onProcessingStart();

    try {
      const result = await transliterateImage(file);
      onUpload(result);
    } catch (err) {
      onError(err.message || 'Gagal memproses gambar. Coba lagi.');
    }
  }, [onUpload, onProcessingStart, onError]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragActive(false);
    const file = e.dataTransfer.files[0];
    handleFile(file);
  }, [handleFile]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragActive(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragActive(false);
  }, []);

  const handleClick = useCallback(() => {
    if (!isProcessing) {
      fileInputRef.current?.click();
    }
  }, [isProcessing]);

  const handleInputChange = useCallback((e) => {
    const file = e.target.files[0];
    handleFile(file);
    e.target.value = '';
  }, [handleFile]);

  return (
    <div id="upload-section">
      <div
        className={`dropzone cursor-pointer p-8 sm:p-12 text-center transition-all duration-300 ${
          isDragActive ? 'active' : ''
        } ${isProcessing ? 'opacity-50 pointer-events-none' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={handleClick}
        role="button"
        tabIndex={0}
        id="dropzone"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/bmp,image/tiff"
          className="hidden"
          onChange={handleInputChange}
          id="file-input"
        />

        <div className="flex flex-col items-center gap-4">
          {/* Icon */}
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-accent-gold/10 to-primary-700/10 border border-dark-border flex items-center justify-center">
            <svg className="w-8 h-8 text-accent-gold" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
          </div>

          {/* Text */}
          <div>
            <p className="text-dark-text font-medium text-lg">
              {isDragActive ? 'Lepaskan gambar di sini' : 'Seret & lepas foto lontar di sini'}
            </p>
            <p className="text-dark-text-muted text-sm mt-1">
              atau <span className="text-accent-gold hover:text-accent-amber transition-colors">klik untuk memilih file</span>
            </p>
          </div>

          {/* Supported formats */}
          <div className="flex items-center gap-2 mt-1">
            {['JPG', 'PNG', 'BMP', 'TIFF'].map((fmt) => (
              <span
                key={fmt}
                className="text-xs px-2 py-0.5 rounded bg-dark-card border border-dark-border text-dark-text-muted"
              >
                {fmt}
              </span>
            ))}
            <span className="text-xs text-dark-text-muted">• Maks 10MB</span>
          </div>
        </div>
      </div>

      {/* Preview thumbnail */}
      {preview && !isProcessing && (
        <div className="mt-3 flex justify-center">
          <p className="text-dark-text-muted text-xs">
            Gambar berhasil diupload ✓
          </p>
        </div>
      )}
    </div>
  );
}
