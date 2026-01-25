import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import { open } from '@tauri-apps/plugin-dialog'
import {
  FileImage,
  FolderOpen,
  LayoutDashboard,
  Settings as SettingsIcon,
  UploadCloud,
  Zap
} from 'lucide-react'
import { useEffect, useState } from 'react'
import './App.css'

// Types
interface ProcessingStats {
  images_count: number
  size_saved_mb: number
  efficiency_percentage: number
}

interface AppSettings {
    outputFormat: 'original' | 'webp' | 'png' | 'jpg';
    quality: number;
    stripMetadata: boolean;
    outputDir: string | null;
}

// Components
function NavButton({ active, onClick, icon, label }: { active: boolean, onClick: () => void, icon: React.ReactNode, label: string }) {
    return (
        <button 
            onClick={onClick}
            className={`
                w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 group
                ${active 
                    ? 'bg-primary/10 text-primary shadow-inner shadow-primary/5' 
                    : 'text-muted-foreground hover:bg-white/5 hover:text-white'
                }
            `}
        >
            <span className={`${active ? 'text-primary' : 'text-current'}`}>{icon}</span>
            <span className="font-medium hidden lg:block">{label}</span>
            {active && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-primary shadow shadow-primary/50 hidden lg:block" />}
        </button>
    )
}

function StatCard({ label, value, trend, icon }: { label: string, value: string, trend: string, icon: React.ReactNode }) {
    return (
        <div className="p-6 rounded-2xl bg-card/40 border border-white/5 backdrop-blur-sm shadow-xl flex items-start justify-between group hover:bg-card/50 transition-colors">
            <div>
                <p className="text-sm font-medium text-muted-foreground mb-1">{label}</p>
                <h4 className="text-3xl font-bold text-white tracking-tight">{value}</h4>
                <div className="flex items-center gap-2 mt-2">
                    <span className="text-xs font-semibold text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded-full">{trend}</span>
                    <span className="text-xs text-muted-foreground">vs last session</span>
                </div>
            </div>
            <div className="p-3 rounded-xl bg-white/5 border border-white/5 group-hover:scale-110 transition-transform">
                {icon}
            </div>
        </div>
    )
}

function SettingsView({ settings, setSettings }: { settings: AppSettings, setSettings: React.Dispatch<React.SetStateAction<AppSettings>> }) {
    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="space-y-2">
                <h2 className="text-2xl font-bold text-white">Conversion Settings</h2>
                <p className="text-muted-foreground">Configure how your images are processed.</p>
            </div>

            <div className="space-y-6">
                {/* Format Selection */}
                <div className="p-6 rounded-2xl bg-card/40 border border-white/5 space-y-4">
                    <h3 className="text-lg font-semibold text-white">Output Format</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {['original', 'webp', 'png', 'jpg'].map((fmt) => (
                            <button
                                key={fmt}
                                onClick={() => setSettings(s => ({ ...s, outputFormat: fmt as any }))}
                                className={`
                                    px-4 py-3 rounded-xl border transition-all
                                    ${settings.outputFormat === fmt 
                                        ? 'bg-primary text-primary-foreground border-primary' 
                                        : 'bg-white/5 border-white/10 hover:bg-white/10 text-muted-foreground hover:text-white'}
                                `}
                            >
                                {fmt.toUpperCase()}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Quality Slider */}
                <div className="p-6 rounded-2xl bg-card/40 border border-white/5 space-y-4">
                    <div className="flex justify-between items-center">
                        <h3 className="text-lg font-semibold text-white">Quality</h3>
                        <span className="text-primary font-mono">{settings.quality}%</span>
                    </div>
                    <input 
                        type="range" 
                        min="1" 
                        max="100" 
                        value={settings.quality} 
                        onChange={(e) => setSettings(s => ({ ...s, quality: parseInt(e.target.value) }))}
                        className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-primary"
                    />
                    <p className="text-xs text-muted-foreground">Lower quality results in smaller file sizes.</p>
                </div>

                {/* Metadata */}
                <div className="p-6 rounded-2xl bg-card/40 border border-white/5 flex items-center justify-between">
                    <div>
                        <h3 className="text-lg font-semibold text-white">Strip Metadata</h3>
                        <p className="text-sm text-muted-foreground">Remove EXIF, GPS, and other private data.</p>
                    </div>
                    <button 
                        onClick={() => setSettings(s => ({ ...s, stripMetadata: !s.stripMetadata }))}
                        className={`w-12 h-7 rounded-full transition-colors relative ${settings.stripMetadata ? 'bg-primary' : 'bg-white/20'}`}
                    >
                        <div className={`absolute top-1 left-1 w-5 h-5 bg-white rounded-full transition-transform ${settings.stripMetadata ? 'translate-x-5' : 'translate-x-0'}`} />
                    </button>
                </div>
            </div>
        </div>
    )
}

function DashboardView({ 
    stats, 
    handleDrop, 
    isHovering, 
    isProcessing, 
    handleDragEnter, 
    handleDragLeave,
    manualSelect
}: any) {
    return (
        <div className="flex flex-col gap-6 h-full">
            {/* Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 shrink-0">
                <StatCard 
                    label="Images Processed" 
                    value={stats.images_count.toString()} 
                    trend="+12%" 
                    icon={<FileImage className="text-primary" />}
                />
                <StatCard 
                    label="Space Saved" 
                    value={`${stats.size_saved_mb.toFixed(1)} MB`} 
                    trend="+5%" 
                    icon={<UploadCloud className="text-blue-400" />}
                />
                <StatCard 
                    label="Efficiency" 
                    value={`${stats.efficiency_percentage.toFixed(0)}%`} 
                    trend="High" 
                    icon={<Zap className="text-yellow-400" />}
                />
            </div>

            {/* Drop Zone */}
            <div 
                className={`
                    flex-1 rounded-3xl border-2 border-dashed transition-all duration-300
                    flex flex-col items-center justify-center gap-6 group relative overflow-hidden
                    ${isHovering 
                        ? 'border-primary bg-primary/10 scale-[0.99]' 
                        : 'border-white/10 bg-card/20 hover:border-white/20 hover:bg-card/30'
                    }
                `}
                onDragOver={(e) => { e.preventDefault(); handleDragEnter(); }}
                onDragLeave={handleDragLeave}
                onDrop={(e) => { e.preventDefault(); handleDrop(e); }}
            >
                {/* Background Pattern */}
                <div className="absolute inset-0 opacity-20 pointer-events-none bg-[radial-gradient(#ffffff1a_1px,transparent_1px)] [background-size:16px_16px]" />

                <div className={`p-8 rounded-full bg-card/50 border border-white/10 shadow-2xl transition-transform duration-500 z-10 ${isHovering || isProcessing ? 'scale-110' : 'group-hover:scale-105'}`}>
                    {isProcessing ? (
                         <div className="animate-spin text-primary"><Zap size={48} /></div>
                    ) : (
                        <UploadCloud size={48} className={`text-primary transition-all duration-500 ${isHovering ? 'animate-bounce' : ''}`} />
                    )}
                </div>
                
                <div className="text-center space-y-4 z-10">
                    <div>
                        <h3 className="text-2xl font-bold text-white mb-2">
                            {isProcessing ? 'Optimizing...' : 'Drop Images or Folders Here'}
                        </h3>
                        <p className="text-muted-foreground">
                            Support for PNG, JPG, WebP, HEIC
                        </p>
                    </div>

                    <div className="flex gap-3 justify-center">
                        <button 
                            onClick={() => manualSelect(false)}
                            className="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground font-medium transition-colors flex items-center gap-2 shadow-lg shadow-primary/20"
                        >
                            <FileImage size={18} />
                            Select Files
                        </button>
                         <button 
                            onClick={() => manualSelect(true)}
                            className="px-5 py-2.5 rounded-xl bg-secondary/80 hover:bg-secondary text-secondary-foreground font-medium transition-colors flex items-center gap-2 border border-white/10"
                        >
                            <FolderOpen size={18} />
                            Select Folder
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}

function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'process' | 'history' | 'settings'>('dashboard')
  const [isHovering, setIsHovering] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [stats, setStats] = useState<ProcessingStats>({
    images_count: 0,
    size_saved_mb: 0,
    efficiency_percentage: 0
  })
  
  // App Settings
  const [settings, setSettings] = useState<AppSettings>({
      outputFormat: 'original',
      quality: 85,
      stripMetadata: true,
      outputDir: null
  })

  // Backend Invocation
  const processFiles = async (paths: string[]) => {
      if (paths.length === 0) return;
      
      setIsProcessing(true);
      try {

          // We pass settings as a separate argument or part of a config object
          // For now, I'll pass fields to match the rust command signature I'm about to update
          const result = await invoke<ProcessingStats>('process_images', { 
              files: paths,
              config: settings // We will update Rust to accept this
          });
          
          setStats(prev => ({
              images_count: prev.images_count + result.images_count,
              size_saved_mb: prev.size_saved_mb + result.size_saved_mb,
              // Rolling average for efficiency or just set
              efficiency_percentage: result.efficiency_percentage 
          }));
          


          
      } catch (error) {
          console.error("Processing failed:", error);
          alert(`Error processing images: ${error}`);
      } finally {
          setIsProcessing(false);
          setIsHovering(false);
      }
  }

  // --- Listeners & Handlers ---

  // Drag & Drop
  const handleDragEnter = () => setIsHovering(true)
  const handleDragLeave = () => setIsHovering(false)
  // Drop UI handler just catches the DOM event logic
  const handleDropUI = (e: React.DragEvent) => {
      e.preventDefault();
      setIsHovering(false);
      // NOTE: We rely on tauri://drop listener because it provides absolute paths better in some contexts,
      // BUT for folders, sometimes the web file item is restricted.
      // Let's rely on the global listener below.
  }

  // File/Folder Dialog
  const manualSelect = async (directory: boolean = false) => {
      try {
          const selected = await open({
              multiple: true,
              directory: directory,
              filters: !directory ? [{
                  name: 'Images',
                  extensions: ['png', 'jpg', 'jpeg', 'webp', 'heic']
              }] : undefined
          });

          if (selected) {
              const paths = Array.isArray(selected) ? selected : [selected];
              processFiles(paths);
          }
      } catch (e) {
          console.error("Dialog error:", e);
      }
  }

  // System Drop Listener
  useEffect(() => {
    // Helper to process payload
    const handleDropEvent = (event: any) => {

        let paths: string[] = [];
        // V2 Structure vs V1 Structure
        if (Array.isArray(event.payload)) {
             paths = event.payload;
        } else if (event.payload?.paths && Array.isArray(event.payload.paths)) {
             paths = event.payload.paths;
        }

        if (paths.length > 0) {
            setActiveTab('process'); // Auto-switch to process view
            processFiles(paths);
        }
    };

    // Listen to all potential event names for maximum compatibility
    const unlisteners: Promise<() => void>[] = [];
    
    unlisteners.push(listen('tauri://drop', handleDropEvent));
    unlisteners.push(listen('tauri://file-drop', handleDropEvent)); // V1 legacy
    unlisteners.push(listen('tauri://drag-drop', handleDropEvent)); // Potential V2 alias

    // Debug Drag Enter
    unlisteners.push(listen('tauri://drag-enter', () => {

        setIsHovering(true);
    }));
    unlisteners.push(listen('tauri://drag-leave', () => {
        setIsHovering(false);
    }));

    return () => {
        unlisteners.forEach(p => p.then(f => f()));
    };
  }, [settings]);

  // View Routing
  const renderContent = () => {
      switch(activeTab) {
          case 'settings':
              return <SettingsView settings={settings} setSettings={setSettings} />
          case 'history':
              return <div className="text-white p-4">History placeholder</div>
          case 'process':
          case 'dashboard':
          default:
              return (
                <DashboardView 
                    stats={stats}
                    handleDrop={handleDropUI}
                    isHovering={isHovering}
                    isProcessing={isProcessing}
                    handleDragEnter={handleDragEnter}
                    handleDragLeave={handleDragLeave}
                    manualSelect={manualSelect}
                />
              )
      }
  }

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden font-sans selection:bg-primary/30">
        {/* Sidebar */}
        <aside className="w-20 lg:w-64 flex flex-col border-r border-white/5 bg-card/30 backdrop-blur-xl z-50 transition-all duration-300">
            <div className="p-6 flex items-center gap-3">
            <div className="h-10 w-10 bg-gradient-to-br from-primary to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-primary/20">
                <Zap className="h-6 w-6 text-white" />
            </div>
            <span className="font-bold text-xl tracking-tight hidden lg:block bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">
                ImgProc
            </span>
            </div>

            <nav className="flex-1 px-4 py-6 space-y-2">
            <NavButton 
                active={activeTab === 'dashboard'} 
                onClick={() => setActiveTab('dashboard')}
                icon={<LayoutDashboard size={20} />}
                label="Dashboard"
            />
            <NavButton 
                active={activeTab === 'process'} 
                onClick={() => setActiveTab('process')}
                icon={<FileImage size={20} />}
                label="Process"
            />
            {/* 
            <NavButton 
                active={activeTab === 'history'} 
                onClick={() => setActiveTab('history')}
                icon={<HistoryIcon size={20} />}
                label="History"
            />
            */}
            </nav>

            <div className="p-4 border-t border-white/5">
            <NavButton 
                active={activeTab === 'settings'} 
                onClick={() => setActiveTab('settings')}
                icon={<SettingsIcon size={20} />}
                label="Settings"
            />
            </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col relative overflow-hidden bg-gradient-to-br from-background to-background/50">
            {/* Glow Effects */}
            <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-primary/10 rounded-full blur-[128px] pointer-events-none mix-blend-screen" />
            <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[128px] pointer-events-none mix-blend-screen" />

            {/* Header */}
            <header className="px-8 py-6 z-10 flex justify-between items-center border-b border-white/5 bg-background/50 backdrop-blur-sm">
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight capitalize">{activeTab}</h1>
                    <p className="text-muted-foreground mt-1">
                        {activeTab === 'settings' ? 'Configure application' : 'Optimize your assets'}
                    </p>
                </div>
            </header>

            {/* View container */}
            <div className="flex-1 px-8 py-8 z-10 overflow-y-auto custom-scrollbar">
                {renderContent()}
            </div>
        </main>
    </div>
  )
}

export default App
