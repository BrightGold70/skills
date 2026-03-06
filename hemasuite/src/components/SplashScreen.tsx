export function SplashScreen() {
  return (
    <div className="flex h-screen items-center justify-center bg-slate-900 text-white">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold tracking-wide">HemaSuite</h1>
        <p className="text-slate-400 text-lg">Clinical Research Suite</p>
        <div role="status" className="flex justify-center pt-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-600 border-t-blue-400" />
        </div>
        <p className="text-slate-500 text-sm">Starting up...</p>
      </div>
    </div>
  );
}
