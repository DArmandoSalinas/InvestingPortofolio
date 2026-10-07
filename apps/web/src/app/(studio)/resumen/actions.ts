"use server";

import { apiSend } from "@/lib/api";

export async function savePushSubscription(subscription: {
  endpoint?: string;
  keys?: { p256dh?: string; auth?: string };
}) {
  const result = await apiSend("POST", "/push/subscriptions", subscription);
  if (!result.ok) {
    return { ok: false as const, detail: result.detail };
  }
  return { ok: true as const, detail: "" };
}
