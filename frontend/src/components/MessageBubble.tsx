import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { RobotIcon } from "./RobotIcon";
import type { Message } from "../types";

interface MessageBubbleProps {
  message: Message;
}

function SourcesSection({ message }: { message: Message }) {
  if (!message.sources || message.sources.length === 0) return null;
  return (
    <div className="mt-3 pt-3 border-t border-white/10">
      <p className="text-[11px] font-semibold text-sky-400 uppercase tracking-wider mb-2">
        Sources
      </p>
      <div className="flex flex-wrap gap-1.5">
        {message.sources.map((src, i) => (
          <span
            key={i}
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] text-slate-300 border border-white/10"
            style={{ background: "rgba(255,255,255,0.05)" }}
          >
            <svg aria-hidden="true" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-sky-400">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14,2 14,8 20,8" />
            </svg>
            {src.source_file
              .replace(/\.pdf$/i, "")
              .replace(/^\d+_/, "")
              .replace(/_/g, " ")
              .replace(/v(\d)/g, "v$1")
            } · p{src.page_number}
          </span>
        ))}
      </div>
    </div>
  );
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  const hasNoContext = message.flags?.includes("no_context_warning");
  const hasPotentialHallucination = message.flags?.includes("potential_hallucination");
  const hasRefusal = message.flags?.includes("refusal_detected");

  const time = new Date(message.timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className={`flex w-full mb-3 ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`flex items-end gap-2.5 max-w-[85%] lg:max-w-[70%] ${isUser ? "flex-row-reverse" : "flex-row"}`}>

        {/* Avatar */}
        {!isUser && (
          <div className="w-7 h-7 rounded-lg shrink-0 mb-1 flex items-center justify-center" style={{ background: "linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)" }}>
            <RobotIcon size="sm" />
          </div>
        )}

        <div className={`flex flex-col gap-1 ${isUser ? "items-end" : "items-start"}`}>
          {/* Message bubble */}
          <div
            className={`relative px-4 py-3 rounded-2xl text-[14px] leading-relaxed ${isUser
                ? "text-white rounded-br-sm"
                : "text-slate-200 rounded-bl-sm glass"
              }`}
            style={isUser
              ? { background: "linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)", boxShadow: "0 4px 20px rgba(6, 182, 212, 0.25)" }
              : {}}
          >
            {isUser ? (
              <p className="whitespace-pre-wrap">{message.content}</p>
            ) : (
              <div className="prose prose-sm max-w-none prose-invert prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0 prose-headings:text-white prose-a:text-sky-400 prose-code:text-cyan-300 prose-code:bg-white/10 prose-code:px-1 prose-code:rounded prose-pre:bg-black/30 prose-pre:border prose-pre:border-white/10">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content || "\u00a0"}</ReactMarkdown>
              </div>
            )}

            {/* Sources inside bubble (assistant only) */}
            {!isUser && <SourcesSection message={message} />}
          </div>

          {/* Timestamp */}
          <span className="text-[10px] text-slate-500 px-1">{time}</span>

          {/* Evaluator warning flags */}
          {!isUser && hasNoContext && (
            <div role="alert" className="flex items-start gap-2 px-3 py-2 rounded-lg text-[12px] text-amber-300 border border-amber-500/30" style={{ background: "rgba(245,158,11,0.08)" }}>
              <span aria-hidden="true" className="shrink-0 mt-px">⚠</span>
              <span>This response was generated without supporting documentation.</span>
            </div>
          )}
          {!isUser && hasPotentialHallucination && (
            <div role="alert" className="flex items-start gap-2 px-3 py-2 rounded-lg text-[12px] text-orange-300 border border-orange-500/30" style={{ background: "rgba(249,115,22,0.08)" }}>
              <span aria-hidden="true" className="shrink-0 mt-px">⚠</span>
              <span>Some details could not be verified against our documentation.</span>
            </div>
          )}
          {!isUser && hasRefusal && (
            <div role="status" className="flex items-start gap-2 px-3 py-2 rounded-lg text-[12px] text-slate-400 border border-white/10" style={{ background: "rgba(255,255,255,0.05)" }}>
              <span aria-hidden="true" className="shrink-0 mt-px">ℹ</span>
              <span>The assistant couldn't find a definitive answer.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
