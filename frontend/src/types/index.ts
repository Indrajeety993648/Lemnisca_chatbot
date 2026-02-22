export interface Source {
  source_file: string;
  page_number: number;
  score: number;
}

export interface DebugInfo {
  classification: "simple" | "complex";
  model_used: string;
  tokens_input: number;
  tokens_output: number;
  latency_ms: number;
  retrieval_count: number;
  evaluator_flags: string[];
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  sources?: Source[];
  debug?: DebugInfo;
  flags?: string[];
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  debugInfo: DebugInfo | null;
  isDebugOpen: boolean;
}
