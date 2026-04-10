import type { AppSettings } from '../types';

interface SettingsViewProps {
  settings: AppSettings;
  setSettings: React.Dispatch<React.SetStateAction<AppSettings>>;
}

const OUTPUT_FORMATS = ['original', 'webp', 'png', 'jpg', 'avif'] as const;

const MAX_DIMENSION_DEFAULT = 2048;
const MAX_DIMENSION_MIN = 256;
const MAX_DIMENSION_MAX = 8192;

export function SettingsView({ settings, setSettings }: SettingsViewProps) {
  return (
    <div className='space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20'>
      <div className='space-y-2'>
        <h2 className='text-2xl font-bold text-white'>Conversion Settings</h2>
        <p className='text-muted-foreground'>
          Configure how your images are processed.
        </p>
      </div>

      <div className='space-y-6'>
        {/* Format Selection */}
        <div className='p-6 rounded-2xl bg-card/40 border border-white/5 space-y-4'>
          <h3 className='text-lg font-semibold text-white'>Output Format</h3>
          <div className='grid grid-cols-2 md:grid-cols-5 gap-3'>
            {OUTPUT_FORMATS.map((fmt) => (
              <button
                key={fmt}
                onClick={() =>
                  setSettings((s) => ({ ...s, outputFormat: fmt }))
                }
                className={`px-4 py-3 rounded-xl border transition-all ${
                  settings.outputFormat === fmt
                    ? 'bg-primary text-primary-foreground border-primary'
                    : 'bg-white/5 border-white/10 hover:bg-white/10 text-muted-foreground hover:text-white'
                }`}
              >
                {fmt.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Quality Slider */}
        <div className='p-6 rounded-2xl bg-card/40 border border-white/5 space-y-4'>
          <div className='flex justify-between items-center'>
            <h3 className='text-lg font-semibold text-white'>Quality</h3>
            <span className='text-primary font-mono'>{settings.quality}%</span>
          </div>
          <input
            type='range'
            min='1'
            max='100'
            value={settings.quality}
            onChange={(e) =>
              setSettings((s) => ({ ...s, quality: parseInt(e.target.value) }))
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
            <h3 className='text-lg font-semibold text-white'>Max Dimension</h3>
            <span className='text-primary font-mono'>
              {settings.maxDimension}px
            </span>
          </div>
          <input
            type='range'
            min={MAX_DIMENSION_MIN}
            max={MAX_DIMENSION_MAX}
            step='128'
            value={settings.maxDimension}
            onChange={(e) =>
              setSettings((s) => ({
                ...s,
                maxDimension: parseInt(e.target.value),
              }))
            }
            className='w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-primary'
          />
          <div className='flex justify-between text-xs text-muted-foreground'>
            <span>{MAX_DIMENSION_MIN}px</span>
            <span>Default: {MAX_DIMENSION_DEFAULT}px</span>
            <span>{MAX_DIMENSION_MAX}px</span>
          </div>
        </div>

        {/* Strip Metadata */}
        <div className='p-6 rounded-2xl bg-card/40 border border-white/5 flex items-center justify-between'>
          <div>
            <h3 className='text-lg font-semibold text-white'>Strip Metadata</h3>
            <p className='text-sm text-muted-foreground'>
              Canvas API always strips EXIF data (built-in privacy).
            </p>
          </div>
          <button
            onClick={() =>
              setSettings((s) => ({ ...s, stripMetadata: !s.stripMetadata }))
            }
            className={`w-12 h-7 rounded-full transition-colors relative ${
              settings.stripMetadata ? 'bg-primary' : 'bg-white/20'
            }`}
          >
            <div
              className={`absolute top-1 left-1 w-5 h-5 bg-white rounded-full transition-transform ${
                settings.stripMetadata ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
      </div>
    </div>
  );
}
