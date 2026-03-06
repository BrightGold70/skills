import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { Table } from "@tiptap/extension-table";
import { TableRow } from "@tiptap/extension-table-row";
import { TableCell } from "@tiptap/extension-table-cell";
import { TableHeader } from "@tiptap/extension-table-header";

interface ManuscriptEditorProps {
  content: string;
  onUpdate: (html: string) => void;
  readOnly?: boolean;
}

export function ManuscriptEditor({ content, onUpdate, readOnly = false }: ManuscriptEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Table.configure({ resizable: true }),
      TableRow,
      TableCell,
      TableHeader,
    ],
    content,
    editable: !readOnly,
    onUpdate: ({ editor: e }) => {
      onUpdate(e.getHTML());
    },
  });

  if (!editor) return null;

  const toolbar = [
    { label: "Bold", action: () => editor.chain().focus().toggleBold().run() },
    { label: "Italic", action: () => editor.chain().focus().toggleItalic().run() },
    { label: "Heading", action: () => editor.chain().focus().toggleHeading({ level: 2 }).run() },
    { label: "List", action: () => editor.chain().focus().toggleBulletList().run() },
    { label: "Table", action: () => editor.chain().focus().insertTable({ rows: 3, cols: 3 }).run() },
    { label: "Undo", action: () => editor.chain().focus().undo().run() },
    { label: "Redo", action: () => editor.chain().focus().redo().run() },
  ];

  return (
    <div className="border rounded-lg overflow-hidden">
      {!readOnly && (
        <div className="flex gap-1 p-2 bg-gray-50 border-b">
          {toolbar.map((btn) => (
            <button
              key={btn.label}
              onClick={btn.action}
              aria-label={btn.label}
              className="px-2 py-1 text-sm rounded hover:bg-gray-200 transition-colors"
            >
              {btn.label}
            </button>
          ))}
        </div>
      )}
      <div className="p-4 min-h-[300px] prose prose-sm max-w-none">
        <EditorContent editor={editor} />
      </div>
    </div>
  );
}
