# News Bot 🗞️🤖

Fully automated X (Twitter) news bot. Reads RSS feeds, verifies hard news from
2+ sources, makes a clean graphic with source credit, and posts to X on a
schedule — runs 24/7 in the cloud (GitHub Actions), no PC needed.

## What it posts
5 pillars: Global news, US foreign policy, Afghanistan, World Cup 2026, Afghan cricket.

## Files
- `config.py` — feeds, posting limits, hashtags (edit this to tune behaviour)
- `main.py` — the bot brain
- `verify.py` — 2-source verification for hard news
- `graphics.py` — generates the news-card image
- `.github/workflows/post.yml` — the 24/7 schedule

## Cost
Pay-per-use X API: ~$0.015 per post (text/image), ~$0.20 if a post has a link.
At a few posts/day this is roughly **$2–8/month**. Auto-recharge stays OFF.

## One-time setup
1. **X API keys** — create an App at https://developer.x.com (set permissions
   to *Read and Write*). Grab: API Key, API Secret, Access Token, Access Token Secret.
2. **Push this folder to a private GitHub repo.**
3. **Add the 4 keys as GitHub Secrets** (repo → Settings → Secrets and variables →
   Actions → New repository secret):
   - `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`
4. **Test:** repo → Actions tab → "News Bot" → *Run workflow* (manual run).
5. If the test post looks good, the schedule takes over automatically.

## Safety
- Never follows/DMs/likes — only posts. (Avoids spam bans.)
- Hard news needs 2 sources before posting.
- Credits every source. Posts unique content only.
