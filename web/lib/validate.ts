// Trust boundary: the create/edit form is public behind one shared invite code.
// Direct port of validate() in server.py.
const E164 = /^\+\d{7,15}$/;
const TOPIC_OK = /^[A-Za-z0-9_-]{3,64}$/;

export type ProfileInput = {
  name: string;
  channel: string;
  target: string;
  urls: string; // raw textarea, one per line
  prompt: string;
};

export function validate(input: ProfileInput): { urls: string[]; errors: string[] } {
  const urls = input.urls.split(/\r?\n/).map((u) => u.trim()).filter(Boolean);
  const errors: string[] = [];
  const target = input.target.trim();

  if (!input.name.trim()) errors.push("Name is required.");
  if (!["ntfy", "sms", "discord"].includes(input.channel))
    errors.push("Channel must be ntfy, sms, or discord.");
  if (input.channel === "sms" && !E164.test(target))
    errors.push("SMS target must be an E.164 phone, e.g. +14155551234.");
  if (input.channel === "ntfy" && !TOPIC_OK.test(target))
    errors.push("ntfy topic must be 3-64 chars: letters, numbers, _ or -.");
  if (input.channel === "discord" && !target.startsWith("https://discord.com/api/webhooks/"))
    errors.push("Discord target must be a https://discord.com/api/webhooks/... URL.");
  if (urls.length === 0) errors.push("At least one search URL is required.");

  for (const u of urls) {
    let host = "";
    try {
      host = new URL(u).hostname;
    } catch {
      /* invalid URL -> caught by the craigslist check below */
    }
    // The scraper opens these in a real browser — only ever Craigslist.
    if (!(u.startsWith("http") && (host === "craigslist.org" || host.endsWith(".craigslist.org"))))
      errors.push(`Not a craigslist.org URL: ${u}`);
  }
  if (!input.prompt.trim()) errors.push("Tell us what you're looking for.");

  return { urls, errors };
}
