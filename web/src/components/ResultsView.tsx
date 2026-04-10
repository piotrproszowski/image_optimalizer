import { ArrowDown, Download, Package, Trash2 } from 'lucide-react';
import { formatFileSize } from '../lib/image-processor';
import type { ProcessedImage } from '../types';

interface ResultsViewProps {
  results: ProcessedImage[];
  onClearResults: () => void;
  onDownloadAll: () => void;
}

function SavingsIndicator({
  originalSize,
  processedSize,
}: {
  originalSize: number;
  processedSize: number;
}) {
  const savedBytes = originalSize - processedSize;
  const savedPercent = ((savedBytes / originalSize) * 100).toFixed(1);
  const isSmaller = savedBytes > 0;

  return (
    <span
      className={`text-xs font-mono ${isSmaller ? 'text-green-400' : 'text-red-400'}`}
    >
      {isSmaller ? `−${savedPercent}%` : `+${Math.abs(Number(savedPercent))}%`}
    </span>
  );
}

function ResultCard({ image }: { image: ProcessedImage }) {
  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = image.previewUrl;
    link.download = image.fileName;
    link.click();
  };

  return (
    <div className='p-4 rounded-2xl bg-card/40 border border-white/5 flex items-center gap-4 hover:bg-card/60 transition-colors'>
      <img
        src={image.previewUrl}
        alt={image.fileName}
        className='w-16 h-16 rounded-xl object-cover border border-white/10'
      />

      <div className='flex-1 min-w-0'>
        <p className='text-sm font-medium text-white truncate'>
          {image.fileName}
        </p>
        <div className='flex items-center gap-2 mt-1'>
          <span className='text-xs text-muted-foreground'>
            {formatFileSize(image.originalSize)}
          </span>
          <ArrowDown size={12} className='text-muted-foreground' />
          <span className='text-xs text-white font-medium'>
            {formatFileSize(image.processedSize)}
          </span>
          <SavingsIndicator
            originalSize={image.originalSize}
            processedSize={image.processedSize}
          />
        </div>
        <p className='text-xs text-muted-foreground mt-0.5 uppercase'>
          {image.outputFormat}
        </p>
      </div>

      <button
        onClick={handleDownload}
        className='p-2 rounded-xl bg-primary/20 hover:bg-primary/40 text-primary transition-colors'
        title='Download'
      >
        <Download size={18} />
      </button>
    </div>
  );
}

export function ResultsView({
  results,
  onClearResults,
  onDownloadAll,
}: ResultsViewProps) {
  if (results.length === 0) {
    return (
      <div className='h-full flex items-center justify-center animate-in fade-in duration-500'>
        <div className='text-center space-y-4'>
          <Package size={48} className='mx-auto text-muted-foreground/50' />
          <p className='text-muted-foreground'>
            No results yet. Process some images first.
          </p>
        </div>
      </div>
    );
  }

  const totalOriginal = results.reduce((sum, r) => sum + r.originalSize, 0);
  const totalProcessed = results.reduce((sum, r) => sum + r.processedSize, 0);
  const totalSaved = totalOriginal - totalProcessed;

  return (
    <div className='space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20'>
      {/* Summary Bar */}
      <div className='p-5 rounded-2xl bg-card/40 border border-white/5 flex flex-wrap items-center justify-between gap-4'>
        <div className='flex items-center gap-6'>
          <div>
            <p className='text-xs text-muted-foreground'>Images</p>
            <p className='text-lg font-bold text-white'>{results.length}</p>
          </div>
          <div>
            <p className='text-xs text-muted-foreground'>Total Saved</p>
            <p className='text-lg font-bold text-green-400'>
              {totalSaved > 0 ? formatFileSize(totalSaved) : '—'}
            </p>
          </div>
          <div>
            <p className='text-xs text-muted-foreground'>Reduction</p>
            <p className='text-lg font-bold text-green-400'>
              {totalSaved > 0
                ? `${((totalSaved / totalOriginal) * 100).toFixed(1)}%`
                : '—'}
            </p>
          </div>
        </div>

        <div className='flex gap-2'>
          <button
            onClick={onDownloadAll}
            className='px-4 py-2 rounded-xl bg-primary text-primary-foreground font-medium flex items-center gap-2 hover:bg-primary/90 transition-colors'
          >
            <Download size={16} />
            Download All (ZIP)
          </button>
          <button
            onClick={onClearResults}
            className='px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-muted-foreground hover:text-white hover:bg-white/10 transition-colors flex items-center gap-2'
          >
            <Trash2 size={16} />
            Clear
          </button>
        </div>
      </div>

      {/* Results List */}
      <div className='space-y-3'>
        {results.map((image) => (
          <ResultCard key={image.id} image={image} />
        ))}
      </div>
    </div>
  );
}
