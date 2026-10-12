import { redirect } from "next/navigation";
import { Shell } from "@/components/shell";
import { createClient } from "@/lib/supabase/server";

export default async function StudioLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const hasPassword = user.app_metadata?.provider === "email" && user.encrypted_password;
  
  if (!hasPassword) {
    redirect("/bienvenida");
  }

  const { data: profile } = await supabase
    .from("profiles")
    .select("role")
    .eq("user_id", user.id)
    .maybeSingle();

  return (
    <Shell email={user.email ?? ""} role={profile?.role ?? "member"}>
      {children}
    </Shell>
  );
}
