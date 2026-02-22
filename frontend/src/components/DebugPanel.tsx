import type { DebugInfo } from "../types";

interface DebugPanelProps {
  debugInfo: DebugInfo | null;
  isOpen: boolean;
  onToggle: () => void;
}

function FlagChip({ flag }: { flag: string }) {
  const isWarning = flag === "no_context_warning" || flag === "potential_hallucination";
  const label = flag.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium border ${isWarning
          ? "text-amber-300 border-amber-500/40 bg-amber-500/10"
          : "text-slate-400 border-white/15 bg-white/5"
        }`}
    >
      {label}
    </span>
  );
}

function DebugRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
      <span className="text-[12px] text-slate-500">{label}</span>
      <span className="text-[12px] font-mono text-slate-200 font-medium">{value}</span>
    </div>
  );
}

function DebugContent({ debugInfo, onToggle }: { debugInfo: DebugInfo | null; onToggle: () => void }) {
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/5 shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg flex items-center justify-center" style={{ background: "linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)" }}>
            <svg aria-hidden="true" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
              <path d="M12 8v4M12 16h.01" />
            </svg>
          </div>
          <span className="text-[14px] font-semibold text-white">Debug Info</span>
        </div>
        <button
          type="button"
          onClick={onToggle}
          aria-label="Close debug panel"
          className="p-1.5 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-white/5 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 transition-colors"
        >
          <svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-4 py-4 scrollbar-thin">
        {debugInfo === null ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-12">
            <div className="w-12 h-12 rounded-xl mb-4 flex items-center justify-center" style={{ background: "rgba(14,165,233,0.12)" }}>
              <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
                <path d="M12 8v4M12 16h.01" />
              </svg>
            </div>
            <p className="text-[13px] text-slate-500">Send a message to see debug information.</p>
          </div>
        ) : (
          <div className="space-y-5">
            {/* Classification */}
            <div>
              <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">Classification</p>
              <span
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[12px] font-semibold ${debugInfo.classification === "simple"
                    ? "text-emerald-300 bg-emerald-500/15 border border-emerald-500/30"
                    : "text-orange-300 bg-orange-500/15 border border-orange-500/30"
                  }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${debugInfo.classification === "simple" ? "bg-emerald-400" : "bg-orange-400"}`} />
                {debugInfo.classification === "simple" ? "Simple" : "Complex"}
              </span>
            </div>

            {/* Stats rows */}
            <div>
              <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">Model & Metrics</p>
              <div className="glass rounded-xl px-3">
                <DebugRow label="Model" value={debugInfo.model_used} />
                <DebugRow label="Input tokens" value={debugInfo.tokens_input.toLocaleString()} />
                <DebugRow label="Output tokens" value={debugInfo.tokens_output.toLocaleString()} />
                <DebugRow label="Latency" value={`${debugInfo.latency_ms.toFixed(0)} ms`} />
                <DebugRow label="Sources retrieved" value={debugInfo.retrieval_count} />
              </div>
            </div>

            {/* Flags */}
            {debugInfo.evaluator_flags.length > 0 && (
              <div>
                <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">Evaluator Flags</p>
                <div className="flex flex-wrap gap-1.5">
                  {debugInfo.evaluator_flags.map((flag) => (
                    <FlagChip key={flag} flag={flag} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export function DebugPanel({ debugInfo, isOpen, onToggle }: DebugPanelProps) {
  if (!isOpen) return null;

  return (
    <>
      {/* Desktop: card beside the chat */}
      <aside
        id="debug-panel"
        aria-label="Debug information"
        className="hidden lg:flex flex-col w-72 shrink-0 rounded-2xl overflow-hidden"
        style={{
          background: "rgba(8,10,22,0.85)",
          border: "1px solid rgba(255,255,255,0.07)",
          boxShadow: "0 24px 80px rgba(0,0,0,0.5)",
          backdropFilter: "blur(20px)",
        }}
      >
        <DebugContent debugInfo={debugInfo} onToggle={onToggle} />
      </aside>

      {/* Mobile: bottom sheet */}
      <div className="lg:hidden fixed inset-0 z-30 flex flex-col justify-end">
        <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" aria-hidden="true" onClick={onToggle} />
        <div
          className="relative rounded-t-2xl max-h-[70vh] overflow-y-auto scrollbar-thin border-t border-white/10"
          style={{ background: "rgba(6,9,20,0.95)", backdropFilter: "blur(20px)" }}
          role="dialog"
          aria-modal="true"
          aria-label="Debug information"
        >
          <DebugContent debugInfo={debugInfo} onToggle={onToggle} />
        </div>
      </div>
    </>
  );
}
