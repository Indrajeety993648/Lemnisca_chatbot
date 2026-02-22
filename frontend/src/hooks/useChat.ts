import { useCallback, useState } from "react";
import { postQuery, ApiError } from "../services/apiClient";
import type { ChatState, Message } from "../types";

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function nowIso(): string {
  return new Date().toISOString();
}


export function useChat() {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
    debugInfo: null,
    isDebugOpen: false,
  });

  const sendMessage = useCallback(async (query: string) => {
    const userMessage: Message = {
      id: generateId(),
      role: "user",
      content: query,
      timestamp: nowIso(),
    };

    setState((prev) => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      isLoading: true,
      error: null,
    }));

    try {
      const response = await postQuery(query, false);

      const assistantMessage: Message = {
        id: generateId(),
        role: "assistant",
        content: response.answer,
        timestamp: nowIso(),
        sources: response.sources,
        debug: response.debug,
        flags: response.debug.evaluator_flags ?? [],
      };

      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
        isLoading: false,
        debugInfo: response.debug,
      }));
    } catch (err) {
      let errorMessage = "An unexpected error occurred. Please try again.";

      if (err instanceof ApiError) {
        errorMessage = err.message;
      } else if (err instanceof Error) {
        if (err.name === "AbortError") {
          errorMessage = "Request timed out. Please try again.";
        } else {
          errorMessage = err.message;
        }
      }

      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
    }
  }, []);

  const toggleDebug = useCallback(() => {
    setState((prev) => ({ ...prev, isDebugOpen: !prev.isDebugOpen }));
  }, []);

  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, error: null }));
  }, []);

  return {
    messages: state.messages,
    isLoading: state.isLoading,
    error: state.error,
    debugInfo: state.debugInfo,
    isDebugOpen: state.isDebugOpen,
    sendMessage,
    toggleDebug,
    clearError,
  };
}
