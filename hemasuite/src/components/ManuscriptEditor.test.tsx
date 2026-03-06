import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ManuscriptEditor } from "./ManuscriptEditor";

// Mock TipTap
const mockChain = {
  focus: vi.fn().mockReturnThis(),
  toggleBold: vi.fn().mockReturnThis(),
  toggleItalic: vi.fn().mockReturnThis(),
  toggleHeading: vi.fn().mockReturnThis(),
  toggleBulletList: vi.fn().mockReturnThis(),
  toggleOrderedList: vi.fn().mockReturnThis(),
  insertTable: vi.fn().mockReturnThis(),
  undo: vi.fn().mockReturnThis(),
  redo: vi.fn().mockReturnThis(),
  run: vi.fn(),
};

const mockEditor = {
  chain: vi.fn(() => mockChain),
  getHTML: vi.fn(() => "<p>test</p>"),
  isActive: vi.fn(() => false),
  commands: { setContent: vi.fn() },
};

vi.mock("@tiptap/react", () => ({
  useEditor: vi.fn(() => mockEditor),
  EditorContent: ({ editor }: { editor: unknown }) => (
    <div data-testid="editor-content">{editor ? "Editor loaded" : "No editor"}</div>
  ),
}));

vi.mock("@tiptap/starter-kit", () => ({
  default: { configure: vi.fn() },
}));

vi.mock("@tiptap/extension-table", () => ({
  Table: { configure: vi.fn() },
}));

vi.mock("@tiptap/extension-table-row", () => ({
  TableRow: {},
}));

vi.mock("@tiptap/extension-table-cell", () => ({
  TableCell: {},
}));

vi.mock("@tiptap/extension-table-header", () => ({
  TableHeader: {},
}));

describe("ManuscriptEditor", () => {
  const onUpdate = vi.fn();

  it("renders editor with initial content", () => {
    render(<ManuscriptEditor content="<p>Hello</p>" onUpdate={onUpdate} />);
    expect(screen.getByTestId("editor-content")).toBeTruthy();
    expect(screen.getByText("Editor loaded")).toBeTruthy();
  });

  it("renders toolbar with formatting buttons", () => {
    render(<ManuscriptEditor content="" onUpdate={onUpdate} />);
    expect(screen.getByRole("button", { name: /bold/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /italic/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /heading/i })).toBeTruthy();
  });

  it("bold button calls toggleBold", () => {
    render(<ManuscriptEditor content="" onUpdate={onUpdate} />);
    fireEvent.click(screen.getByRole("button", { name: /bold/i }));
    expect(mockChain.toggleBold).toHaveBeenCalled();
    expect(mockChain.run).toHaveBeenCalled();
  });

  it("italic button calls toggleItalic", () => {
    render(<ManuscriptEditor content="" onUpdate={onUpdate} />);
    fireEvent.click(screen.getByRole("button", { name: /italic/i }));
    expect(mockChain.toggleItalic).toHaveBeenCalled();
  });
});
