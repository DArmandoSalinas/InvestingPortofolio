"use server";

import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

function siteUrl() {
  return process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
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
    redirect("/login?error=envio");
  }

  redirect("/login?sent=1");
}

export async function continueWithGoogle() {
  const supabase = await createClient();
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: {
      redirectTo: `${siteUrl()}/auth/callback`,
      skipBrowserRedirect: true,
    },
  });

  if (error || !data.url) {
    redirect("/login?error=google");
  }

  redirect(data.url);
}
