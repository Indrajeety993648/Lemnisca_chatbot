import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { DebugPanel } from "../../src/components/DebugPanel";
import type { DebugInfo } from "../../src/types";

const sampleDebugInfo: DebugInfo = {
    classification: "simple",
    model_used: "llama-3.1-8b-instant",
    tokens_input: 120,
    tokens_output: 30,
    latency_ms: 450.5,
    retrieval_count: 3,
    evaluator_flags: [],
};

const complexDebugInfo: DebugInfo = {
    classification: "complex",
    model_used: "llama-3.3-70b-versatile",
    tokens_input: 500,
    tokens_output: 200,
    latency_ms: 2100.0,
    retrieval_count: 5,
    evaluator_flags: ["no_context_warning", "potential_hallucination"],
};

describe("DebugPanel", () => {
    it("should not render when isOpen is false", () => {
        const { container } = render(
            <DebugPanel
                debugInfo={sampleDebugInfo}
                isOpen={false}
                onToggle={vi.fn()}
            />
        );
        expect(container.firstChild).toBeNull();
    });

    it("should render when isOpen is true", () => {
        render(
            <DebugPanel
                debugInfo={sampleDebugInfo}
                isOpen={true}
                onToggle={vi.fn()}
            />
        );
        expect(screen.getByText("Debug Info")).toBeInTheDocument();
    });

    it("should show placeholder when debugInfo is null", () => {
        render(
            <DebugPanel debugInfo={null} isOpen={true} onToggle={vi.fn()} />
        );
        expect(
            screen.getByText(/Send a message to see debug information/i)
        ).toBeInTheDocument();
    });

    it("should display simple classification badge in green", () => {
        render(
            <DebugPanel
                debugInfo={sampleDebugInfo}
                isOpen={true}
                onToggle={vi.fn()}
            />
        );
        expect(screen.getByText("Simple")).toBeInTheDocument();
    });

    it("should display complex classification badge in orange for complex query", () => {
        render(
            <DebugPanel
                debugInfo={complexDebugInfo}
                isOpen={true}
                onToggle={vi.fn()}
            />
        );
        expect(screen.getByText("Complex")).toBeInTheDocument();
    });

    it("should display model name", () => {
        render(
            <DebugPanel
                debugInfo={sampleDebugInfo}
                isOpen={true}
                onToggle={vi.fn()}
            />
        );
        expect(
            screen.getByText("llama-3.1-8b-instant")
        ).toBeInTheDocument();
    });

    it("should display token counts", () => {
        render(
            <DebugPanel
                debugInfo={sampleDebugInfo}
                isOpen={true}
                onToggle={vi.fn()}
            />
        );
        expect(screen.getByText("120")).toBeInTheDocument();
        expect(screen.getByText("30")).toBeInTheDocument();
    });

    it("should display latency with ms suffix", () => {
        render(
            <DebugPanel
                debugInfo={sampleDebugInfo}
                isOpen={true}
                onToggle={vi.fn()}
            />
        );
        expect(screen.getByText(/450.*ms/i)).toBeInTheDocument();
    });

    it("should display retrieval count", () => {
        render(
            <DebugPanel
                debugInfo={sampleDebugInfo}
                isOpen={true}
                onToggle={vi.fn()}
            />
        );
        expect(screen.getByText("3")).toBeInTheDocument();
    });

    it("should display evaluator flags as chips", () => {
        render(
            <DebugPanel
                debugInfo={complexDebugInfo}
                isOpen={true}
                onToggle={vi.fn()}
            />
        );
        expect(screen.getByText("No Context Warning")).toBeInTheDocument();
        expect(screen.getByText("Potential Hallucination")).toBeInTheDocument();
    });

    it("should not render flags section when no flags", () => {
        render(
            <DebugPanel
                debugInfo={sampleDebugInfo}
                isOpen={true}
                onToggle={vi.fn()}
            />
        );
        expect(screen.queryByText("Evaluator Flags")).not.toBeInTheDocument();
    });

    it("should call onToggle when close button clicked", () => {
        const mockToggle = vi.fn();
        render(
            <DebugPanel
                debugInfo={sampleDebugInfo}
                isOpen={true}
                onToggle={mockToggle}
            />
        );
        fireEvent.click(screen.getByRole("button", { name: /close debug panel/i }));
        expect(mockToggle).toHaveBeenCalledTimes(1);
    });
});
