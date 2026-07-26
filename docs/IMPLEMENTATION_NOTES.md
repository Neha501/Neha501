# IMPLEMENTATION_NOTES.md

## 1. Contact links (LinkedIn / Email)

The previous README contained a LinkedIn URL and an email address. Per your correction, I am **not** characterizing them as jokes or placeholders — I have no way to confirm that one way or the other from public data alone.

What I *can* say factually: neither address is registered anywhere in your public GitHub account settings (no bio, no profile links), so I have no independent way to verify them. Rather than either (a) publishing them as-is without being able to confirm they're correct, or (b) inventing different ones, I've left them **out of the new README** and put commented-out placeholders in the "Connect With Me" section instead.

**To finish this section:** tell me your LinkedIn URL and the email you want listed, and I'll drop them in — verbatim, no changes.

## 2. LeetCode profile

Confirmed real: the `Leetcode_problems` repository is LeetHub-v2–synced and contains genuine solved problems across topics like String, Stack, Greedy, and Monotonic Stack. That proves activity — it does not give me a public profile URL to link to, since none is listed anywhere on the account.

**To finish this section:** send your LeetCode profile URL and I'll add the badge (no solved-count claims unless you also want me to compute those from the repo's topic lists, which I can do if you'd like).

## 3. AI_Study_Assistance — authorship

This repo has a real, working, deployed demo (`ai-study-assistance.vercel.app`), which is genuinely valuable to show off. It was held back from Featured Projects for one specific, checkable reason: its `README.md`'s clone instructions reference `github.com/Saumya552/Ai_study_assistance.git`, a different GitHub username, rather than `Neha501/AI_Study_Assistance`.

That is **not** proof of anything by itself — READMEs get copy-pasted, cloned starter templates keep old instructions, etc. — so I'm not asserting plagiarism or claiming it isn't your work. I just can't confidently represent it as an original project from public repository evidence alone, so per your instruction I substituted the strongest verified alternative (`Retail-Sales-Analytics-Dashboard`) instead.

**To resolve this:** if this is your own project (e.g., you started from a template, or the README wasn't updated after a rename), just confirm it and I'll swap it back into Featured Projects — it's a strong entry given the live demo.

## 4. Language-mix methodology (documented, not hidden)

The donut chart in the analytics panel is built from **repo-count of each non-fork repository's GitHub-detected primary language** (the `language` field from the GitHub repos API), not byte-weighted per-file analysis. The per-repo `/languages` byte-count endpoint was rate-limited during generation (unauthenticated calls are capped at 60/hour, and this session used many), so the script uses the field that's already present on the repo-list response instead — which is real, verified GitHub data, just coarser-grained than a byte-weighted breakdown.

In CI (via the GitHub Action, using the built-in `GITHUB_TOKEN`), the rate limit is 5,000/hour, effectively removing this constraint. **The script has an extension point to switch to byte-weighted calculation** if you'd like that level of precision — flag it and I'll implement it.

## 5. Radar chart axes and normalization

Axes used: **Contributions (past year), Public repositories, Stars earned, PRs opened.**

Axes considered and excluded, with reasons:
- **Followers** — real (currently 0), but a single zero-valued axis degenerates the radar shape rather than adding useful signal; can be added back if you'd like it shown as-is.
- **Issues opened** — verified at 0 via the GitHub Search API; excluded for the same reason as followers.
- **Commits (total)** — not reliably retrievable without an authenticated GraphQL call scoped to your account; the REST API doesn't expose a simple lifetime commit count. Can be added if you provide a token-based method you're comfortable with, or computed per-repo as an approximation.

**Normalization:** each axis is displayed as `min(real_value / ceiling, 1.0)`, where the ceiling is a fixed **display** scale (e.g., Contributions ceiling = 200/year) chosen so the chart is readable — this ceiling is not a data point, just an axis scale, the same way a bar chart needs a y-axis maximum. The real values feeding it are: Contributions = 72, Repos = 10, Stars = 7, PRs = 1 (all verified at generation time).

## 6. Manual configuration checklist

- [ ] Confirm real LinkedIn URL (then uncomment badge in Connect section of README)
- [ ] Confirm real contact email (then uncomment badge in Connect section of README)
- [ ] Provide LeetCode profile URL → add Coding Profiles section back to README with badge
- [ ] Confirm AI_Study_Assistance authorship → swap it into Featured Projects (strong entry given the live demo at ai-study-assistance.vercel.app)

**Note (2026-07):** The Coding Profiles section has been omitted from the public README pending a verified LeetCode profile URL. When available, add this section before the Connect section:

```markdown
## Coding Profiles

[![LeetCode](https://img.shields.io/badge/LeetCode-83B547?style=flat-square&logo=leetcode&logoColor=white)](YOUR_LEETCODE_URL_HERE)
```

## 7. How to regenerate assets manually

```bash
cd scripts
python3 generate_analytics.py --username Neha501 --out ../assets/generated/analytics.svg
python3 generate_contribution.py --username Neha501 --out ../assets/generated/contribution-animation.svg
```

Both scripts use only the Python standard library — no `pip install` needed.

Or trigger it without touching a terminal: go to the **Actions** tab → **Update profile assets** → **Run workflow**.
