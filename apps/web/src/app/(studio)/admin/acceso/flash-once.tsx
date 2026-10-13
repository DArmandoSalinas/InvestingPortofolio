"use client";

import { useEffect } from "react";
import { clearInviteFlash } from "./actions";

/** Borra la cookie flash tras el primer paint para no re-mostrar la contraseña. */
export function FlashOnce() {
  useEffect(() => {
    void clearInviteFlash();
  }, []);
  return null;
}
