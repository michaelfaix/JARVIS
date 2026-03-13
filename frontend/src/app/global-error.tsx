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
      <body style={{ margin: 0, background: "#05080f", color: "#fff", fontFamily: "monospace", display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
        <div style={{ textAlign: "center" }}>
          <h2 style={{ fontSize: 18, color: "#ff4466" }}>Kritischer Fehler</h2>
          <p style={{ fontSize: 14, color: "#888", marginTop: 8 }}>{error.message}</p>
          <button
            onClick={reset}
            style={{
              marginTop: 16,
              padding: "8px 16px",
              border: "1px solid #4db8ff",
              color: "#4db8ff",
              background: "transparent",
              borderRadius: 4,
              cursor: "pointer",
              fontFamily: "monospace",
            }}
          >
            Neu laden
          </button>
        </div>
      </body>
    </html>
  );
}
