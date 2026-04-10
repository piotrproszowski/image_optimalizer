export interface AppSettings {
  outputFormat: OutputFormat;
  quality: number;
  maxDimension: number;
  stripMetadata: boolean;
}

export type OutputFormat = 'original' | 'webp' | 'png' | 'jpg' | 'avif';

export type ActiveTab = 'process' | 'settings' | 'results';

export interface ProcessedImage {
  id: string;
  originalFile: File;
  originalSize: number;
  processedBlob: Blob;
  processedSize: number;
  outputFormat: string;
  previewUrl: string;
  fileName: string;
}

export interface ProcessingProgress {
  current: number;
  total: number;
  lastFile: string;
}
