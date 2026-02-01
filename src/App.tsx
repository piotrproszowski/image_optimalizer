import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { open } from '@tauri-apps/plugin-dialog';
import {
    FileImage,
    FolderOpen,
    Settings as SettingsIcon,
    UploadCloud,
    Zap,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import './App.css';

// Types
interface ProcessingStats {
    images_count: number;
    size_saved_mb: number;
    efficiency_percentage: number;
}

interface AppSettings {
    outputFormat: 'original' | 'webp' | 'png' | 'jpg' | 'avif';
    quality: number;
    stripMetadata: boolean;
    outputDir: string | null;
}

function SettingsView({
    settings,
    setSettings,
}: {
    settings: AppSettings;
    setSettings: React.Dispatch<React.SetStateAction<AppSettings>>;
}) {
    const handleSelectDir = async () => {
        try {
            const { open } = await import('@tauri-apps/plugin-dialog');
            const selected = await open({
                directory: true,
                multiple: false,
            });
            if (selected && typeof selected === 'string') {
                setSettings((s) => ({ ...s, outputDir: selected }));
            }
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div className='space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20'>
            <div className='space-y-2'>
                <h2 className='text-2xl font-bold text-white'>
                    Conversion Settings
                </h2>
                <p className='text-muted-foreground'>
                    Configure how your images are processed.
                </p>
            </div>

            <div className='space-y-6'>
                {/* Format Selection */}
                <div className='p-6 rounded-2xl bg-card/40 border border-white/5 space-y-4'>
                    <h3 className='text-lg font-semibold text-white'>
                        Output Format
                    </h3>
                    <div className='grid grid-cols-2 md:grid-cols-4 gap-3'>
                        {['original', 'webp', 'png', 'jpg', 'avif'].map(
                            (fmt) => (
                                <button
                                    key={fmt}
                                    onClick={() =>
                                        setSettings((s) => ({
                                            ...s,
                                            outputFormat: fmt as any,
                                        }))
                                    }
                                    className={`
                                    px-4 py-3 rounded-xl border transition-all
                                    ${
                                        settings.outputFormat === fmt
                                            ? 'bg-primary text-primary-foreground border-primary'
                                            : 'bg-white/5 border-white/10 hover:bg-white/10 text-muted-foreground hover:text-white'
                                    }
                                `}
                                >
                                    {fmt.toUpperCase()}
                                </button>
                            ),
                        )}
                    </div>
                </div>

                {/* Quality Slider */}
                <div className='p-6 rounded-2xl bg-card/40 border border-white/5 space-y-4'>
                    <div className='flex justify-between items-center'>
                        <h3 className='text-lg font-semibold text-white'>
                            Quality
                        </h3>
                        <span className='text-primary font-mono'>
                            {settings.quality}%
                        </span>
                    </div>
                    <input
                        type='range'
                        min='1'
                        max='100'
                        value={settings.quality}
                        onChange={(e) =>
                            setSettings((s) => ({
                                ...s,
                                quality: parseInt(e.target.value),
                            }))
                        }
                        className='w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-primary'
                    />
                    <p className='text-xs text-muted-foreground'>
                        Lower quality results in smaller file sizes.
                    </p>
                </div>

                {/* Output Directory */}
                <div className='p-6 rounded-2xl bg-card/40 border border-white/5 space-y-4'>
                    <h3 className='text-lg font-semibold text-white'>
                        Output Directory
                    </h3>
                    <div className='flex flex-col gap-3'>
                        <div className='flex gap-3'>
                            <input
                                disabled
                                value={
                                    settings.outputDir ||
                                    'Same as original folder'
                                }
                                className='flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-muted-foreground text-sm'
                            />
                            <button
                                onClick={handleSelectDir}
                                className='px-4 py-2 bg-secondary text-secondary-foreground rounded-xl hover:bg-secondary/80 border border-white/10 transition-colors'
                            >
                                Browse...
                            </button>
                        </div>
                        {settings.outputDir && (
                            <button
                                onClick={() =>
                                    setSettings((s) => ({
                                        ...s,
                                        outputDir: null,
                                    }))
                                }
                                className='text-xs text-red-400 hover:text-red-300 self-start'
                            >
                                Reset to default
                            </button>
                        )}
                        <p className='text-xs text-muted-foreground'>
                            If empty, processed images use source folder.
                        </p>
                    </div>
                </div>

                {/* Metadata */}
                <div className='p-6 rounded-2xl bg-card/40 border border-white/5 flex items-center justify-between'>
                    <div>
                        <h3 className='text-lg font-semibold text-white'>
                            Strip Metadata
                        </h3>
                        <p className='text-sm text-muted-foreground'>
                            Remove EXIF, GPS, and other private data.
                        </p>
                    </div>
                    <button
                        onClick={() =>
                            setSettings((s) => ({
                                ...s,
                                stripMetadata: !s.stripMetadata,
                            }))
                        }
                        className={`w-12 h-7 rounded-full transition-colors relative ${settings.stripMetadata ? 'bg-primary' : 'bg-white/20'}`}
                    >
                        <div
                            className={`absolute top-1 left-1 w-5 h-5 bg-white rounded-full transition-transform ${settings.stripMetadata ? 'translate-x-5' : 'translate-x-0'}`}
                        />
                    </button>
                </div>
            </div>
        </div>
    );
}

function ProcessView({
    handleDrop,
    isHovering,
    isProcessing,
    handleDragEnter,
    handleDragLeave,
    onSelectFiles,
    onSelectFolder,
    selectedMode,
}: any) {
    return (
        <div className='h-full flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-500'>
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
                onDragOver={(e) => {
                    e.preventDefault();
                    handleDragEnter();
                }}
                onDragLeave={handleDragLeave}
                onDrop={(e) => {
                    e.preventDefault();
                    handleDrop(e);
                }}
            >
                {/* Background Pattern */}
                <div className='absolute inset-0 opacity-20 pointer-events-none bg-[radial-gradient(#ffffff1a_1px,transparent_1px)] [background-size:16px_16px]' />

                <div
                    className={`p-8 rounded-full bg-card/50 border border-white/10 shadow-2xl transition-transform duration-500 z-10 ${isHovering || isProcessing ? 'scale-110' : 'group-hover:scale-105'}`}
                >
                    {isProcessing ? (
                        <div className='animate-spin text-primary'>
                            <Zap size={48} />
                        </div>
                    ) : (
                        <UploadCloud
                            size={48}
                            className={`text-primary transition-all duration-500 ${isHovering ? 'animate-bounce' : ''}`}
                        />
                    )}
                </div>

                <div className='text-center space-y-4 z-10'>
                    <div>
                        <h3 className='text-2xl font-bold text-white mb-2'>
                            {isProcessing
                                ? 'Optimizing...'
                                : 'Drop Images or Folders Here'}
                        </h3>
                        <p className='text-muted-foreground'>
                            Support for PNG, JPG, WebP, HEIC, AVIF
                        </p>
                    </div>

                    <div className='flex gap-3 justify-center'>
                        <button
                            onClick={onSelectFiles}
                            className={`px-5 py-2.5 rounded-xl border transition-colors font-medium flex items-center gap-2 ${
                                selectedMode === 'files'
                                    ? 'bg-primary text-primary-foreground border-primary'
                                    : 'bg-primary/80 hover:bg-primary text-primary-foreground border-primary/80'
                            }`}
                        >
                            <FileImage size={18} />
                            Select Files
                        </button>
                        <button
                            onClick={onSelectFolder}
                            className={`px-5 py-2.5 rounded-xl border transition-colors font-medium flex items-center gap-2 ${
                                selectedMode === 'folder'
                                    ? 'bg-primary text-primary-foreground border-primary'
                                    : 'bg-primary/80 hover:bg-primary text-primary-foreground border-primary/80'
                            }`}
                        >
                            <FolderOpen size={18} />
                            Select Folder
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

function App() {
    const [activeTab, setActiveTab] = useState<'process' | 'settings'>(
        'process',
    );
    const [isHovering, setIsHovering] = useState(false);
    const [selectedMode, setSelectedMode] = useState<'files' | 'folder' | null>(
        null,
    );
    const [isProcessing, setIsProcessing] = useState(false);

    // App Settings
    const [settings, setSettings] = useState<AppSettings>({
        outputFormat: 'webp',
        quality: 77,
        stripMetadata: true,
        outputDir: null,
    });

    // Backend Invocation
    const processFiles = async (paths: string[]) => {
        if (paths.length === 0) return;

        setIsProcessing(true);
        try {
            // We pass settings as a separate argument or part of a config object
            // For now, I'll pass fields to match the rust command signature I'm about to update
            const result = await invoke<ProcessingStats>('process_images', {
                files: paths,
                config: settings, // We will update Rust to accept this
            });

            void result;
        } catch (error) {
            console.error('Processing failed:', error);
            alert(`Error processing images: ${error}`);
        } finally {
            setIsProcessing(false);
            setIsHovering(false);
        }
    };

    // --- Listeners & Handlers ---

    // Drag & Drop
    const handleDragEnter = () => setIsHovering(true);
    const handleDragLeave = () => setIsHovering(false);
    // Drop UI handler just catches the DOM event logic
    const handleDropUI = (e: React.DragEvent) => {
        e.preventDefault();
        setIsHovering(false);
        // NOTE: We rely on tauri://drop listener because it provides absolute paths better in some contexts,
        // BUT for folders, sometimes the web file item is restricted.
        // Let's rely on the global listener below.
    };

    // File/Folder Dialog
    const manualSelect = async (directory: boolean = false) => {
        try {
            const selected = await open({
                multiple: true,
                directory: directory,
                filters: !directory
                    ? [
                          {
                              name: 'Images',
                              extensions: [
                                  'png',
                                  'jpg',
                                  'jpeg',
                                  'webp',
                                  'heic',
                                  'avif',
                              ],
                          },
                      ]
                    : undefined,
            });

            if (selected) {
                const paths = Array.isArray(selected) ? selected : [selected];
                processFiles(paths);
            }
        } catch (e) {
            console.error('Dialog error:', e);
        }
    };

    const selectFiles = () => {
        setSelectedMode('files');
        manualSelect(false);
    };

    const selectFolder = () => {
        setSelectedMode('folder');
        manualSelect(true);
    };

    // System Drop Listener
    useEffect(() => {
        // Helper to process payload
        const handleDropEvent = (event: any) => {
            let paths: string[] = [];
            // V2 Structure vs V1 Structure
            if (Array.isArray(event.payload)) {
                paths = event.payload;
            } else if (
                event.payload?.paths &&
                Array.isArray(event.payload.paths)
            ) {
                paths = event.payload.paths;
            }

            if (paths.length > 0) {
                setActiveTab('process');
                processFiles(paths);
            }
        };

        // Listen to all potential event names for maximum compatibility
        const unlisteners: Promise<() => void>[] = [];

        unlisteners.push(listen('tauri://drop', handleDropEvent));
        unlisteners.push(listen('tauri://file-drop', handleDropEvent)); // V1 legacy
        unlisteners.push(listen('tauri://drag-drop', handleDropEvent)); // Potential V2 alias

        // Debug Drag Enter
        unlisteners.push(
            listen('tauri://drag-enter', () => {
                setIsHovering(true);
            }),
        );
        unlisteners.push(
            listen('tauri://drag-leave', () => {
                setIsHovering(false);
            }),
        );

        return () => {
            unlisteners.forEach((p) => p.then((f) => f()));
        };
    }, [settings]);

    // View Routing
    const renderContent = () => {
        switch (activeTab) {
            case 'settings':
                return (
                    <SettingsView
                        settings={settings}
                        setSettings={setSettings}
                    />
                );
            case 'process':
                return (
                    <ProcessView
                        handleDrop={handleDropUI}
                        isHovering={isHovering}
                        isProcessing={isProcessing}
                        handleDragEnter={handleDragEnter}
                        handleDragLeave={handleDragLeave}
                        onSelectFiles={selectFiles}
                        onSelectFolder={selectFolder}
                        selectedMode={selectedMode}
                    />
                );
            default:
                return null;
        }
    };

    return (
        <div className='flex h-screen bg-background text-foreground overflow-hidden font-sans selection:bg-primary/30'>
            <main className='flex-1 flex flex-col relative overflow-hidden bg-gradient-to-br from-background to-background/50'>
                {/* Glow Effects */}
                <div className='absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-primary/10 rounded-full blur-[128px] pointer-events-none mix-blend-screen' />
                <div className='absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[128px] pointer-events-none mix-blend-screen' />

                {/* Header */}
                <header className='px-8 py-6 z-10 flex items-center justify-between border-b border-white/5 bg-background/50 backdrop-blur-sm'>
                    <div className='flex items-center gap-4'>
                        <div className='h-11 w-11 rounded-xl overflow-hidden shadow-lg shadow-primary/20'>
                            <img
                                src='/icons/128x128.png'
                                alt='Image Processor'
                                className='h-full w-full object-contain'
                            />
                        </div>
                        <div>
                            <h1 className='text-2xl font-bold text-white tracking-tight'>
                                Image Processor
                            </h1>
                            <p className='text-muted-foreground mt-1'>
                                {activeTab === 'settings'
                                    ? 'Configure application'
                                    : 'Optimize your assets'}
                            </p>
                        </div>
                    </div>
                    <div className='flex items-center gap-2'>
                        <button
                            onClick={() => setActiveTab('process')}
                            className={`px-4 py-2 rounded-xl border transition-all flex items-center gap-2 select-none ${
                                activeTab === 'process'
                                    ? 'bg-primary text-primary-foreground border-primary'
                                    : 'bg-white/5 border-white/10 hover:bg-white/10 text-muted-foreground hover:text-white'
                            }`}
                        >
                            <FileImage size={18} />
                            Process
                        </button>
                        <button
                            onClick={() => setActiveTab('settings')}
                            className={`px-4 py-2 rounded-xl border transition-all flex items-center gap-2 select-none ${
                                activeTab === 'settings'
                                    ? 'bg-primary text-primary-foreground border-primary'
                                    : 'bg-white/5 border-white/10 hover:bg-white/10 text-muted-foreground hover:text-white'
                            }`}
                        >
                            <SettingsIcon size={18} />
                            Settings
                        </button>
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

export default App;
