import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { InputBar } from "../../src/components/InputBar";

describe("InputBar", () => {
    it("should render the text input with placeholder", () => {
        render(<InputBar onSend={vi.fn()} isLoading={false} />);
        expect(
            screen.getByPlaceholderText("Ask Clearpath a question...")
        ).toBeInTheDocument();
    });

    it("should render the send button", () => {
        render(<InputBar onSend={vi.fn()} isLoading={false} />);
        expect(screen.getByRole("button", { name: /send message/i })).toBeInTheDocument();
    });

    it("should have send button disabled when input is empty", () => {
        render(<InputBar onSend={vi.fn()} isLoading={false} />);
        expect(screen.getByRole("button", { name: /send message/i })).toBeDisabled();
    });

    it("should enable send button when user types text", async () => {
        const user = userEvent.setup();
        render(<InputBar onSend={vi.fn()} isLoading={false} />);
        const input = screen.getByPlaceholderText("Ask Clearpath a question...");
        await user.type(input, "Hello");
        expect(screen.getByRole("button", { name: /send message/i })).not.toBeDisabled();
    });

    it("should call onSend with the query when send button clicked", async () => {
        const user = userEvent.setup();
        const mockSend = vi.fn();
        render(<InputBar onSend={mockSend} isLoading={false} />);
        const input = screen.getByPlaceholderText("Ask Clearpath a question...");
        await user.type(input, "What is Clearpath?");
        await user.click(screen.getByRole("button", { name: /send message/i }));
        expect(mockSend).toHaveBeenCalledWith("What is Clearpath?");
    });

    it("should call onSend when Enter is pressed", async () => {
        const user = userEvent.setup();
        const mockSend = vi.fn();
        render(<InputBar onSend={mockSend} isLoading={false} />);
        const input = screen.getByPlaceholderText("Ask Clearpath a question...");
        await user.type(input, "Hello{Enter}");
        expect(mockSend).toHaveBeenCalledWith("Hello");
    });

    it("should not call onSend when Shift+Enter is pressed (newline instead)", async () => {
        const user = userEvent.setup();
        const mockSend = vi.fn();
        render(<InputBar onSend={mockSend} isLoading={false} />);
        const input = screen.getByPlaceholderText("Ask Clearpath a question...");
        await user.type(input, "Hello{Shift>}{Enter}{/Shift}");
        expect(mockSend).not.toHaveBeenCalled();
    });

    it("should clear input after sending", async () => {
        const user = userEvent.setup();
        render(<InputBar onSend={vi.fn()} isLoading={false} />);
        const input = screen.getByPlaceholderText("Ask Clearpath a question...");
        await user.type(input, "Hello");
        await user.click(screen.getByRole("button", { name: /send message/i }));
        expect(input).toHaveValue("");
    });

    it("should disable input and button when loading", () => {
        render(<InputBar onSend={vi.fn()} isLoading={true} />);
        expect(
            screen.getByPlaceholderText("Ask Clearpath a question...")
        ).toBeDisabled();
        expect(screen.getByRole("button", { name: /send message/i })).toBeDisabled();
    });

    it("should show character counter when near limit (within 200 chars)", async () => {
        const user = userEvent.setup();
        render(<InputBar onSend={vi.fn()} isLoading={false} />);
        const input = screen.getByPlaceholderText("Ask Clearpath a question...");
        // Type enough to get within 200 chars of 2000 limit
        const longText = "a".repeat(1850);
        await user.type(input, longText);
        expect(screen.getByText(/characters remaining/i)).toBeInTheDocument();
    });

    it("should not call onSend for whitespace-only input", async () => {
        const user = userEvent.setup();
        const mockSend = vi.fn();
        render(<InputBar onSend={mockSend} isLoading={false} />);
        const input = screen.getByPlaceholderText("Ask Clearpath a question...");
        await user.type(input, "   ");
        fireEvent.click(screen.getByRole("button", { name: /send message/i }));
        expect(mockSend).not.toHaveBeenCalled();
    });
});
