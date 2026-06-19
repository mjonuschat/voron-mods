# Migrate from Hugo/Doks to Astro/Starlight

## Goal

Replace the current Hugo + Doks site with an Astro + Starlight site, deployed the same way (GitHub Pages via Actions, triggered on push to `gh-pages`), with the same content, reorganized only where the framework switch requires it.

## Why

Two concrete problems with the current stack, not just a preference for something newer:

- **Local dev toolchain juggling.** Running the site locally means a Hugo binary, a separately-installed Dart Sass compiler, and Node/npm, each managed independently. The GitHub Actions workflow installs Dart Sass via `snap`, which doesn't exist on macOS, so the local toolchain can never exactly mirror CI.
- **Version drift between environments.** `netlify.toml` pins `HUGO_VERSION = "0.125.1"`. `.github/workflows/deploy.yml` pins `HUGO_VERSION: 0.128.0`. Whatever's installed locally is a third, uncoordinated version. Nothing forces these to match.
- **The Doks theme is stale.** `@hyas/doks-core`'s last npm publish was `1.6.1` on 2024-04-23 — over two years before this migration. Not archived, but no evidence of active maintenance either.

Astro + Starlight is 100% npm/Node-native: one `npm install`, every tool version pinned in `package-lock.json`, no out-of-band binaries. This fixes both the toolchain and version-drift problems directly, and Starlight is actively maintained by the Astro core team (unlike Doks).

## Alternatives Considered

**VitePress** and **Docusaurus** were both viable — same npm-native build, same problem fixed. Starlight was picked as the closest match to Doks' shape (sidebar nav, search, content-collections-driven docs) without Docusaurus's React-SPA weight or VitePress's more manual sidebar/theming setup.

**Theme**: stock Starlight, not a community theme. Two candidates were evaluated for the "narrow default content width" complaint specifically:

- **Ion** (`louisescher/starlight-ion-theme`) — 2 years old, 70 stars, steady release cadence (v2.2.3 → v2.4.0 over 12 months). Solves width by overriding `.sl-container`'s `max-width` directly.
- **Page** (`pelagornis/starlight-theme-page`, npm `@pelagornis/page`) — ~1 year old, 15 stars. Solves width by hiding Starlight's default content/sidebar markup entirely and rebuilding it full-width.

Both are real and currently maintained, not abandoned. Neither was picked — going stock keeps the dependency surface smallest, and the width complaint has a clean fix that doesn't require a third-party theme (see below).

## Scope

**Whole site**, not just `docs/guides/`. Current content outside the guides is tiny: `content/_index.md` (13 lines, homepage), `content/docs/_index.md` (15), `content/docs/resources.md` (17), `content/privacy.md` (14) — 59 lines total. Running two site generators for one stub homepage isn't worth the complexity of a partial migration.

**Drop the blog/categories/contributors taxonomies** that ship with the Doks theme. Verified zero content uses them: no blog posts, no contributors data file. Starlight has no built-in blog equivalent, so keeping this capability "for later" would mean standing up a custom blog integration for a feature with no current content and no stated need.

**Not in scope for this pass:** the go2rtc camera-streaming guide (`docs/superpowers/plans/2026-06-19-go2rtc-guide-implementation.md`) is still a plan, not yet landed in `content/`. If it merges before this migration executes, it needs the same content-mapping rules applied (see below) either as part of this migration or as a fast-follow; this spec doesn't block on it landing first.

## Project Structure

```text
astro.config.mjs           # Starlight integration, sidebar config, customCss
src/content/docs/          # all docs/guide Markdown (Starlight's required content root)
src/content.config.ts      # content collection schema (Starlight defaults)
src/styles/custom.css      # --sl-content-width override
public/                    # Astro's static-asset SOURCE dir
```

**Naming collision to handle carefully during migration:** Hugo's `public/` is gitignored *build output*. Astro's `public/` is a *source* directory for static assets copied as-is. Same name, opposite role. The old Hugo build artifact directory must be cleared (or already gitignored and absent from the working tree) before Astro's source `public/` is created in its place — otherwise stale Hugo build output could get mistaken for, or collide with, Astro source assets.

**Removed:**
- `config/` (`config/_default/hugo.toml`, `config/next/hugo.toml`, `config/production/hugo.toml`, `config/_default/menus/menus.en.toml`)
- `@hyas/doks-core`, `@hyas/images`, `@hyas/inline-svg`, `@hyas/seo` npm packages
- `netlify.toml` (stale, pins an old Hugo version, not the active deploy path)
- `hugo_stats.json`, `.hugo_build.lock`

## Styling: Content Width Fix

Starlight's default `--sl-content-width` is `45rem` (`packages/starlight/style/props.css`), which is what makes the content column look narrow on large screens. Fix:

```css
/* src/styles/custom.css */
:root {
  --sl-content-width: calc(100% - var(--sl-sidebar-width));
}
```

```js
// astro.config.mjs
starlight({
  customCss: ['./src/styles/custom.css'],
})
```

This isn't an arbitrary value — it's chosen because Starlight's own grid math in `TwoColumnContent.astro` already runs `--sl-content-width` through a calc for both `.main-pane`'s width and the right-hand ToC sidebar's width:

```
.main-pane          = content-width + (100% - content-width - sidebar-width) / 2
.right-sidebar-container = sidebar-width + (100% - content-width - sidebar-width) / 2
```

Substituting `content-width = 100% - sidebar-width` makes the `(100% - content-width - sidebar-width)` term resolve to exactly `0` in both formulas. `.main-pane` becomes exactly `100% - sidebar-width`; the ToC sidebar becomes exactly `sidebar-width`. No leftover term, nothing goes negative — which sidesteps the known ToC-overflow failure mode (`withastro/starlight` issue #3513) that hits people who set `--sl-content-width` to a flat value like `100%` without accounting for the sidebar.

This reproduces Ion's "fill all available space" behavior through Starlight's own public, documented variable, with no internal classnames touched and no third-party theme dependency. Precedent: Starlight itself reassigns this variable conditionally — `Page.astro` sets `--sl-content-width: 67.5rem` for pages with no sidebar.

## Content Migration Mapping

Applies to the three existing guides (`automatic-z-offset-adjustments.md`, `energy-usage-monitoring.md`, `optimized-bed-leveling-macros.md`) and the resources/privacy/docs-index pages.

**Front matter:**
- `title`, `description` — carry over unchanged.
- `weight` (Doks ordering) — replaced by Starlight sidebar `autogenerate`, which sorts alphabetically by filename. No numeric weight field needed.
- `seo: { title, description, canonical, noindex }` block — mostly redundant; Starlight generates reasonable SEO meta tags from `title`/`description` directly. Before dropping `noindex` outright, confirm no current page sets it to `true` (none currently do, but verify during implementation rather than assume).

**Callouts:** Hugo shortcode → Starlight Markdown directive, no `.mdx` conversion required (this syntax is documented to work in plain `.md`):

```text
{{< callout context="caution" title="..." icon="outline/alert-triangle" >}}
...
{{< /callout >}}
```
becomes
```text
:::caution[...]
...
:::
```

Type names map 1:1: `note`, `tip`, `caution`, `danger` — same four names in both Doks' SCSS and Starlight's built-in aside types. The Doks-specific `icon="outline/..."` parameter is dropped; Starlight's default icon per type already matches the same intent (e.g. caution → warning triangle).

**Code blocks:** drop the curly braces, everything else is unchanged:

````text
```bash {title="Installing FFmpeg"}
````
becomes
````text
```bash title="Installing FFmpeg"
````

Starlight ships Expressive Code by default, which supports this `title="..."` meta-string syntax natively.

**File format:** all content stays `.md`. No MDX migration needed for anything covered by this spec.

**Numbered steps:** Hugo's repeated `1.` auto-increment convention is plain CommonMark behavior — unchanged in any Markdown renderer, no migration needed.

## Sidebar & Navigation

`astro.config.mjs` sidebar config, using `autogenerate` per directory:

```js
starlight({
  sidebar: [
    { label: 'Guides', autogenerate: { directory: 'guides' } },
  ],
})
```

Sort order is alphabetical by filename — Starlight's autogenerate has no built-in date-based or custom sort. Confirmed acceptable: current guide ordering doesn't need to be preserved exactly, alphabetical-by-filename is fine.

## Homepage

Current `content/_index.md` is a stub: title ("Voron Guides") and a one-line tagline, no body content. Maps directly onto Starlight's `template: splash` frontmatter (hero title + tagline + actions, no sidebar) — there's very little to actually port.

## Build & Deploy

Rewrite `.github/workflows/deploy.yml`:
- Remove the Hugo CLI install step entirely.
- Remove the Dart Sass `snap install` step entirely (not needed by Astro's build).
- Keep `actions/checkout`, `actions/setup-node`, `actions/configure-pages`.
- Keep the `npm run build` invocation — the script itself changes to run `astro build`, the workflow step doesn't need to change.
- Change `actions/upload-pages-artifact`'s `path` from `./public` to `./dist` (Astro's default build output directory).

`netlify.toml` is deleted (see Project Structure).

## Git Workflow for the Migration

Regular feature branch cut from the current `gh-pages` tip — **not** an orphan branch. The goal is a clean workspace to build the migration in without messy half-Hugo/half-Astro diffs, not a deliberate history reset. An orphan branch has no common ancestor with `gh-pages`, which forces `git merge --allow-unrelated-histories` at cutover time and produces a merge commit joining two disconnected histories for no benefit — the diff size is the same near-total rewrite either way regardless of which branching approach is used.

Plan: branch from `gh-pages`, do the migration as a sequence of commits (scaffold Astro/Starlight → styles → migrate each page → rewrite deploy workflow → remove Hugo-era files), then **squash-merge into `gh-pages`** for one clean cutover commit. Full history stays linear and intact; no unrelated-histories merge.

## Verification

- `npm run build` (now `astro build` under the hood) exits 0.
- Each migrated page renders: homepage splash, docs index, resources, privacy, and all three guides.
- Callouts render with the correct type/styling for all four variants used across the existing content.
- Code blocks render with their `title="..."` labels intact.
- Sidebar shows all docs/guides pages, alphabetically ordered.
- `--sl-content-width` fix is visibly wider than Starlight's 45rem default on a large viewport, with no ToC overflow.
- GitHub Pages deploy workflow runs green end-to-end on the feature branch (via `workflow_dispatch` or a temporary branch trigger) before the squash-merge into `gh-pages`.

## Out of Scope

- Ion or Page themes, or any third-party Starlight theme.
- Custom/dynamic sidebar sorting (e.g. by last-updated date) — confirmed unnecessary, autogenerate's alphabetical default is fine.
- Blog, categories, contributors functionality (dropped per Scope).
- i18n, versioned docs, search configuration beyond Starlight's defaults.
- The go2rtc camera-streaming guide, pending its own implementation (see Scope).
- Netlify as a deploy target (the active deploy path is GitHub Pages via Actions; `netlify.toml` is removed, not ported).

## Acceptance Criteria

- Site builds via `npm run build` with Astro/Starlight, no Hugo toolchain involved.
- `.github/workflows/deploy.yml` no longer installs Hugo or Dart Sass, and uploads `./dist`.
- All current content (homepage, docs index, resources, privacy, 3 guides) is present and renders correctly under Astro/Starlight.
- All Hugo shortcodes (`callout`) are converted to Starlight's native syntax; no `{{< ... >}}` shortcode syntax remains anywhere in `src/content/docs/`.
- `config/`, `@hyas/*` packages, `netlify.toml`, `hugo_stats.json`, and `.hugo_build.lock` are removed.
- `--sl-content-width` is set via the calc-based override in `src/styles/custom.css`, registered through `customCss`.
- Migration work happens on a feature branch off `gh-pages` and lands via a single squash-merge.
