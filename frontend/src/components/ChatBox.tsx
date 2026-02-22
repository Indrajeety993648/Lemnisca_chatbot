import { useEffect, useRef } from "react";
import { MessageBubble } from "./MessageBubble";
import { RobotIcon } from "./RobotIcon";
import type { Message } from "../types";

interface ChatBoxProps {
  messages: Message[];
  isLoading: boolean;
}

function TypingIndicator() {
  return (
    <div className="flex justify-start mb-4 px-1">
      <div className="flex items-center gap-3">
        {/* Avatar */}
        <div className="w-7 h-7 rounded-lg shrink-0 flex items-center justify-center" style={{ background: "linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)" }}>
          <RobotIcon size="sm" />
        </div>
        <div
          aria-label="Assistant is typing"
          className="px-4 py-3 rounded-2xl rounded-bl-sm glass"
        >
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-sky-400 dot-bounce" style={{ animationDelay: "0ms" }} />
            <span className="w-2 h-2 rounded-full bg-sky-400 dot-bounce" style={{ animationDelay: "200ms" }} />
            <span className="w-2 h-2 rounded-full bg-sky-400 dot-bounce" style={{ animationDelay: "400ms" }} />
          </div>
        </div>
      </div>
    </div>
  );
}

/** Decorative ghost chat bubbles shown in the empty state */
function GhostChat() {
  return (
    <div className="w-full max-w-sm space-y-3 pointer-events-none select-none" aria-hidden="true">
      {/* User bubble */}
      <div className="flex justify-end">
        <div
          className="px-4 py-2.5 rounded-2xl rounded-br-sm text-[13px] text-white/55 max-w-[78%]"
          style={{ background: "linear-gradient(135deg, rgba(14,165,233,0.25) 0%, rgba(6,182,212,0.25) 100%)", border: "1px solid rgba(6,182,212,0.2)" }}
        >
          What are Clearpath's pricing plans?
        </div>
      </div>

      {/* Assistant bubble */}
      <div className="flex justify-start items-end gap-2">
        <div
          className="w-6 h-6 rounded-md shrink-0 flex items-center justify-center opacity-50"
          style={{ background: "linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)" }}
        >
          <RobotIcon size="sm" />
        </div>
        <div
          className="px-4 py-2.5 rounded-2xl rounded-bl-sm text-[13px] text-slate-400 max-w-[78%] space-y-1"
          style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
        >
          <p>Clearpath offers three plans — <span className="text-sky-400/80">Starter</span>, <span className="text-sky-400/80">Pro</span>, and <span className="text-sky-400/80">Enterprise</span>.</p>
          <p className="text-slate-500 text-[11px]">Sourced from documentation · p4</p>
        </div>
      </div>

      {/* User bubble */}
      <div className="flex justify-end">
        <div
          className="px-4 py-2.5 rounded-2xl rounded-br-sm text-[13px] text-white/55 max-w-[78%]"
          style={{ background: "linear-gradient(135deg, rgba(14,165,233,0.25) 0%, rgba(6,182,212,0.25) 100%)", border: "1px solid rgba(6,182,212,0.2)" }}
        >
          How do I reset my password?
        </div>
      </div>

      {/* Fading overlay at bottom */}
      <div className="absolute bottom-0 left-0 right-0 h-10 pointer-events-none" style={{ background: "linear-gradient(to bottom, transparent, #060914)" }} />
    </div>
  );
}

interface ChatBoxProps2 extends ChatBoxProps {
  onSuggest?: (query: string) => void;
}

export function ChatBox({ messages, isLoading, onSuggest: _onSuggest }: ChatBoxProps2) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const isEmpty = messages.length === 0;

  return (
    <div
      role="log"
      aria-label="Chat messages"
      aria-live="polite"
      aria-atomic="false"
      className="flex-1 overflow-y-auto scrollbar-thin px-4 py-6 flex flex-col"
    >
      {/* Welcome / Empty State */}
      {isEmpty && !isLoading && (
        <div className="flex-1 flex flex-col items-center justify-center text-center px-4 gap-6">
          {/* Hero icon */}
          <div className="relative">
            <div
              className="w-20 h-20 rounded-2xl flex items-center justify-center glow-purple"
              style={{ background: "linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)" }}
            >
              <RobotIcon size="lg" />
            </div>
            {/* Pulse ring */}
            <div className="absolute inset-0 rounded-2xl animate-ping opacity-15" style={{ background: "linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)" }} />
          </div>

          <div>
            <h2 className="text-[28px] font-bold text-white mb-2 leading-tight">
              <span className="gradient-text">Clearpath Assistant</span>
            </h2>
            <p className="text-[14px] text-slate-400 max-w-xs leading-relaxed">
              Ask me anything about Clearpath products, plans, and support topics.
            </p>
          </div>

          {/* Ghost preview chat */}
          <div className="relative w-full max-w-sm">
            <GhostChat />
          </div>
        </div>
      )}

      {/* Messages */}
      {!isEmpty && (
        <div className="flex flex-col gap-1">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {isLoading && <TypingIndicator />}
        </div>
      )}

      {isEmpty && isLoading && <TypingIndicator />}

      <div ref={bottomRef} aria-hidden="true" />
    </div>
  );
}
