"use server";

import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

export async function setPassword(formData: FormData) {
  const password = String(formData.get("password") ?? "").trim();
  const confirm = String(formData.get("confirm") ?? "").trim();

  if (password.length < 8) {
    redirect("/bienvenida?error=password");
  }

  if (password !== confirm) {
    redirect("/bienvenida?error=match");
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/bienvenida?error=session");
  }

  const { error } = await supabase.auth.updateUser({ password });

  if (error) {
    redirect("/bienvenida?error=update");
  }

  redirect("/");
}
