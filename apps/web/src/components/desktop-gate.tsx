export function DesktopGate() {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black px-8 min-[1280px]:hidden">
      <p className="max-w-sm text-center text-2xl font-light leading-snug tracking-tight text-ink">
        Esta plataforma está hecha para pantallas de escritorio, de 1280px en adelante.
      </p>
    </div>
  );
}
