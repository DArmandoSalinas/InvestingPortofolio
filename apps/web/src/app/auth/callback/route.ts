import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { safeRedirect } from "@/lib/redirect";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const site = process.env.NEXT_PUBLIC_SITE_URL ?? url.origin;
  const code = url.searchParams.get("code");

  if (!code) {
    return NextResponse.redirect(`${site}/login?error=enlace`);
  }

  const supabase = await createClient();
  const { error } = await supabase.auth.exchangeCodeForSession(code);

  if (error) {
    const message = error.message.toLowerCase();
    const key =
      message.includes("email_not_allowed") || message.includes("database error")
        ? "invitacion"
        : "enlace";
    return NextResponse.redirect(`${site}/login?error=${key}`);
  }

  const next = safeRedirect(url.searchParams.get("next"));
  return NextResponse.redirect(`${site}${next}`);
}
