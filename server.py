"""Self-serve config UI. Friends visit, enter the invite code, and create a
profile (where to notify them + what free items they want). Each profile gets
an unguessable edit link to come back and tweak it.

Run:  uvicorn server:app --host 127.0.0.1 --port 8000
Expose it publicly with a Cloudflare named tunnel (see README).

Auth is deliberately minimal (friends-only, not productionized):
  - INVITE_CODE gates *creating* a profile.
  - an unguessable per-profile edit_token (in the URL) gates *editing* it.
# ponytail: no sessions/passwords. Upgrade to magic-link login if it outgrows
# a handful of friends.
"""
import datetime
import os
import re
import secrets as pysecrets
from contextlib import asynccontextmanager
from html import escape as h
from urllib.parse import urlparse

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import func, select

from db import get_engine_from_env
from models import Listing, ScraperStatus, Search, Session, User, init_db

load_dotenv()

INVITE_CODE = os.getenv("INVITE_CODE", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
engine = get_engine_from_env()
basic = HTTPBasic()


def require_admin(creds: HTTPBasicCredentials = Depends(basic)):
    # Separate, stronger gate than the friends' invite code: /admin exposes
    # everyone's notify targets. compare_digest avoids timing leaks.
    user_ok = pysecrets.compare_digest(creds.username, "admin")
    pass_ok = bool(ADMIN_PASSWORD) and pysecrets.compare_digest(creds.password, ADMIN_PASSWORD)
    if not (user_ok and pass_ok):
        raise HTTPException(status_code=401, detail="admin only",
                            headers={"WWW-Authenticate": "Basic"})
    return True


@asynccontextmanager
async def lifespan(app):
    init_db(engine)  # create tables on startup, not at import (keeps import DB-free)
    yield


app = FastAPI(lifespan=lifespan)

E164 = re.compile(r'^\+\d{7,15}$')
TOPIC_OK = re.compile(r'^[A-Za-z0-9_-]{3,64}$')


# --- validation (trust boundary: this form is public behind one shared code) ---

def validate(name, channel, target, urls_raw, prompt):
    urls = [u.strip() for u in urls_raw.splitlines() if u.strip()]
    errors = []
    if not name.strip():
        errors.append("Name is required.")
    if channel not in ("ntfy", "sms", "discord"):
        errors.append("Channel must be ntfy, sms, or discord.")
    if channel == "sms" and not E164.match(target.strip()):
        errors.append("SMS target must be an E.164 phone, e.g. +14155551234.")
    if channel == "ntfy" and not TOPIC_OK.match(target.strip()):
        errors.append("ntfy topic must be 3-64 chars: letters, numbers, _ or -.")
    if channel == "discord" and not target.strip().startswith("https://discord.com/api/webhooks/"):
        errors.append("Discord target must be a https://discord.com/api/webhooks/... URL.")
    if not urls:
        errors.append("At least one search URL is required.")
    for u in urls:
        host = (urlparse(u).hostname or "")
        # The scraper opens these in a real browser — only ever Craigslist.
        if not (u.startswith("http") and (host == "craigslist.org" or host.endswith(".craigslist.org"))):
            errors.append(f"Not a craigslist.org URL: {u}")
    if not prompt.strip():
        errors.append("Tell us what you're looking for.")
    return urls, errors


# --- HTML (inline, no template engine — ponytail) ---

def page(body: str) -> HTMLResponse:
    return HTMLResponse(f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Free Stuff Finder</title>
<style>
 body{{font:16px/1.5 system-ui,sans-serif;max-width:640px;margin:2rem auto;padding:0 1rem;color:#222}}
 label{{display:block;margin:1rem 0 .25rem;font-weight:600}}
 input,textarea,select{{width:100%;padding:.5rem;font:inherit;border:1px solid #bbb;border-radius:6px}}
 textarea{{min-height:5rem}} button{{margin-top:1.5rem;padding:.6rem 1.2rem;font:inherit;border:0;border-radius:6px;background:#5b21b6;color:#fff;cursor:pointer}}
 .err{{background:#fee;border:1px solid #f99;padding:.75rem;border-radius:6px;margin:1rem 0}}
 .ok{{background:#efe;border:1px solid #9c9;padding:.75rem;border-radius:6px;margin:1rem 0}}
 .hint{{color:#666;font-size:.85rem;font-weight:400}}
 table{{border-collapse:collapse;width:100%;margin:.5rem 0 1.5rem;font-size:.82rem}}
 th,td{{border:1px solid #ddd;padding:.35rem .5rem;text-align:left;vertical-align:top}}
 th{{background:#f3f0fa}}
 .badge{{display:inline-block;padding:.1rem .5rem;border-radius:4px;font-weight:600;font-size:.8rem}}
 .live{{background:#d8f5d8}} .stale{{background:#fdd}} .muted{{color:#888}}
</style></head><body>{body}</body></html>""")


def form_fields(name="", channel="ntfy", target="", urls="", prompt="", filters=""):
    sel = lambda c: "selected" if channel == c else ""
    # escape reflected values — user input must not break out of the markup
    return f"""
 <label>Your name</label><input name="name" value="{h(name)}">
 <label>Notify me via</label>
 <select name="channel">
   <option value="ntfy" {sel('ntfy')}>ntfy (free push app)</option>
   <option value="sms" {sel('sms')}>SMS (text message)</option>
   <option value="discord" {sel('discord')}>Discord (webhook)</option>
 </select>
 <label>Notify target <span class="hint">ntfy topic (unguessable, subscribe in the ntfy app) — or +phone for SMS — or a Discord webhook URL</span></label>
 <input name="target" value="{h(target)}">
 <label>Search URLs <span class="hint">one per line, from the Craigslist FREE section after you set your area/radius</span></label>
 <textarea name="urls">{h(urls)}</textarea>
 <label>What are you looking for? <span class="hint">plain English — the AI judges each item against this</span></label>
 <textarea name="prompt">{h(prompt)}</textarea>
 <label>Never alert me about <span class="hint">comma-separated words to hard-skip (optional)</span></label>
 <input name="filters" value="{h(filters)}">"""


@app.get("/", response_class=HTMLResponse)
def landing():
    return page(f"""
 <h1>🛋️ Free Stuff Finder</h1>
 <p>Create a profile and get pinged only about free Craigslist items you'd actually want.</p>
 <form method="post" action="/profile">
   <label>Invite code</label><input name="invite" type="password">
   {form_fields()}
   <button type="submit">Create my profile</button>
 </form>""")


@app.post("/profile", response_class=HTMLResponse)
def create_profile(invite: str = Form(""), name: str = Form(""), channel: str = Form("ntfy"),
                   target: str = Form(""), urls: str = Form(""), prompt: str = Form(""),
                   filters: str = Form("")):
    if not INVITE_CODE or invite != INVITE_CODE:
        return page('<div class="err">Wrong invite code.</div><p><a href="/">Back</a></p>')

    parsed_urls, errors = validate(name, channel, target, urls, prompt)
    if errors:
        body = '<h1>Fix these:</h1><div class="err">' + "<br>".join(errors) + '</div>'
        body += f'<form method="post" action="/profile"><label>Invite code</label><input name="invite" type="password">{form_fields(name, channel, target, urls, prompt, filters)}<button>Create my profile</button></form>'
        return page(body)

    excludes = [w.strip() for w in filters.split(",") if w.strip()]
    with Session(engine) as session:
        user = User(name=name.strip(), notify_channel=channel, notify_target=target.strip())
        session.add(user)
        session.flush()
        session.add(Search(user_id=user.id, urls=parsed_urls,
                           preference_prompt=prompt.strip(), exclude_filters=excludes))
        session.commit()
        token = user.edit_token
    return page(f"""<div class="ok">Profile created. You'll start getting alerts within a couple minutes.</div>
 <p><strong>Bookmark your private edit link:</strong><br>
 <a href="/profile/{token}">/profile/{token}</a></p>
 <p class="hint">Anyone with this link can edit your profile — keep it to yourself.</p>""")


@app.get("/profile/{token}", response_class=HTMLResponse)
def edit_form(token: str):
    with Session(engine) as session:
        user = session.scalar(select(User).where(User.edit_token == token))
        if not user:
            return page('<div class="err">Profile not found.</div>')
        search = session.scalar(select(Search).where(Search.user_id == user.id))
        urls = "\n".join(search.urls) if search else ""
        prompt = search.preference_prompt if search else ""
        filters = ", ".join(search.exclude_filters) if search else ""
    return page(f"""<h1>Edit profile</h1>
 <form method="post" action="/profile/{token}">
   {form_fields(user.name, user.notify_channel, user.notify_target, urls, prompt, filters)}
   <button type="submit">Save</button>
 </form>""")


@app.post("/profile/{token}")
def update_profile(token: str, name: str = Form(""), channel: str = Form("ntfy"),
                   target: str = Form(""), urls: str = Form(""), prompt: str = Form(""),
                   filters: str = Form("")):
    with Session(engine) as session:
        user = session.scalar(select(User).where(User.edit_token == token))
        if not user:
            return page('<div class="err">Profile not found.</div>')
        parsed_urls, errors = validate(name, channel, target, urls, prompt)
        if errors:
            return page('<div class="err">' + "<br>".join(errors) + f'</div><p><a href="/profile/{token}">Back</a></p>')
        search = session.scalar(select(Search).where(Search.user_id == user.id))
        user.name, user.notify_channel, user.notify_target = name.strip(), channel, target.strip()
        search.urls = parsed_urls
        search.preference_prompt = prompt.strip()
        search.exclude_filters = [w.strip() for w in filters.split(",") if w.strip()]
        session.commit()
    return RedirectResponse(f"/profile/{token}", status_code=303)


# --- admin dashboard (Basic Auth, read-only) ---

def _heartbeat_badge(status):
    if not status:
        return '<span class="badge stale">no heartbeat yet</span>'
    try:
        age = (datetime.datetime.now() - datetime.datetime.fromisoformat(status.last_cycle_at)).total_seconds()
    except Exception:
        age = None
    if age is not None and age < 180:
        return f'<span class="badge live">running</span> last cycle {int(age)}s ago · {status.cycle_count} cycles'
    return (f'<span class="badge stale">stale</span> last cycle {h(status.last_cycle_at)} '
            f'· {status.cycle_count} cycles')


@app.get("/admin", response_class=HTMLResponse)
def admin(_: bool = Depends(require_admin)):
    with Session(engine) as session:
        users = session.scalars(select(User)).all()
        searches = session.scalars(select(Search)).all()
        status = session.scalars(select(ScraperStatus)).first()
        n_listings = session.scalar(select(func.count()).select_from(Listing)) or 0
        labels = dict(session.execute(
            select(Listing.ai_label, func.count()).group_by(Listing.ai_label)).all())
        recent = session.scalars(select(Listing).order_by(Listing.id.desc()).limit(20)).all()
        users_by_id = {u.id: u for u in users}

        srows = []
        for s in searches:
            base = select(func.count()).select_from(Listing).where(Listing.search_id == s.id)
            total = session.scalar(base) or 0
            wants = session.scalar(base.where(Listing.ai_label == 'want')) or 0
            last = session.scalar(select(func.max(Listing.time_scraped)).where(Listing.search_id == s.id))
            srows.append((s, total, wants, last))

    owner = lambda uid: h(users_by_id[uid].name) if uid in users_by_id else f'#{uid}'
    want_n = labels.get('want', 0)
    skip_n = labels.get('skip', 0)
    base_n = labels.get(None, 0)

    body = ['<h1>⚙️ Admin</h1>']
    body.append(f'<p><strong>Scraper:</strong> {_heartbeat_badge(status)}</p>')
    body.append(f'<p><strong>Totals:</strong> {len(users)} users · {len(searches)} searches · '
                f'{n_listings} listings · <b>{want_n}</b> wanted · {skip_n} skipped · {base_n} baselined</p>')

    body.append('<h2>Searches</h2><table><tr><th>Owner</th><th>Notify</th><th>Wishlist</th>'
                '<th>Excludes</th><th>URLs</th><th>Active</th><th>Listings</th><th>Wanted</th>'
                '<th>Last scraped</th></tr>')
    for s, total, wants, last in srows:
        u = users_by_id.get(s.user_id)
        notify_cell = f'{h(u.notify_channel)} → {h(u.notify_target)}' if u else '—'
        urls_cell = "<br>".join(h(x) for x in s.urls)
        active = '<span class="badge live">yes</span>' if s.active else '<span class="badge stale">no</span>'
        body.append(
            f'<tr><td>{owner(s.user_id)}</td><td>{notify_cell}</td>'
            f'<td>{h(s.preference_prompt)}</td><td>{h(", ".join(s.exclude_filters))}</td>'
            f'<td>{urls_cell}</td><td>{active}</td><td>{total}</td><td><b>{wants}</b></td>'
            f'<td class="muted">{h(last or "—")}</td></tr>')
    body.append('</table>')

    body.append('<h2>Users &amp; notifications</h2><table><tr><th>Name</th><th>Channel</th>'
                '<th>Target</th><th>Created</th></tr>')
    for u in users:
        body.append(f'<tr><td>{h(u.name)}</td><td>{h(u.notify_channel)}</td>'
                    f'<td>{h(u.notify_target)}</td><td class="muted">{h(u.created_at)}</td></tr>')
    body.append('</table>')

    body.append('<h2>Recent classifications</h2><table><tr><th>When</th><th>Owner</th>'
                '<th>Verdict</th><th>Title</th><th>Reason</th></tr>')
    for l in recent:
        label = l.ai_label or 'baseline'
        cls = 'live' if l.ai_label == 'want' else 'stale' if l.ai_label == 'skip' else 'muted'
        score = f' {l.ai_score}' if l.ai_score is not None else ''
        body.append(
            f'<tr><td class="muted">{h(l.time_scraped or "")}</td><td>{owner(l.search_id)}</td>'
            f'<td><span class="badge {cls}">{h(label)}{score}</span></td>'
            f'<td><a href="{h(l.link)}">{h(l.title)}</a></td>'
            f'<td>{h(l.ai_reason or "")}</td></tr>')
    body.append('</table>')

    return page("\n".join(body))
