// Self-check for the pure pickup-message helpers. No framework — run with:
//   npx tsx app/admin/listings/draft.test.ts   (or `npm test`)
import assert from "node:assert";

import { buildPrompt, extractPostingBody, prettyPhone } from "./draft";

// prettyPhone: drops +1 and formats US numbers; leaves odd shapes alone.
assert.strictEqual(prettyPhone("+12069531234"), "(206)-953-1234");
assert.strictEqual(prettyPhone("2069531234"), "(206)-953-1234");
assert.strictEqual(prettyPhone("+447911123456"), "+447911123456"); // non-US untouched

// buildPrompt: includes the key fields when present...
const full = buildPrompt({
  name: "Jo",
  phone: "+14155551234",
  note: "have a truck",
  title: "Free oak desk",
  location: "Ballard",
  description: "Solid oak, some scratches.",
});
assert.match(full, /Free oak desk/);
assert.match(full, /\(415\)-555-1234/);
assert.doesNotMatch(full, /\+1/); // +1 dropped
assert.match(full, /have a truck/);
assert.match(full, /Solid oak/);
assert.match(full, /pick it up today/);

// ...and omits the phone line cleanly when there's no phone or description.
const bare = buildPrompt({ name: "Jo", phone: "", note: "", title: "Free chair", location: "", description: "" });
assert.doesNotMatch(bare, /text me at/i);
assert.match(bare, /no phone number to share/);
assert.match(bare, /no description available/);

// extractPostingBody: pulls and cleans the section...
const html = `<div><section id="postingbody"><div class="print-qrcode">QR Code Link to This Post</div>Comfy couch,<br>free to a good home &amp; pet-free.</section></div>`;
const body = extractPostingBody(html);
assert.match(body, /Comfy couch/);
assert.match(body, /free to a good home & pet-free/);
assert.doesNotMatch(body, /QR Code/);

// ...and returns "" when the section is absent.
assert.strictEqual(extractPostingBody("<html><body>no body here</body></html>"), "");

console.log("draft helpers ok");
