# IMPLEMENTATION_REPORT.md

## 1. Files Created

```
README.md
assets/hero.svg
assets/footer.svg
assets/generated/analytics.svg
assets/generated/contribution-animation.svg
scripts/generate_analytics.py
scripts/generate_contribution.py
.github/workflows/update-profile-assets.yml
docs/README_BEFORE_REDESIGN.md
docs/IMPLEMENTATION_NOTES.md
IMPLEMENTATION_REPORT.md   (this file)
```

## 2. Files Modified

None yet in your live repo — see §16, this package hasn't been pushed to `Neha501/Neha501` (I don't have write access to your GitHub account). Everything above is built and validated in this sandbox, ready for you to add.

## 3. Files Removed

None. The previous README is preserved unmodified at `docs/README_BEFORE_REDESIGN.md`.

## 4. Final README Structure

Hero → About Me → Tech Stack → Featured Projects → GitHub Activity → Contribution Runner → Coding Profiles → Connect With Me → Footer. Matches your locked section order exactly; no extra sections introduced.

## 5. Analytics Architecture

`scripts/generate_analytics.py` → fetches real data → composes one SVG (`assets/generated/analytics.svg`) with three non-overlapping rows:
1. Isometric contribution landscape (left) + activity radar (right)
2. Language donut + legend
3. Verified numeric readouts

Built entirely with Python standard library (`urllib`, `math`, `re`) — no external dependencies, so nothing to `pip install` in CI.

## 6. Data Sources (all real, verified at generation time)

| Metric | Source | Value used |
|---|---|---|
| Contribution calendar (365 days, per-day level 0–4) | `github.com/users/Neha501/contributions` (public HTML, no auth) | 342 days at level 0, 18 at level 1, 4 at level 2, 3 at level 3, 3 at level 4 |
| Total contributions (past year) | Same page | 72 |
| Repository list, stars, primary language | `api.github.com/users/Neha501/repos` | 10 non-fork repos (incl. profile repo), 7 total stars |
| PRs opened | `api.github.com/search/issues?q=author:Neha501+type:pr` | 1 |
| Issues opened | Same endpoint, `type:issue` | 0 |

No number on the panel was invented. Where a metric wasn't reliably obtainable (e.g., lifetime commit count), it was left out rather than estimated — see `docs/IMPLEMENTATION_NOTES.md` §5.

## 7. Isometric Contribution Logic

The public contribution calendar (365 daily cells) is grouped into 7-day weeks; the **maximum daily level within each week** sets that week's block color and height (taller/darker = more active week). Last 26 weeks are shown. This is a direct, real transformation of your actual GitHub contribution data — no synthetic blocks.

## 8. Language Donut Calculation

Repo-count of each **non-fork** repository's GitHub-reported primary language (the `language` field from the repos API), excluding the profile-README repo itself. Current real distribution: Python 3, Java 2, JavaScript 1, C++ 1, untagged/Other 2 (Power BI + Excel projects, which GitHub doesn't language-tag). This is coarser than a byte-weighted breakdown — documented honestly in `docs/IMPLEMENTATION_NOTES.md` §4, with an upgrade path noted.

## 9. Radar Normalization Formula

For each axis: `displayed_fraction = min(real_value / display_ceiling, 1.0)`.

Axes and ceilings used: Contributions (÷200), Repos (÷20), Stars (÷20), PRs opened (÷10). The ceiling is a fixed axis scale for display purposes only (like a chart's y-axis max) — it is not a data value and does not affect what real numbers are shown in the readouts row below the radar. Full rationale for which axes were included/excluded is in `docs/IMPLEMENTATION_NOTES.md` §5.

## 10. Contribution Animation Architecture

`scripts/generate_contribution.py` groups the same 365-day calendar into the last 20 weeks, takes each week's max activity level, and renders it as a "platform" whose height scales with that level. A small square character (`<g id="runner">`) follows an SMIL `<animateMotion>` path across the platform tops, looping over 14 seconds. This is an original composition — not the standard contribution-snake SVG re-skinned, and not the `czl9707` space-shooter.

## 11. GitHub Action Behavior

`.github/workflows/update-profile-assets.yml`:
- Runs daily at 03:17 UTC, and on-demand via `workflow_dispatch`
- Checks out the repo, sets up Python 3.12, runs both generator scripts (stdlib only, no pip install needed), commits changed SVGs back with `github-actions[bot]` as the author, and pushes
- If nothing changed, it skips the commit (`git diff --cached --quiet` check) rather than creating empty commits every day

## 12. Required Repository Permissions

`permissions: contents: write` at the workflow level — the minimum needed to commit regenerated assets back to the same repo, using the built-in `GITHUB_TOKEN` (no personal access token or repo secret required).

## 13. Manual Configuration Still Required

See the full checklist in `docs/IMPLEMENTATION_NOTES.md` §6. In short:
- Your real LinkedIn URL and email (Connect section currently has them commented out)
- Your LeetCode profile URL (Coding Profiles section currently has a placeholder note, no fake link)
- Confirmation on `AI_Study_Assistance` authorship, if you'd like it added back to Featured Projects

## 14. Unverified Links Intentionally Omitted

- Previous README's LinkedIn URL (`linkedin.com/in/neha-shit`) and email (`nehashit8@gmail.com`) — not published in the new README since I can't verify them against any account-level source; also not deleted anywhere, they remain visible in the backup file for your reference.
- No LeetCode link (none exists on the account).

## 15. Known Limitations

- **Language donut is repo-count-based, not byte-weighted** (see §8) — upgradeable once running with an authenticated token in CI, which lifts the rate limit that blocked the more granular calculation during this session.
- **GitHub's native `<table>` HTML can horizontal-scroll on narrow mobile widths** even with percentage-based cell widths — this is a platform-level GitHub Markdown limitation, not something CSS can fully override. The 2-column Featured Projects table is the one place this could show up; if you want zero risk of this on mobile, I can convert it to a stacked single-column layout instead (trade-off: less compact on desktop).
- **Commit and code-review counts aren't included** in the radar — not reliably obtainable from the public/unauthenticated API surface used here.
- The analytics panel was rendered and visually reviewed as a PNG during development to check for overlaps; final on-GitHub rendering should still be spot-checked once pushed, since GitHub's `<img>` sanitization/caching can occasionally behave differently from a local render.

## 16. How to Add This to Your Repository

I don't have write access to `github.com/Neha501/Neha501`, so you'll need to copy these files over yourself:

```bash
git clone https://github.com/Neha501/Neha501.git
cd Neha501
# copy in: README.md, assets/, scripts/, .github/, docs/, IMPLEMENTATION_REPORT.md
git add .
git commit -m "Redesign profile README: light-green theme, custom analytics, contribution runner"
git push
```

Then either wait for the next scheduled run, or trigger **Actions → Update profile assets → Run workflow** to regenerate the two SVGs with the freshest data right away.

## 17. How to Rollback

```bash
cp docs/README_BEFORE_REDESIGN.md README.md
git add README.md
git commit -m "Revert to previous README"
git push
```
The previous pink-themed README will be restored immediately; nothing about the redesign needs to be deleted for this to work.
