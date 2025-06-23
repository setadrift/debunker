export interface SourceBias {
  id: string;
  name: string;
  bias_score: number;
  bias_label: 'left' | 'center' | 'right' | 'unknown';
}

export interface Source {
  id: number;
  platform: string;
  text_excerpt: string;
  timestamp: string;
  url: string;
  engagement: number;
  bias?: SourceBias | null;
}

export interface TimelineEvent {
  date: string;
  mentions: number;
}

export interface NarrativeDetail {
  summary: string;
  sources: Source[];
  timeline: TimelineEvent[];
  cluster_bias_avg?: number | null;
}

export interface Narrative {
  id: number;
  summary: string;
  source_count: number;
  last_seen: string;
  first_seen: string;
  cluster_bias_avg?: number | null;
} 