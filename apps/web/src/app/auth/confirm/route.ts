import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import type { EmailOtpType } from "@supabase/supabase-js";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const site = process.env.NEXT_PUBLIC_SITE_URL ?? url.origin;
  const token_hash = url.searchParams.get("token_hash");
  const type = url.searchParams.get("type") as EmailOtpType | null;
  const next = url.searchParams.get("next") ?? "/";

  if (!token_hash || !type) {
    return NextResponse.redirect(`${site}/login?error=enlace`);
  }

  const supabase = await createClient();
  const { error } = await supabase.auth.verifyOtp({
    type,
    token_hash,
  });

  if (error) {
    const message = error.message.toLowerCase();
    const key =
      message.includes("email_not_allowed") || message.includes("database error")
        ? "invitacion"
        : "enlace";
    return NextResponse.redirect(`${site}/login?error=${key}`);
  }

  return NextResponse.redirect(`${site}${next}`);
}
