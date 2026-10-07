import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

export async function proxy(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
          supabaseResponse = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) => {
            supabaseResponse.cookies.set(name, value, options);
          });
        },
      },
    },
  );

  const {
    data: { user },
  } = await supabase.auth.getUser();

  const path = request.nextUrl.pathname;
  const isPublic = path === "/login" || path.startsWith("/auth/");

  const redirectTo = (pathname: string, error?: string) => {
    const url = request.nextUrl.clone();
    url.pathname = pathname;
    url.search = "";
    if (error) {
      url.searchParams.set("error", error);
    }
    const redirect = NextResponse.redirect(url);
    supabaseResponse.cookies.getAll().forEach((cookie) => {
      redirect.cookies.set(cookie);
    });
    return redirect;
  };

  if (!user && !isPublic) {
    return redirectTo("/login");
  }

  if (user) {
    const { data: profile } = await supabase
      .from("profiles")
      .select("role, active")
      .eq("user_id", user.id)
      .maybeSingle();

    if (!profile || !profile.active) {
      await supabase.auth.signOut();
      return redirectTo("/login", profile ? "revocado" : "invitacion");
    }

    if (path.startsWith("/admin") && profile.role !== "admin") {
      return redirectTo("/");
    }

    if (path === "/login") {
      return redirectTo("/");
    }
  }

  return supabaseResponse;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)"],
};
