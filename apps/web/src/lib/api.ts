import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

async function authorizedFetch(path: string, init: RequestInit = {}) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!user || !session) {
    redirect("/login");
  }

  let response: Response;
  try {
    response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${path}`, {
      ...init,
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        "Content-Type": "application/json",
        ...(init.headers ?? {}),
      },
      cache: "no-store",
    });
  } catch {
    return { ok: false as const, status: 503, detail: "La API no responde", data: null };
  }

  if (response.status === 401) {
    redirect("/login");
  }

  const data = await response.json().catch(() => null);
  const detail =
    data && typeof data === "object" && "detail" in data && typeof data.detail === "string"
      ? data.detail
      : "No se pudo completar la acción";

  if (!response.ok) {
    return { ok: false as const, status: response.status, detail, data };
  }

  return { ok: true as const, status: response.status, detail: "", data };
}

export async function apiGetResult<T>(path: string) {
  return authorizedFetch(path) as Promise<
    { ok: true; status: number; detail: string; data: T } | { ok: false; status: number; detail: string; data: null }
  >;
}

export async function apiGet<T>(path: string): Promise<T> {
  const result = await authorizedFetch(path);
  if (!result.ok) {
    throw new Error(result.detail);
  }
  return result.data as T;
}

export async function apiSend(
  method: "POST" | "PATCH" | "PUT" | "DELETE",
  path: string,
  body?: unknown,
) {
  return authorizedFetch(path, {
    method,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}
