import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { DebugPanel } from "../components/DebugPanel";
import type { DebugInfo } from "../types";

const sampleDebugInfo: DebugInfo = {
    classification: "simple",
    model_used: "llama-3.1-8b-instant",
    tokens_input: 120,
    tokens_output: 30,
    latency_ms: 450,
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

// DebugPanel renders DebugContent twice (desktop sidebar + mobile bottom sheet).
// Use getAllBy* and check that at least one match exists.

describe("DebugPanel", () => {
    it("should not render when isOpen is false", () => {
        const { container } = render(
            <DebugPanel debugInfo={sampleDebugInfo} isOpen={false} onToggle={vi.fn()} />
        );
        expect(container.firstChild).toBeNull();
    });

    it("should render when isOpen is true", () => {
        render(
            <DebugPanel debugInfo={sampleDebugInfo} isOpen={true} onToggle={vi.fn()} />
        );
        // Two renders (desktop + mobile) — just confirm at least one "Debug Info" heading
        expect(screen.getAllByText("Debug Info").length).toBeGreaterThanOrEqual(1);
    });

    it("should show placeholder when debugInfo is null", () => {
        render(<DebugPanel debugInfo={null} isOpen={true} onToggle={vi.fn()} />);
        expect(
            screen.getAllByText(/Send a message to see debug information/i).length
        ).toBeGreaterThanOrEqual(1);
    });

    it("should display simple classification badge", () => {
        render(
            <DebugPanel debugInfo={sampleDebugInfo} isOpen={true} onToggle={vi.fn()} />
        );
        expect(screen.getAllByText("Simple").length).toBeGreaterThanOrEqual(1);
    });

    it("should display complex classification badge", () => {
        render(
            <DebugPanel debugInfo={complexDebugInfo} isOpen={true} onToggle={vi.fn()} />
        );
        expect(screen.getAllByText("Complex").length).toBeGreaterThanOrEqual(1);
    });

    it("should display model name", () => {
        render(
            <DebugPanel debugInfo={sampleDebugInfo} isOpen={true} onToggle={vi.fn()} />
        );
        expect(
            screen.getAllByText("llama-3.1-8b-instant").length
        ).toBeGreaterThanOrEqual(1);
    });

    it("should display input token count", () => {
        render(
            <DebugPanel debugInfo={sampleDebugInfo} isOpen={true} onToggle={vi.fn()} />
        );
        // tokens_input = 120 rendered via toLocaleString
        expect(screen.getAllByText("120").length).toBeGreaterThanOrEqual(1);
    });

    it("should display output token count", () => {
        render(
            <DebugPanel debugInfo={sampleDebugInfo} isOpen={true} onToggle={vi.fn()} />
        );
        // tokens_output = 30
        expect(screen.getAllByText("30").length).toBeGreaterThanOrEqual(1);
    });

    it("should display latency formatted with ms suffix", () => {
        render(
            <DebugPanel debugInfo={sampleDebugInfo} isOpen={true} onToggle={vi.fn()} />
        );
        // latency_ms = 450 → "450 ms" via toFixed(0)
        expect(screen.getAllByText("450 ms").length).toBeGreaterThanOrEqual(1);
    });

    it("should display retrieval count", () => {
        render(
            <DebugPanel debugInfo={sampleDebugInfo} isOpen={true} onToggle={vi.fn()} />
        );
        expect(screen.getAllByText("3").length).toBeGreaterThanOrEqual(1);
    });

    it("should display evaluator flag chips", () => {
        render(
            <DebugPanel debugInfo={complexDebugInfo} isOpen={true} onToggle={vi.fn()} />
        );
        expect(
            screen.getAllByText("No Context Warning").length
        ).toBeGreaterThanOrEqual(1);
        expect(
            screen.getAllByText("Potential Hallucination").length
        ).toBeGreaterThanOrEqual(1);
    });

    it("should not render Evaluator Flags heading when flags array is empty", () => {
        render(
            <DebugPanel debugInfo={sampleDebugInfo} isOpen={true} onToggle={vi.fn()} />
        );
        expect(screen.queryByText("Evaluator Flags")).not.toBeInTheDocument();
    });

    it("should call onToggle when a close button is clicked", () => {
        const mockToggle = vi.fn();
        render(
            <DebugPanel debugInfo={sampleDebugInfo} isOpen={true} onToggle={mockToggle} />
        );
        // Two close buttons exist (desktop + mobile); click the first one
        const closeButtons = screen.getAllByRole("button", { name: /close debug panel/i });
        expect(closeButtons.length).toBeGreaterThanOrEqual(1);
        fireEvent.click(closeButtons[0]);
        expect(mockToggle).toHaveBeenCalledTimes(1);
    });
});
