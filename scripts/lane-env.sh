#!/usr/bin/env bash
# Fetch the lane's database URL ONCE, then run every script locally.
#
# ⭐ WHY THIS EXISTS. `railway run <cmd>` performs a NETWORK ROUND-TRIP to fetch
# environment variables on EVERY invocation. A measurement lane that runs forty
# scripts makes forty fetches. Under that repetition the CLI degrades: a healthy
# call returns in ~1.5s, but a burst of twelve hung past ten minutes, and two
# lanes died with
#
#     Failed to fetch: error decoding response body
#       expected ident at line 1 column 2
#
# — the CLI receiving a non-JSON body where JSON was expected, which is what an
# upstream error page or a rate-limit response looks like to a JSON decoder.
#
# ⭐ THE FIX IS THE USAGE PATTERN, WHICH IS THE LAYER WE CONTROL. One fetch per
# lane, N local runs. We cannot repair Railway's API; we can stop calling it
# once per query.
#
#   source scripts/lane-env.sh          # once, at the top of a lane
#   python3 scripts/<whatever>.py       # then plain python3, no railway run
#
# ⭐ THE URL IS NEVER PRINTED. It carries a password. It is exported into the
# shell and nothing echoes it — `set -x` is deliberately not used here.

_lane_url="$(railway variables --service Postgres --kv 2>/dev/null \
             | sed -n 's/^DATABASE_PUBLIC_URL=//p' | head -1)"

if [ -z "$_lane_url" ]; then
  echo "lane-env: could not fetch DATABASE_PUBLIC_URL from the Postgres service." >&2
  echo "          The CLI may be degraded — retry once, then stop rather than" >&2
  echo "          substituting. An unreliable instrument has cost three lanes." >&2
  unset _lane_url
  return 1 2>/dev/null || exit 1
fi

export DATABASE_PUBLIC_URL="$_lane_url"
unset _lane_url
echo "lane-env: DATABASE_PUBLIC_URL exported (value not printed). One fetch, N local runs."
