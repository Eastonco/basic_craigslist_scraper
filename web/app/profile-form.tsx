"use client";

import { useActionState } from "react";
import type { FormState, FormValues } from "./actions";

type Props = {
  action: (prev: FormState, formData: FormData) => Promise<FormState>;
  defaults: FormValues;
  submitLabel: string;
  showInvite?: boolean;
  token?: string;
};

export default function ProfileForm({ action, defaults, submitLabel, showInvite, token }: Props) {
  const [state, formAction] = useActionState(action, null);
  const v = state?.values ?? defaults; // repopulate with last submission on error

  return (
    <form action={formAction}>
      {state?.errors?.length ? (
        <div className="err">
          {state.errors.map((e, i) => (
            <div key={i}>{e}</div>
          ))}
        </div>
      ) : null}

      {token ? <input type="hidden" name="token" value={token} /> : null}

      {showInvite ? (
        <>
          <label>Invite code</label>
          <input name="invite" type="password" />
        </>
      ) : null}

      <label>Your name</label>
      <input name="name" defaultValue={v.name} />

      <label>Notify me via</label>
      <select name="channel" defaultValue={v.channel}>
        <option value="ntfy">ntfy (free push app)</option>
        <option value="sms">SMS (text message)</option>
        <option value="discord">Discord (webhook)</option>
      </select>

      <label>
        Notify target{" "}
        <span className="hint">
          ntfy topic (unguessable, subscribe in the ntfy app) — or +phone for SMS — or a Discord
          webhook URL
        </span>
      </label>
      <input name="target" defaultValue={v.target} />

      <label>
        Search URLs{" "}
        <span className="hint">
          one per line, from the Craigslist FREE section after you set your area/radius
        </span>
      </label>
      <textarea name="urls" defaultValue={v.urls} />

      <label>
        What are you looking for?{" "}
        <span className="hint">plain English — the AI judges each item against this</span>
      </label>
      <textarea name="prompt" defaultValue={v.prompt} />

      <label>
        Never alert me about{" "}
        <span className="hint">comma-separated words to hard-skip (optional)</span>
      </label>
      <input name="filters" defaultValue={v.filters} />

      <button type="submit">{submitLabel}</button>
    </form>
  );
}
