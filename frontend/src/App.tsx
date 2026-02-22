import { ChatBox } from "./components/ChatBox";
import { DebugPanel } from "./components/DebugPanel";
import { InputBar } from "./components/InputBar";
import { RobotIcon } from "./components/RobotIcon";
import { useChat } from "./hooks/useChat";

export function App() {
  const {
    messages,
    isLoading,
    error,
    debugInfo,
    isDebugOpen,
    sendMessage,
    toggleDebug,
    clearError,
  } = useChat();

  return (
    <div className="flex h-screen w-full items-center justify-center overflow-hidden" style={{ background: "linear-gradient(135deg, #060914 0%, #080f20 50%, #060914 100%)" }}>
      {/* Ambient background orbs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full opacity-20" style={{ background: "radial-gradient(circle, #0ea5e9 0%, transparent 70%)" }} />
        <div className="absolute top-1/2 -right-32 w-80 h-80 rounded-full opacity-10" style={{ background: "radial-gradient(circle, #06b6d4 0%, transparent 70%)" }} />
        <div className="absolute -bottom-20 left-1/3 w-72 h-72 rounded-full opacity-12" style={{ background: "radial-gradient(circle, #0284c7 0%, transparent 70%)" }} />
      </div>

      {/* Centered chat card + optional debug panel side-by-side */}
      <div className="flex w-full max-w-5xl h-[92vh] mx-auto px-4 gap-4 relative z-10">

        {/* Main chat column */}
        <div
          className="flex flex-col flex-1 min-w-0 overflow-hidden rounded-2xl"
          style={{
            background: "rgba(8,10,22,0.85)",
            border: "1px solid rgba(255,255,255,0.07)",
            boxShadow: "0 24px 80px rgba(0,0,0,0.6), 0 0 0 1px rgba(6,182,212,0.06)",
            backdropFilter: "blur(20px)",
          }}
        >

        {/* Header */}
        <header className="flex items-center justify-between px-5 py-4 shrink-0 border-b border-white/5">
          <div className="flex items-center gap-3">
            {/* Logo */}
            <div className="relative">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center glow-purple" style={{ background: "linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)" }}>
                <RobotIcon size="sm" />
              </div>
              {/* Online dot */}
              <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-400 border-2 border-[#060914]" />
            </div>

            <div>
              <h1 className="text-[16px] font-bold text-white leading-tight">Clearpath Assistant</h1>
              <p className="text-[11px] text-sky-400 font-medium">AI-powered support</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={toggleDebug}
              aria-label={isDebugOpen ? "Close debug panel" : "Open debug panel"}
              aria-expanded={isDebugOpen}
              aria-controls="debug-panel"
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-[12px] font-medium transition-all duration-200 ${isDebugOpen
                ? "text-sky-300 border border-sky-500/40"
                : "text-slate-400 hover:text-sky-300 border border-white/10 hover:border-sky-500/40 hover:bg-sky-600/10"
                }`}
              style={isDebugOpen ? { background: "rgba(14,165,233,0.12)" } : {}}
            >
              <svg aria-hidden="true" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
                <path d="M12 8v4M12 16h.01" />
              </svg>
              Debug
            </button>
          </div>
        </header>

        {/* Error banner */}
        {error && (
          <div
            role="alert"
            className="flex items-center justify-between mx-4 mt-3 px-4 py-3 rounded-xl border border-red-500/30 text-[13px] text-red-300"
            style={{ background: "rgba(239,68,68,0.1)" }}
          >
            <div className="flex items-center gap-2">
              <svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
                <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <span>{error}</span>
            </div>
            <button type="button" onClick={clearError} aria-label="Dismiss error" className="ml-4 text-red-400 hover:text-red-200 transition-colors rounded">
              <svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        )}

          <ChatBox messages={messages} isLoading={isLoading} onSuggest={sendMessage} />
          <InputBar onSend={sendMessage} isLoading={isLoading} />
        </div>

        {/* Debug panel — sits beside the chat card */}
        <DebugPanel debugInfo={debugInfo} isOpen={isDebugOpen} onToggle={toggleDebug} />
      </div>
    </div>
  );
}
