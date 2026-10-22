export default function OfflinePage() {
  return (
    <div className="flex min-h-[70dvh] flex-col items-center justify-center px-6 text-center">
      <span aria-hidden className="text-4xl">
        ⚡
      </span>
      <h1 className="mt-4 text-xl font-semibold text-slate-100">You are offline</h1>
      <p className="mt-2 max-w-sm text-sm leading-relaxed text-slate-400">
        Captures you take while offline are stored on this device and uploaded automatically when
        the connection returns. Nothing is lost.
      </p>
    </div>
  );
}
