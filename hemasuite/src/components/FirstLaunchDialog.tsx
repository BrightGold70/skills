export function FirstLaunchDialog({ onDismiss }: { onDismiss: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-lg p-6 max-w-md text-white space-y-4">
        <h2 className="text-xl font-semibold">Welcome to HemaSuite</h2>
        <p className="text-slate-300 text-sm">
          If macOS showed a security warning when opening this app,
          right-click the app icon and select <strong>Open</strong>,
          then click <strong>Open</strong> in the dialog.
        </p>
        <p className="text-slate-400 text-xs">
          This only needs to be done once. Future launches will work normally.
        </p>
        <button
          onClick={onDismiss}
          className="w-full bg-blue-600 hover:bg-blue-700 rounded px-4 py-2 text-sm font-medium"
        >
          Got it
        </button>
      </div>
    </div>
  );
}
