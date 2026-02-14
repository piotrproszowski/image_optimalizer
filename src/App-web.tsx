import {
    FileImage,
    FolderOpen,
    Settings as SettingsIcon,
    UploadCloud,
    Zap,
    Download,
    CheckCircle,
} from 'lucide-react';
import { useState } from 'react';
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
    maxDimension: number | null;
}

interface JobStatus {
    id: string;
    total: number;
    processed: number;
    status: string;
    output_files: string[];
}

// API Base URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000';

function SettingsView({
    settings,
    setSettings,
}: {
    settings: AppSettings;
    setSettings: React.Dispatch<React.SetStateAction<AppSettings>>;
}) {
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

                {/* Max Dimension */}
                <div className='p-6 rounded-2xl bg-card/40 border border-white/5 space-y-4'>
                    <div className='flex justify-between items-center'>
                        <h3 className='text-lg font-semibold text-white'>
                            Max Dimension
                        </h3>
                        <span className='text-primary font-mono'>
                            {settings.maxDimension || 'No limit'}
                        </span>
                    </div>
                    <input
                        type='range'
                        min='512'
                        max='4096'
                        step='128'
                        value={settings.maxDimension || 2048}
                        onChange={(e) =>
                            setSettings((s) => ({
                                ...s,
                                maxDimension: parseInt(e.target.value),
                            }))
                        }
                        className='w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-primary'
                    />
                    <p className='text-xs text-muted-foreground'>
                        Maximum width or height in pixels.
                    </p>
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
    jobStatus,
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
                    ) : jobStatus?.status === 'completed' ? (
                        <CheckCircle size={48} className='text-green-500' />
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
                                ? `Processing... ${jobStatus?.processed || 0}/${jobStatus?.total || 0}`
                                : jobStatus?.status === 'completed'
                                  ? 'Processing Complete!'
                                  : 'Drop Images Here'}
                        </h3>
                        <p className='text-muted-foreground'>
                            Support for PNG, JPG, WebP, HEIC, AVIF
                        </p>
                    </div>

                    {!isProcessing && jobStatus?.status !== 'completed' && (
                        <div className='flex gap-3 justify-center'>
                            <button
                                onClick={onSelectFiles}
                                className='px-5 py-2.5 rounded-xl border bg-primary text-primary-foreground border-primary hover:bg-primary/80 transition-colors font-medium flex items-center gap-2'
                            >
                                <FileImage size={18} />
                                Select Files
                            </button>
                        </div>
                    )}

                    {jobStatus?.status === 'completed' && (
                        <button
                            onClick={() =>
                                window.open(
                                    `${API_BASE_URL}/api/download/${jobStatus.id}`,
                                    '_blank',
                                )
                            }
                            className='px-5 py-2.5 rounded-xl border bg-green-600 text-white border-green-600 hover:bg-green-700 transition-colors font-medium flex items-center gap-2 mx-auto'
                        >
                            <Download size={18} />
                            Download Results
                        </button>
                    )}
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
    const [isProcessing, setIsProcessing] = useState(false);
    const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);

    // App Settings
    const [settings, setSettings] = useState<AppSettings>({
        outputFormat: 'webp',
        quality: 77,
        stripMetadata: true,
        maxDimension: 2048,
    });

    // Poll job status
    const pollJobStatus = async (jobId: string) => {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/api/job/${jobId}`);
                const status = await response.json();
                setJobStatus(status);

                if (status.status === 'completed' || status.status === 'failed') {
                    clearInterval(interval);
                    setIsProcessing(false);
                }
            } catch (error) {
                console.error('Failed to poll job status:', error);
                clearInterval(interval);
                setIsProcessing(false);
            }
        }, 1000);
    };

    // Backend Invocation
    const processFiles = async (files: File[]) => {
        if (files.length === 0) return;

        setIsProcessing(true);
        setJobStatus(null);

        try {
            const formData = new FormData();
            
            // Add config
            const config = {
                outputFormat: settings.outputFormat,
                quality: settings.quality,
                stripMetadata: settings.stripMetadata,
                maxDimension: settings.maxDimension,
            };
            formData.append('config', JSON.stringify(config));

            // Add files
            files.forEach((file) => {
                formData.append('files', file);
            });

            const response = await fetch(`${API_BASE_URL}/api/process`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Processing failed');
            }

            const result = await response.json();
            pollJobStatus(result.job_id);
        } catch (error) {
            console.error('Processing failed:', error);
            alert(`Error processing images: ${error}`);
            setIsProcessing(false);
        }
    };

    // Drag & Drop
    const handleDragEnter = () => setIsHovering(true);
    const handleDragLeave = () => setIsHovering(false);
    const handleDropUI = (e: React.DragEvent) => {
        e.preventDefault();
        setIsHovering(false);
        
        const files = Array.from(e.dataTransfer.files).filter((file) =>
            file.type.startsWith('image/'),
        );
        
        if (files.length > 0) {
            processFiles(files);
        }
    };

    // File Dialog
    const selectFiles = () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.multiple = true;
        input.accept = 'image/*';
        input.onchange = (e: any) => {
            const files = Array.from(e.target.files || []) as File[];
            if (files.length > 0) {
                processFiles(files);
            }
        };
        input.click();
    };

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
                        jobStatus={jobStatus}
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
                        <div className='h-11 w-11 rounded-xl overflow-hidden shadow-lg shadow-primary/20 bg-primary/20 flex items-center justify-center'>
                            <Zap className='text-primary' size={24} />
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
