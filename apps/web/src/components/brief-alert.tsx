"use client";

import { useState } from "react";
import { savePushSubscription } from "@/app/(studio)/resumen/actions";

function keyBytes(value: string) {
  const padded = value.replace(/-/g, "+").replace(/_/g, "/") + "=".repeat((4 - (value.length % 4)) % 4);
  const raw = atob(padded);
  return Uint8Array.from(raw, (char) => char.charCodeAt(0));
}

export function BriefAlert({ publicKey }: { publicKey: string }) {
  const [label, setLabel] = useState("Avisarme cuando salga");
  if (!publicKey) {
    return null;
  }

  async function enable() {
    try {
      if (!("Notification" in window) || !("serviceWorker" in navigator)) {
        setLabel("Este navegador no recibe avisos");
        return;
      }
      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        setLabel("El aviso quedó bloqueado en el navegador");
        return;
      }
      const registration = await navigator.serviceWorker.register("/sw.js");
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: keyBytes(publicKey),
      });
      const json = subscription.toJSON();
      const result = await savePushSubscription({
        endpoint: json.endpoint,
        keys: { p256dh: json.keys?.p256dh, auth: json.keys?.auth },
      });
      setLabel(result.ok ? "Aviso activado" : result.detail);
    } catch {
      setLabel("No se pudo activar el aviso");
    }
  }

  return (
    <button
      type="button"
      onClick={enable}
      className="w-fit rounded-full border border-line px-5 py-2.5 text-sm text-ink"
    >
      {label}
    </button>
  );
}
