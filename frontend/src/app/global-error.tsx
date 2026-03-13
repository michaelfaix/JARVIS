"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body className="dark bg-[#05080f] text-white font-mono flex items-center justify-center min-h-screen">
        <div className="text-center space-y-4">
          <h2 className="text-lg text-[#ff4466]">Something went wrong</h2>
          <p className="text-sm text-gray-400">{error.message}</p>
          <button
            onClick={reset}
            className="px-4 py-2 border border-[#4db8ff] text-[#4db8ff] rounded hover:bg-[#4db8ff]/10 transition-colors"
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}
