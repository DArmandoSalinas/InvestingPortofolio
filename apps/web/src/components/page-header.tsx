interface PageHeaderProps {
  title: string;
  description: string;
  subtitle?: string;
}

export function PageHeader({ title, description, subtitle }: PageHeaderProps) {
  return (
    <div>
      <h1 className="text-5xl font-light tracking-tight">{title}</h1>
      <p className="mt-2 text-sm leading-6 text-muted">{description}</p>
      {subtitle && <p className="mt-3 text-sm text-faint">{subtitle}</p>}
    </div>
  );
}
