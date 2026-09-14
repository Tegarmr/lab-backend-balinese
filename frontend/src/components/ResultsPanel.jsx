import ImageDisplay from './ImageDisplay';
import CollapsibleStep from './CollapsibleStep';
import BinaryMapView from './BinaryMapView';
import ScribbleMapView from './ScribbleMapView';
import SegmentedLinesView from './SegmentedLinesView';
import YoloDetectionView from './YoloDetectionView';
import PositionsView from './PositionsView';
import GroupedPositionsView from './GroupedPositionsView';
import SyllableGroupsView from './SyllableGroupsView';
import TransliterationView from './TransliterationView';

/**
 * Main results panel that shows all processing steps.
 * - Input image (always visible)
 * - Steps 2-7 (collapsible)
 * - Transliteration (always visible)
 */
export default function ResultsPanel({ data, onReset }) {
  if (!data) return null;

  const totalChars = data.total_characters || 0;
  const totalLines = data.total_lines || 0;

  return (
    <div id="results-panel">
      {/* Stats bar */}
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-accent-teal text-sm font-medium">✓ Selesai</span>
            <span className="text-dark-text-muted text-xs">
              {data.processing_time?.toFixed(1)}s
            </span>
          </div>
          <div className="flex gap-3">
            <span className="detection-badge">{totalLines} baris</span>
            <span className="detection-badge">{totalChars} karakter</span>
          </div>
        </div>
        <button
          onClick={onReset}
          className="text-sm text-accent-gold hover:text-accent-amber transition-colors flex items-center gap-1"
          id="btn-new-upload"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          Upload baru
        </button>
      </div>

      <div className="space-y-4">
        {/* 1. Input Image — always visible */}
        <ImageDisplay base64Image={data.input_image} />

        {/* 2. Binary Map — collapsible */}
        <CollapsibleStep
          title="Binary Map"
          icon="🔲"
          stepNumber={2}
          badge="Stage 1"
        >
          <BinaryMapView base64Image={data.binary_map} />
        </CollapsibleStep>

        {/* 3. Scribble Map — collapsible */}
        <CollapsibleStep
          title="Scribble Map"
          icon="〰️"
          stepNumber={3}
          badge="Stage 1"
        >
          <ScribbleMapView base64Image={data.scribble_map} />
        </CollapsibleStep>

        {/* 4. Segmented Lines — collapsible */}
        <CollapsibleStep
          title="Hasil Segmentasi"
          icon="✂️"
          stepNumber={4}
          badge={`${totalLines} baris`}
        >
          <SegmentedLinesView
            segmentationImage={data.segmentation_image}
            segmentedLines={data.segmented_lines}
          />
        </CollapsibleStep>

        {/* 5. YOLO Detection — collapsible */}
        <CollapsibleStep
          title="Deteksi YOLO per Baris"
          icon="🔍"
          stepNumber={5}
          badge={`${totalChars} karakter`}
        >
          <YoloDetectionView lines={data.lines} />
        </CollapsibleStep>

        {/* 6. Positions — collapsible */}
        <CollapsibleStep
          title="Posisi Karakter (x, y)"
          icon="📐"
          stepNumber={6}
        >
          <PositionsView lines={data.lines} />
        </CollapsibleStep>

        {/* 7. Grouped Positions — collapsible */}
        <CollapsibleStep
          title="Posisi Terkelompok"
          icon="🔗"
          stepNumber={7}
        >
          <GroupedPositionsView lines={data.lines} />
        </CollapsibleStep>

        {/* 8. Syllable grouping — collapsible (verifikasi aturan) */}
        <CollapsibleStep
          title="Pembentukan Suku Kata & Aturan"
          icon="🔤"
          stepNumber={8}
          badge="verifikasi rule"
          defaultOpen
        >
          <SyllableGroupsView lines={data.lines} />
        </CollapsibleStep>

        {/* 9. Transliteration — always visible */}
        <TransliterationView
          lines={data.lines}
          fullTransliteration={data.full_transliteration}
        />
      </div>
    </div>
  );
}
