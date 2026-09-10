import { useState, useCallback } from 'react';
import Header from './components/Header';
import UploadSection from './components/UploadSection';
import ProcessingStatus from './components/ProcessingStatus';
import ResultsPanel from './components/ResultsPanel';
import './index.css';

function App() {
  const [result, setResult] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [processingStage, setProcessingStage] = useState('');

  const handleUpload = useCallback((data) => {
    setResult(data);
    setIsProcessing(false);
    setError(null);
    setProcessingStage('');
  }, []);

  const handleProcessingStart = useCallback(() => {
    setIsProcessing(true);
    setError(null);
    setResult(null);
    setProcessingStage('Mengunggah dan memproses gambar...');
  }, []);

  const handleError = useCallback((err) => {
    setIsProcessing(false);
    setError(err);
    setProcessingStage('');
  }, []);

  const handleReset = useCallback(() => {
    setResult(null);
    setIsProcessing(false);
    setError(null);
    setProcessingStage('');
  }, []);

  return (
    <div className="min-h-screen bg-dark-bg">
      <Header />

      <main className="max-w-6xl mx-auto px-4 pb-16">
        {/* Upload Section */}
        <div className="mt-8">
          <UploadSection
            onUpload={handleUpload}
            onProcessingStart={handleProcessingStart}
            onError={handleError}
            isProcessing={isProcessing}
          />
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-6 animate-fade-in" id="error-display">
            <div className="glass-card p-4 border-red-500/30 border">
              <div className="flex items-center gap-3">
                <span className="text-2xl">⚠️</span>
                <div>
                  <p className="text-red-400 font-medium">Terjadi Kesalahan</p>
                  <p className="text-dark-text-muted text-sm mt-1">{error}</p>
                </div>
              </div>
              <button
                onClick={handleReset}
                className="mt-3 text-sm text-accent-gold hover:text-accent-amber transition-colors"
                id="btn-reset-error"
              >
                Coba lagi →
              </button>
            </div>
          </div>
        )}

        {/* Processing Status */}
        {isProcessing && (
          <div className="mt-6">
            <ProcessingStatus stage={processingStage} />
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="mt-8 animate-fade-in">
            <ResultsPanel data={result} onReset={handleReset} />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-dark-border py-6 text-center">
        <p className="text-dark-text-muted text-xs">
          DeepLontar v1.0 — Powered by{' '}
          <span className="text-accent-teal">SeamFormer</span> &{' '}
          <span className="text-accent-teal">YOLOv8</span>
        </p>
      </footer>
    </div>
  );
}

export default App;
