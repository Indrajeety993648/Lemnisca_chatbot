import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ChatBox } from "../../src/components/ChatBox";
import type { Message } from "../../src/types";

const userMessage: Message = {
    id: "1",
    role: "user",
    content: "Hello",
    timestamp: new Date().toISOString(),
};

const assistantMessage: Message = {
    id: "2",
    role: "assistant",
    content: "Hello! How can I help you today?",
    timestamp: new Date().toISOString(),
};

describe("ChatBox", () => {
    it("should render empty state when no messages", () => {
        render(<ChatBox messages={[]} isLoading={false} />);
        expect(screen.getByText(/Clearpath Assistant/i)).toBeInTheDocument();
        expect(
            screen.getByText(/Ask me anything about Clearpath/i)
        ).toBeInTheDocument();
    });

    it("should render user message when messages are provided", () => {
        render(<ChatBox messages={[userMessage]} isLoading={false} />);
        expect(screen.getByText("Hello")).toBeInTheDocument();
    });

    it("should render assistant message content", () => {
        render(<ChatBox messages={[assistantMessage]} isLoading={false} />);
        expect(
            screen.getByText("Hello! How can I help you today?")
        ).toBeInTheDocument();
    });

    it("should render multiple messages", () => {
        render(
            <ChatBox messages={[userMessage, assistantMessage]} isLoading={false} />
        );
        expect(screen.getByText("Hello")).toBeInTheDocument();
        expect(
            screen.getByText("Hello! How can I help you today?")
        ).toBeInTheDocument();
    });

    it("should show typing indicator when loading with messages", () => {
        render(<ChatBox messages={[userMessage]} isLoading={true} />);
        expect(screen.getByLabelText("Assistant is typing")).toBeInTheDocument();
    });

    it("should show typing indicator when loading with no messages", () => {
        render(<ChatBox messages={[]} isLoading={true} />);
        expect(screen.getByLabelText("Assistant is typing")).toBeInTheDocument();
    });

    it("should not show typing indicator when not loading", () => {
        render(<ChatBox messages={[userMessage]} isLoading={false} />);
        expect(
            screen.queryByLabelText("Assistant is typing")
        ).not.toBeInTheDocument();
    });

    it("should have role=log for accessibility", () => {
        render(<ChatBox messages={[]} isLoading={false} />);
        expect(screen.getByRole("log")).toBeInTheDocument();
    });

    it("should have aria-live polite attribute", () => {
        render(<ChatBox messages={[]} isLoading={false} />);
        const log = screen.getByRole("log");
        expect(log).toHaveAttribute("aria-live", "polite");
    });
});
