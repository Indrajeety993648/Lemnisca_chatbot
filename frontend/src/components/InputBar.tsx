import { useRef, useState, useCallback, type KeyboardEvent } from "react";

interface InputBarProps {
  onSend: (query: string) => void;
  isLoading: boolean;
}

const MAX_CHARS = 2000;
const COUNTER_THRESHOLD = 200;

export function InputBar({ onSend, isLoading }: InputBarProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const canSend = value.trim().length > 0 && !isLoading;
  const remaining = MAX_CHARS - value.length;
  const isNearLimit = remaining <= COUNTER_THRESHOLD;

  const handleSend = useCallback(() => {
    if (!canSend) return;
    onSend(value.trim());
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [canSend, value, onSend]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
  };

  return (
    <div className="shrink-0 px-4 pb-4 pt-2">
      {/* Floating input container */}
      <div
        className={`relative rounded-2xl transition-all duration-200 ${isLoading ? "opacity-70" : ""}`}
        style={{
          background: "rgba(255,255,255,0.04)",
          border: canSend
            ? "1px solid rgba(6,182,212,0.45)"
            : "1px solid rgba(255,255,255,0.09)",
          boxShadow: canSend
            ? "0 0 0 1px rgba(6,182,212,0.15), 0 8px 32px rgba(6,182,212,0.12)"
            : "0 4px 24px rgba(0,0,0,0.3)",
        }}
      >
        {/* Textarea */}
        <textarea
          ref={textareaRef}
          id="chat-input"
          value={value}
          onChange={(e) => {
            if (e.target.value.length <= MAX_CHARS) setValue(e.target.value);
          }}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder="Ask Clearpath anything…"
          disabled={isLoading}
          rows={1}
          aria-label="Message input"
          aria-multiline="true"
          className="w-full resize-none bg-transparent text-[14px] text-white placeholder-slate-500 focus:outline-none leading-relaxed scrollbar-thin px-4 pt-4 pb-12 min-h-[56px] max-h-[180px] disabled:cursor-not-allowed block"
        />

        {/* Bottom toolbar inside the box */}
        <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between px-3 pb-2.5 pointer-events-none">
          {/* Left — char counter or hint */}
          <span className="text-[11px] text-slate-600 pointer-events-none select-none">
            {isNearLimit ? (
              <span className={remaining <= 50 ? "text-red-400" : "text-amber-400"}>
                {remaining} left
              </span>
            ) : (
              <span>
                <kbd className="px-1 py-0.5 rounded border border-white/10 text-[10px] text-slate-600">Enter</kbd>
                {" "}to send
              </span>
            )}
          </span>

          {/* Right — send button */}
          <button
            type="button"
            id="send-button"
            onClick={handleSend}
            disabled={!canSend}
            aria-label="Send message"
            className={`pointer-events-auto w-8 h-8 rounded-xl flex items-center justify-center transition-all duration-200 shrink-0 ${
              canSend ? "hover:scale-105 active:scale-95" : "cursor-not-allowed"
            }`}
            style={
              canSend
                ? {
                    background: "linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)",
                    boxShadow: "0 0 14px rgba(6,182,212,0.4)",
                  }
                : { background: "rgba(255,255,255,0.07)" }
            }
          >
            {isLoading ? (
              <svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" className="animate-spin opacity-60">
                <circle cx="12" cy="12" r="10" strokeOpacity="0.2" />
                <path d="M12 2a10 10 0 0 1 10 10" />
              </svg>
            ) : (
              <svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={canSend ? "white" : "rgba(255,255,255,0.25)"} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="19" x2="12" y2="5" />
                <polyline points="5,12 12,5 19,12" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Disclaimer below */}
      <p className="text-center text-[10px] text-slate-700 mt-2 select-none">
        Clearpath AI · Answers based on official documentation
      </p>
    </div>
  );
}
