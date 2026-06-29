import { and, count, desc, eq, max } from "drizzle-orm";

import { db } from "@/db";
import { listings, scraperStatus, searches, users } from "@/db/schema";

export const dynamic = "force-dynamic"; // always read live data, never prerender

type Status = typeof scraperStatus.$inferSelect;

function HeartbeatBadge({ status }: { status: Status | undefined }) {
  if (!status) return <span className="badge stale">no heartbeat yet</span>;
  const age = (Date.now() - new Date(status.lastCycleAt).getTime()) / 1000;
  if (Number.isFinite(age) && age < 180)
    return (
      <>
        <span className="badge live">running</span> last cycle {Math.floor(age)}s ago ·{" "}
        {status.cycleCount} cycles
      </>
    );
  return (
    <>
      <span className="badge stale">stale</span> last cycle {status.lastCycleAt} ·{" "}
      {status.cycleCount} cycles
    </>
  );
}

export default async function Admin() {
  const usersList = await db.select().from(users);
  const searchesList = await db.select().from(searches);
  const [status] = await db.select().from(scraperStatus).limit(1);
  const [{ nListings }] = await db.select({ nListings: count() }).from(listings);
  const labelRows = await db
    .select({ label: listings.aiLabel, n: count() })
    .from(listings)
    .groupBy(listings.aiLabel);
  const recent = await db.select().from(listings).orderBy(desc(listings.id)).limit(20);

  const usersById = new Map(usersList.map((u) => [u.id, u]));
  const owner = (uid: number) => usersById.get(uid)?.name ?? `#${uid}`;
  const labels = Object.fromEntries(labelRows.map((r) => [r.label ?? "baseline", r.n]));
  const wantN = labels["want"] ?? 0;
  const skipN = labels["skip"] ?? 0;
  const baseN = labels["baseline"] ?? 0;

  const srows = await Promise.all(
    searchesList.map(async (s) => {
      const [{ total }] = await db
        .select({ total: count() })
        .from(listings)
        .where(eq(listings.searchId, s.id));
      const [{ wants }] = await db
        .select({ wants: count() })
        .from(listings)
        .where(and(eq(listings.searchId, s.id), eq(listings.aiLabel, "want")));
      const [{ last }] = await db
        .select({ last: max(listings.timeScraped) })
        .from(listings)
        .where(eq(listings.searchId, s.id));
      return { s, total, wants, last };
    }),
  );

  return (
    <>
      <h1>Admin</h1>
      <p className="status">
        <strong>Scraper:</strong> <HeartbeatBadge status={status} />
      </p>

      <div className="stats">
        <div className="stat">
          <div className="stat__num">{usersList.length}</div>
          <div className="stat__label">Users</div>
        </div>
        <div className="stat">
          <div className="stat__num">{searchesList.length}</div>
          <div className="stat__label">Searches</div>
        </div>
        <div className="stat">
          <div className="stat__num">{nListings}</div>
          <div className="stat__label">Listings</div>
        </div>
        <div className="stat stat--good">
          <div className="stat__num">{wantN}</div>
          <div className="stat__label">Wanted</div>
        </div>
        <div className="stat">
          <div className="stat__num">{skipN}</div>
          <div className="stat__label">Skipped</div>
        </div>
        <div className="stat">
          <div className="stat__num">{baseN}</div>
          <div className="stat__label">Baselined</div>
        </div>
      </div>

      <h2>Searches</h2>
      <div className="table-wrap">
      <table>
        <tbody>
          <tr>
            <th>Owner</th>
            <th>Notify</th>
            <th>Wishlist</th>
            <th>Excludes</th>
            <th>URLs</th>
            <th>Active</th>
            <th>Listings</th>
            <th>Wanted</th>
            <th>Last scraped</th>
          </tr>
          {srows.map(({ s, total, wants, last }) => {
            const u = usersById.get(s.userId);
            return (
              <tr key={s.id}>
                <td>{owner(s.userId)}</td>
                <td>{u ? `${u.notifyChannel} → ${u.notifyTarget}` : "—"}</td>
                <td>{s.preferencePrompt}</td>
                <td>{s.excludeFilters.join(", ")}</td>
                <td>
                  {s.urls.map((x, i) => (
                    <div key={i}>{x}</div>
                  ))}
                </td>
                <td>
                  {s.active ? (
                    <span className="badge live">yes</span>
                  ) : (
                    <span className="badge stale">no</span>
                  )}
                </td>
                <td>{total}</td>
                <td>
                  <b>{wants}</b>
                </td>
                <td className="muted">{last || "—"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      </div>

      <h2>Users &amp; notifications</h2>
      <div className="table-wrap">
      <table>
        <tbody>
          <tr>
            <th>Name</th>
            <th>Channel</th>
            <th>Target</th>
            <th>Created</th>
          </tr>
          {usersList.map((u) => (
            <tr key={u.id}>
              <td>{u.name}</td>
              <td>{u.notifyChannel}</td>
              <td>{u.notifyTarget}</td>
              <td className="muted">{u.createdAt}</td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>

      <h2>Recent classifications</h2>
      <div className="table-wrap">
      <table>
        <tbody>
          <tr>
            <th>When</th>
            <th>Owner</th>
            <th>Verdict</th>
            <th>Title</th>
            <th>Reason</th>
          </tr>
          {recent.map((l) => {
            const label = l.aiLabel ?? "baseline";
            const cls = l.aiLabel === "want" ? "live" : l.aiLabel === "skip" ? "stale" : "muted";
            const score = l.aiScore != null ? ` ${l.aiScore}` : "";
            return (
              <tr key={l.id}>
                <td className="muted">{l.timeScraped || ""}</td>
                <td>{owner(l.searchId)}</td>
                <td>
                  <span className={`badge ${cls}`}>
                    {label}
                    {score}
                  </span>
                </td>
                <td>
                  <a href={l.link}>{l.title}</a>
                </td>
                <td>{l.aiReason || ""}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      </div>
    </>
  );
}
