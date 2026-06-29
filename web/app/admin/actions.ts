"use server";

import { eq } from "drizzle-orm";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { db } from "@/db";
import { searches, users } from "@/db/schema";
import { validateNotify, validateSearch } from "@/lib/validate";

// Admin-only: every /admin/* POST goes through middleware's Basic Auth gate (see middleware.ts).
// On success the action redirects back to the entity's view page; on error it returns the
// messages for the edit form to render.
export type SaveState = { errors?: string[] } | null;

export async function updateUser(_prev: SaveState, formData: FormData): Promise<SaveState> {
  const id = Number(formData.get("userId"));
  const name = String(formData.get("name") ?? "");
  const channel = String(formData.get("channel") ?? "");
  const target = String(formData.get("target") ?? "");

  if (!Number.isInteger(id) || id <= 0) return { errors: ["Bad user id."] };
  const errors: string[] = [];
  if (!name.trim()) errors.push("Name is required.");
  errors.push(...validateNotify(channel, target));
  if (errors.length) return { errors };

  await db
    .update(users)
    .set({ name: name.trim(), notifyChannel: channel, notifyTarget: target.trim() })
    .where(eq(users.id, id));

  revalidatePath(`/admin/users/${id}`);
  redirect(`/admin/users/${id}`);
}

export async function updateSearch(_prev: SaveState, formData: FormData): Promise<SaveState> {
  const id = Number(formData.get("searchId"));
  const rawUrls = String(formData.get("urls") ?? "");
  const prompt = String(formData.get("prompt") ?? "");
  const filters = String(formData.get("filters") ?? "");
  const active = formData.get("active") === "on";

  if (!Number.isInteger(id) || id <= 0) return { errors: ["Bad search id."] };
  const { urls, errors } = validateSearch(rawUrls, prompt);
  if (errors.length) return { errors };

  await db
    .update(searches)
    .set({
      urls,
      preferencePrompt: prompt.trim(),
      excludeFilters: filters.split(",").map((w) => w.trim()).filter(Boolean),
      active,
    })
    .where(eq(searches.id, id));

  revalidatePath(`/admin/searches/${id}`);
  redirect(`/admin/searches/${id}`);
}
