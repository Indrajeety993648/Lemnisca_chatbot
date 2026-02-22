import "@testing-library/jest-dom";

// jsdom does not implement scrollIntoView — mock it globally
window.HTMLElement.prototype.scrollIntoView = vi.fn();
