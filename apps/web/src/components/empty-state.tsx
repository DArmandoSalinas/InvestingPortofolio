export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-[24px] border border-dashed border-line bg-surface/60 px-6 py-10 sm:px-8">
      <p className="text-lg font-light tracking-tight">{title}</p>
      <p className="mt-3 max-w-lg text-sm leading-6 text-muted">{body}</p>
    </div>
  );
}
