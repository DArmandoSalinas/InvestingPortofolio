import Link from "next/link";

export function ScoreChart({
  title,
  rows,
}: {
  title: string;
  rows: { key: string; label: string; href?: string; value: number | null }[];
}) {
  const drawn = rows.filter((row) => row.value !== null);
  if (drawn.length === 0) {
    return null;
  }

  return (
    <section className="rounded-[24px] border border-line bg-surface px-5 py-6 sm:px-6">
      <h2 className="text-[11px] uppercase tracking-[0.14em] text-faint">{title}</h2>
      <div className="mt-5 flex flex-col gap-3">
        {drawn.map((row) => {
          const value = row.value ?? 0;
          const label = (
            <span className="truncate text-sm tracking-wide">{row.label}</span>
          );
          return (
            <div
              key={row.key}
              className="grid grid-cols-[5.5rem_1fr_2.5rem] items-center gap-3 sm:grid-cols-[7.5rem_1fr_2.5rem]"
            >
              {row.href ? (
                <Link href={row.href} className="truncate hover:text-accent">
                  {label}
                </Link>
              ) : (
                label
              )}
              <div className="h-2 overflow-hidden rounded-full bg-raised">
                <div
                  className="h-2 rounded-full bg-accent"
                  style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
                />
              </div>
              <span className="text-right text-sm tabular-nums text-muted">{value}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
