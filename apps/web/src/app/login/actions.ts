"use server";

import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

function siteUrl() {
  return process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
}

export async function signInWithPassword(formData: FormData) {
  const email = String(formData.get("email") ?? "")
    .trim()
    .toLowerCase();
  const password = String(formData.get("password") ?? "");

  if (!email.includes("@")) {
    redirect("/login?error=correo");
  }

  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    const message = error.message.toLowerCase();
    if (message.includes("email_not_allowed") || message.includes("database error")) {
      redirect("/login?error=invitacion");
    }
    if (message.includes("invalid") || message.includes("credentials")) {
      redirect("/login?error=credentials");
    }
    redirect("/login?error=credentials");
  }

  redirect("/");
}

export async function resetPassword(formData: FormData) {
  const email = String(formData.get("email") ?? "")
    .trim()
    .toLowerCase();

  if (!email || !email.includes("@")) {
    redirect("/login?error=correo");
  }

  const supabase = await createClient();
  const { error } = await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${siteUrl()}/auth/callback?next=/bienvenida`,
  });

  if (error) {
    const message = error.message.toLowerCase();
    if (message.includes("email_not_allowed") || message.includes("database error")) {
      redirect("/login?error=invitacion");
    }
  }

  redirect("/login?sent=1");
}

export async function sendLink(formData: FormData) {
  const email = String(formData.get("email") ?? "")
    .trim()
    .toLowerCase();

  if (!email.includes("@")) {
    redirect("/login?error=correo");
  }

  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithOtp({
    email,
    options: { emailRedirectTo: `${siteUrl()}/auth/callback` },
  });

  if (error) {
    const message = error.message.toLowerCase();
    if (message.includes("email_not_allowed") || message.includes("database error")) {
      redirect("/login?error=invitacion");
    }
  }

  redirect("/login?sent=1");
}
