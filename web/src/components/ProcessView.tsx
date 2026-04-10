import { FileImage, FolderOpen, UploadCloud, Zap } from 'lucide-react';
import { useRef } from 'react';
import type { ProcessingProgress } from '../types';

const ACCEPTED_IMAGE_TYPES = '.jpg,.jpeg,.png,.webp,.avif';

interface ProcessViewProps {
  isProcessing: boolean;
  progress: ProcessingProgress | null;
  onFilesSelected: (files: File[]) => void;
}

function extractFilesFromDataTransfer(dataTransfer: DataTransfer): File[] {
  const files: File[] = [];
  for (let i = 0; i < dataTransfer.files.length; i++) {
    const file = dataTransfer.files[i];
    if (file.type.startsWith('image/')) {
      files.push(file);
    }
  }
  return files;
}

function extractFilesFromInput(input: HTMLInputElement): File[] {
  if (!input.files) return [];
  return Array.from(input.files);
}

export function ProcessView({
  isProcessing,
  progress,
  onFilesSelected,
}: ProcessViewProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = extractFilesFromDataTransfer(e.dataTransfer);
    if (files.length > 0) {
      onFilesSelected(files);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = extractFilesFromInput(e.target);
    if (files.length > 0) {
      onFilesSelected(files);
    }
    e.target.value = '';
  };

  const selectFiles = () => fileInputRef.current?.click();
  const selectFolder = () => folderInputRef.current?.click();

  const isHovering = false;

  return (
    <div className='h-full flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-500'>
      {/* Hidden file inputs */}
      <input
        ref={fileInputRef}
        type='file'
        accept={ACCEPTED_IMAGE_TYPES}
        multiple
        className='hidden'
        onChange={handleFileInputChange}
      />
      <input
        ref={folderInputRef}
        type='file'
        // @ts-expect-error webkitdirectory is not in React types
        webkitdirectory=''
        multiple
        className='hidden'
        onChange={handleFileInputChange}
      />

      <div
        className={`
          flex-1 rounded-3xl border-2 border-dashed transition-all duration-300
          flex flex-col items-center justify-center gap-6 group relative overflow-hidden
          ${
            isHovering
              ? 'border-primary bg-primary/10 scale-[0.99]'
              : 'border-white/10 bg-card/20 hover:border-white/20 hover:bg-card/30'
          }
        `}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
      >
        {/* Background Pattern */}
        <div className='absolute inset-0 opacity-20 pointer-events-none bg-[radial-gradient(#ffffff1a_1px,transparent_1px)] [background-size:16px_16px]' />

        <div
          className={`p-8 rounded-full bg-card/50 border border-white/10 shadow-2xl transition-transform duration-500 z-10 ${isProcessing ? 'scale-110' : 'group-hover:scale-105'}`}
        >
          {isProcessing ? (
            <div className='animate-spin text-primary'>
              <Zap size={48} />
            </div>
          ) : (
            <UploadCloud
              size={48}
              className='text-primary transition-all duration-500'
            />
          )}
        </div>

        <div className='text-center space-y-4 z-10'>
          <div>
            <h3 className='text-2xl font-bold text-white mb-2'>
              {isProcessing ? 'Optimizing...' : 'Drop Images or Folders Here'}
            </h3>
            {isProcessing && progress ? (
              <div className='space-y-2'>
                <p className='text-muted-foreground'>
                  {progress.current} / {progress.total} — {progress.lastFile}
                </p>
                <div className='w-64 mx-auto h-2 bg-white/10 rounded-full overflow-hidden'>
                  <div
                    className='h-full bg-primary rounded-full transition-all duration-300'
                    style={{
                      width: `${(progress.current / progress.total) * 100}%`,
                    }}
                  />
                </div>
              </div>
            ) : (
              <p className='text-muted-foreground'>
                Support for PNG, JPG, WebP, AVIF
              </p>
            )}
          </div>

          {!isProcessing && (
            <div className='flex gap-3 justify-center'>
              <button
                onClick={selectFiles}
                className='px-5 py-2.5 rounded-xl border transition-colors font-medium flex items-center gap-2 bg-primary/80 hover:bg-primary text-primary-foreground border-primary/80'
              >
                <FileImage size={18} />
                Select Files
              </button>
              <button
                onClick={selectFolder}
                className='px-5 py-2.5 rounded-xl border transition-colors font-medium flex items-center gap-2 bg-primary/80 hover:bg-primary text-primary-foreground border-primary/80'
              >
                <FolderOpen size={18} />
                Select Folder
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
