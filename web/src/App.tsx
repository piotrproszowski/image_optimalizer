import JSZip from 'jszip';
import { FileImage, Package, Settings as SettingsIcon } from 'lucide-react';
import { useCallback, useState } from 'react';
import { ProcessView } from './components/ProcessView';
import { ResultsView } from './components/ResultsView';
import { SettingsView } from './components/SettingsView';
import { processImages, revokeProcessedUrls } from './lib/image-processor';
import type {
  ActiveTab,
  AppSettings,
  ProcessedImage,
  ProcessingProgress,
} from './types';

function downloadBlob(blob: Blob, fileName: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

const DEFAULT_SETTINGS: AppSettings = {
  outputFormat: 'webp',
  quality: 77,
  maxDimension: 2048,
  stripMetadata: true,
};

export default function App() {
  const [activeTab, setActiveTab] = useState<ActiveTab>('process');
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState<ProcessingProgress | null>(null);
  const [results, setResults] = useState<ProcessedImage[]>([]);
  const [settings, setSettings] = useState<AppSettings>(DEFAULT_SETTINGS);

  const handleFilesSelected = useCallback(
    async (files: File[]) => {
      if (files.length === 0) return;

      setIsProcessing(true);
      setProgress({ current: 0, total: files.length, lastFile: '' });

      try {
        const processed = await processImages(
          files,
          settings,
          (current, total, lastFile) => {
            setProgress({ current, total, lastFile });
          },
        );

        setResults((prev) => [...prev, ...processed]);
        setActiveTab('results');
      } catch (error) {
        console.error('Processing failed:', error);
      } finally {
        setIsProcessing(false);
        setProgress(null);
      }
    },
    [settings],
  );

  const handleClearResults = useCallback(() => {
    revokeProcessedUrls(results);
    setResults([]);
  }, [results]);

  const handleDownloadAll = useCallback(async () => {
    if (results.length === 0) return;

    const zip = new JSZip();
    for (const image of results) {
      zip.file(image.fileName, image.processedBlob);
    }

    const blob = await zip.generateAsync({ type: 'blob' });
    downloadBlob(blob, 'optimized_images.zip');
  }, [results]);

  const renderContent = () => {
    switch (activeTab) {
      case 'settings':
        return <SettingsView settings={settings} setSettings={setSettings} />;
      case 'results':
        return (
          <ResultsView
            results={results}
            onClearResults={handleClearResults}
            onDownloadAll={handleDownloadAll}
          />
        );
      case 'process':
      default:
        return (
          <ProcessView
            isProcessing={isProcessing}
            progress={progress}
            onFilesSelected={handleFilesSelected}
          />
        );
    }
  };

  const tabs = [
    { id: 'process' as const, label: 'Process', icon: FileImage },
    {
      id: 'results' as const,
      label: `Results${results.length > 0 ? ` (${results.length})` : ''}`,
      icon: Package,
    },
    { id: 'settings' as const, label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <div className='flex h-screen bg-background text-foreground overflow-hidden font-sans selection:bg-primary/30'>
      <main className='flex-1 flex flex-col relative overflow-hidden bg-gradient-to-br from-background to-background/50'>
        {/* Glow Effects */}
        <div className='absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-primary/10 rounded-full blur-[128px] pointer-events-none mix-blend-screen' />
        <div className='absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[128px] pointer-events-none mix-blend-screen' />

        {/* Header */}
        <header className='px-8 py-6 z-10 flex items-center justify-between border-b border-white/5 bg-background/50 backdrop-blur-sm'>
          <div className='flex items-center gap-4'>
            <div className='h-11 w-11 rounded-xl overflow-hidden shadow-lg shadow-primary/20 bg-primary/10 flex items-center justify-center'>
              <FileImage size={24} className='text-primary' />
            </div>
            <div>
              <h1 className='text-2xl font-bold text-white tracking-tight'>
                Image Optimizer
              </h1>
              <p className='text-muted-foreground mt-1'>
                {activeTab === 'settings'
                  ? 'Configure application'
                  : activeTab === 'results'
                    ? 'Processed images'
                    : 'Optimize your assets'}
              </p>
            </div>
          </div>

          <div className='flex items-center gap-2'>
            {tabs.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`px-4 py-2 rounded-xl border transition-all flex items-center gap-2 select-none ${
                  activeTab === id
                    ? 'bg-primary text-primary-foreground border-primary'
                    : 'bg-white/5 border-white/10 hover:bg-white/10 text-muted-foreground hover:text-white'
                }`}
              >
                <Icon size={18} />
                {label}
              </button>
            ))}
          </div>
        </header>

        {/* View container */}
        <div className='flex-1 px-8 py-8 z-10 overflow-y-auto custom-scrollbar'>
          {renderContent()}
        </div>
      </main>
    </div>
  );
}
