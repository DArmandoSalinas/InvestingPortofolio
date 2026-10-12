"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { apiSend } from "@/lib/api";

function fail(detail: string): never {
  redirect(`/admin/acceso?error=${encodeURIComponent(detail)}`);
}

async function rememberPassword(data: unknown) {
  if (!data || typeof data !== "object" || !("temporary_password" in data)) {
    return;
  }
  const password = String(data.temporary_password ?? "");
  const email = "email" in data ? String(data.email ?? "") : "";
  if (!password || !email) {
    return;
  }
  const jar = await cookies();
  jar.set("invite_flash", JSON.stringify({ email, password }), {
    httpOnly: true,
    sameSite: "lax",
    path: "/admin/acceso",
    maxAge: 180,
  });
}

export async function invite(formData: FormData) {
  const email = String(formData.get("email") ?? "")
    .trim()
    .toLowerCase();
  const role = formData.get("role") === "admin" ? "admin" : "member";
  const result = await apiSend("POST", "/admin/access", { email, role });
  if (!result.ok) {
    fail(result.detail);
  }
  await rememberPassword(result.data);
  revalidatePath("/admin/acceso");
  redirect(`/admin/acceso?enviado=${delivery(result.data)}`);
}

function delivery(data: unknown) {
  if (data && typeof data === "object" && "mail" in data) {
    if (data.mail === "smtp") {
      return "correo";
    }
    if (data.mail === "error") {
      return "error";
    }
  }
  return "local";
}

export async function resendLink(formData: FormData) {
  const email = String(formData.get("email") ?? "")
    .trim()
    .toLowerCase();
  const result = await apiSend("POST", "/admin/access/link", { email });
  if (!result.ok) {
    fail(result.detail);
  }
  await rememberPassword(result.data);
  revalidatePath("/admin/acceso");
  redirect(`/admin/acceso?enviado=${delivery(result.data)}`);
}

export async function updateAccess(formData: FormData) {
  const email = String(formData.get("email") ?? "").trim().toLowerCase();
  const role = formData.get("role");
  const active = formData.get("active");
  const body: { email: string; role?: "admin" | "member"; active?: boolean } = { email };
  if (role === "admin" || role === "member") {
    body.role = role;
  }
  if (active === "true" || active === "false") {
    body.active = active === "true";
  }
  const result = await apiSend("PATCH", "/admin/access", body);
  if (!result.ok) {
    fail(result.detail);
  }
  revalidatePath("/admin/acceso");
}
