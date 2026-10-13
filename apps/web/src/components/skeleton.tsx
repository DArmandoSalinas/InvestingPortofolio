export function SkeletonBlock({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-2xl bg-raised ${className}`} />;
}

export function PageSkeleton() {
  return (
    <div className="flex flex-col gap-8" aria-busy="true" aria-label="Cargando">
      <SkeletonBlock className="h-10 w-48" />
      <SkeletonBlock className="h-4 w-72" />
      <SkeletonBlock className="h-40 w-full" />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <SkeletonBlock className="h-28" />
        <SkeletonBlock className="h-28" />
        <SkeletonBlock className="h-28" />
      </div>
    </div>
  );
}
