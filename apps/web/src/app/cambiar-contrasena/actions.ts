"use server";

import { redirect } from "next/navigation";
import { apiSend } from "@/lib/api";
import { createClient } from "@/lib/supabase/server";

export async function savePassword(formData: FormData) {
  const password = String(formData.get("password") ?? "");
  const confirm = String(formData.get("confirm") ?? "");

  if (password !== confirm) {
    redirect("/cambiar-contrasena?error=distinta");
  }

  const result = await apiSend("POST", "/me/password", { password });
  if (!result.ok) {
    redirect(`/cambiar-contrasena?error=${encodeURIComponent(result.detail)}`);
  }

  const supabase = await createClient();
  await supabase.auth.signOut();
  redirect("/login?cambiada=1");
}
