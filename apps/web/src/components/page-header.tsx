import { FadeIn } from "@/components/fade-in";

export function PageHeader({
  eyebrow,
  title,
  description,
  meta,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  meta?: React.ReactNode;
}) {
  return (
    <FadeIn>
      <header className="flex flex-col gap-3 border-b border-line pb-8">
        {eyebrow ? (
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-accent">{eyebrow}</p>
        ) : null}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="max-w-2xl">
            <h1 className="text-4xl font-light tracking-tight sm:text-5xl">{title}</h1>
            {description ? (
              <p className="mt-3 text-sm leading-6 text-muted">{description}</p>
            ) : null}
          </div>
          {meta ? <div className="shrink-0 text-sm text-muted">{meta}</div> : null}
        </div>
      </header>
    </FadeIn>
  );
}
