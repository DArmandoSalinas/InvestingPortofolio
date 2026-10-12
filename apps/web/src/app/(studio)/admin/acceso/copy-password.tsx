"use client";

export function CopyPasswordButton({ password }: { password: string }) {
  return (
    <button
      onClick={(e) => {
        e.preventDefault();
        navigator.clipboard.writeText(password);
      }}
      className="rounded-full border border-line px-3 py-1.5 text-xs text-muted hover:text-ink"
    >
      Copiar
    </button>
  );
}
