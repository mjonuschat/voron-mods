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

**Page inventory** (whole site, confirmed against the current `content/` tree): `content/_index.md` (homepage), `content/docs/_index.md`, `content/docs/guides/_index.md`, `content/docs/resources.md`, `content/privacy.md`, and the three guides under `content/docs/guides/`.

**Not in scope for this pass:** the go2rtc camera-streaming guide (`docs/superpowers/plans/2026-06-19-go2rtc-guide-implementation.md`) is still a plan, not yet landed in `content/`. If it merges before this migration executes, it needs the same content-mapping rules applied (see below) either as part of this migration or as a fast-follow; this spec doesn't block on it landing first.

## Project Structure

```text
astro.config.mjs           # Starlight integration, sidebar config, customCss
src/content/docs/          # all docs/guide Markdown (Starlight's required content root)
src/content.config.ts      # content collection schema (Starlight defaults)
src/styles/custom.css      # --sl-content-width override
public/                    # Astro's static-asset SOURCE dir
```

**Naming collision to handle carefully during migration:** Hugo's `public/` is gitignored *build output* (`.gitignore`, under the "Generate pages" comment). Astro's `public/` is a *source* directory for static assets copied as-is. Same name, opposite role — and the existing blanket `public/` gitignore rule is wrong for Astro: it would silently swallow any future Astro static asset (favicon, `robots.txt`, a custom-domain `CNAME` file) without anyone noticing. Since this migration removes Hugo entirely (Astro's build output goes to `dist/`, not `public/`), remove the `public/` gitignore rule outright rather than patching it with negations — the rule's reason for existing (Hugo build output) goes away along with Hugo. Given the image-mapping decision below, `public/` likely starts out empty or near-empty after migration; that's fine, it's a source directory, not a sign anything is missing.

**Removed:**
- `config/` (`config/_default/hugo.toml`, `config/next/hugo.toml`, `config/production/hugo.toml`, `config/_default/menus/menus.en.toml`)
- `@hyas/doks-core`, `@hyas/images`, `@hyas/inline-svg`, `@hyas/seo` npm packages
- `netlify.toml` (stale, pins an old Hugo version, not the active deploy path)
- `hugo_stats.json`, `.hugo_build.lock`
- `resources/` — currently tracked in git despite being Hugo's generated image/Sass cache (`resources/_gen/...`, 15 files, all regeneratable build artifacts that shouldn't have been committed in the first place)
- `layouts/index.html` — once its content is ported (see Homepage, below). `layouts/partials/footer/script-footer-custom.html`, `layouts/partials/head/custom-head.html`, `layouts/partials/head/script-header.html` — confirmed empty Doks scaffold placeholders (e.g. `custom-head.html` is just the comment `<!-- Custom head -->`), nothing to port.
- `assets/scss/common/_custom.scss`, `assets/scss/common/_variables-custom.scss` — confirmed empty placeholders (just "Put your custom SCSS code here" comments), nothing to port.
- `assets/jsconfig.json` — hardcodes a path alias into `node_modules/@hyas/doks-core/assets/*`, dead once `@hyas/doks-core` is removed.

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

**Disclosure blocks (`details` shortcode):** used twice, both nested inside a `callout` (`automatic-z-offset-adjustments.md:45`, `energy-usage-monitoring.md:194`):

```text
{{< details "Macro: PRINT_END" >}}
...
{{< /details >}}
```
becomes plain HTML, which nests fine inside a `:::` aside directive:
```html
<details>
<summary>Macro: PRINT_END</summary>

...

</details>
```

**Images:** the existing guides reference 5 PNGs via Hugo's asset pipeline, sourced from `assets/images/guides/{automatic-z-offset-ajustments,energy-usage-monitoring}/*.png` (note: the source folder name has a pre-existing typo, "ajustments" — left as-is unless a cleanup is wanted separately).

**Not** `public/` with a root-absolute path. This site's production base is `/voron-mods` (`config/production/hugo.toml:2`, carrying over to Astro's `base` config). Astro only auto-prefixes `base` onto asset URLs it generates itself through its build pipeline — a literal Markdown reference like `![alt](/images/foo.png)` pointing at a `public/` file is emitted into the HTML completely as-written, with no base awareness at all, and would 404 on the deployed site under `/voron-mods/`. Plain `.md` content has no way to interpolate `import.meta.env.BASE_URL` to fix this (that's a JS expression, only usable in `.astro` files or MDX).

Move the images to `src/assets/guides/{automatic-z-offset-ajustments,energy-usage-monitoring}/*.png` instead, and reference them with relative Markdown paths from each guide file:

```text
![PrusSlicer Filament Settings](../../../../assets/guides/automatic-z-offset-ajustments/prusaslicer-filament-settings.png)
```

This is Astro's documented recommendation for content-collection images ("local images are kept in `src/` when possible so that Astro can transform, optimize, and bundle them") — Astro processes these through `astro:assets`, the same base-aware pipeline used for bundled CSS/JS, so the `base` prefix is applied automatically and correctly, with image optimization as a side benefit. The relative path is four levels up (`src/content/docs/docs/guides/` → `src/`) given the nested `docs/docs/guides/` path from URL Structure, above, and guides staying flat files rather than folders — worth confirming during implementation whether Astro also resolves a `tsconfig.json` import alias here instead of the relative path; the relative-path approach above is the one that's directly confirmed against Astro's docs.

**File format:** guide/docs content stays `.md`. The homepage becomes `.mdx` (see Homepage, below) to use Starlight's `Card`/`CardGrid` components — that's the only page in this migration that needs MDX.

**Numbered steps:** Hugo's repeated `1.` auto-increment convention is plain CommonMark behavior — unchanged in any Markdown renderer, no migration needed.

## Sidebar & Navigation

`astro.config.mjs` sidebar config, using `autogenerate` per directory:

```js
starlight({
  sidebar: [
    { label: 'Guides', items: [{ autogenerate: { directory: 'docs/guides' } }] },
  ],
})
```

(`directory` is relative to `src/content/docs/`, so it's `docs/guides` here, not `guides` — see URL Structure, above, for why the content is nested one level deeper than it looks like it should be.)

Sort order is alphabetical by filename — Starlight's autogenerate has no built-in date-based or custom sort. Confirmed acceptable: current guide ordering doesn't need to be preserved exactly, alphabetical-by-filename is fine.

## URL Structure

Starlight routes directly from `src/content/docs/`: a file at `src/content/docs/guides/foo.md` becomes `/guides/foo`, not `/docs/guides/foo`. Hugo's current permalink config (`config/_default/hugo.toml:59`) explicitly puts guides under `/docs/guides/...`, scoped to content with type/section `docs`. `content/privacy.md` has `type: "legal"`, so that permalink rule doesn't apply to it — it's already at root `/privacy/` today and is unaffected by anything below.

Decision: preserve the exact current URLs, no redirects. Since Starlight requires all content under `src/content/docs/`, getting an actual `/docs/...` URL (not just a redirect target) means nesting the docs-tree content one level deeper, inside an extra `docs/` folder within that root:

```text
src/content/docs/index.mdx              → /            (homepage, not nested)
src/content/docs/privacy.md             → /privacy     (not nested, see above)
src/content/docs/docs/index.md          → /docs
src/content/docs/docs/resources.md      → /docs/resources
src/content/docs/docs/guides/index.md   → /docs/guides
src/content/docs/docs/guides/*.md       → /docs/guides/*
```

The doubled `docs/docs/` path looks redundant, but it's the documented mechanism for getting a `/docs` URL prefix while still satisfying Starlight's "everything lives under `src/content/docs/`" requirement. This affects the sidebar config and the images' relative-path depth (both below).

## Homepage

`content/_index.md` itself is a stub (title "Voron Guides", one-line tagline, no body) — but the actual rendered homepage also includes a features section that's *not* in the content file at all. It's hardcoded in a Hugo layout override, `layouts/index.html`, as three cards (title, description, link) pointing at each guide:

- Energy Usage Tracking → Energy Usage Monitoring & Tracking guide
- Optimized Bed Leveling Macros guide
- Automating Z Offset Adjustments guide

(A fourth section in that same layout file, a "Start building with Doks today" CTA, is gated behind `sectionFooter = false` in `config/_default/params.toml` and never actually renders — that one's dead code, not migrated.)

Decision: keep the feature cards, using Starlight's built-in `Card`/`CardGrid` components, which exist for exactly this pattern. The homepage becomes `src/content/docs/index.mdx` (Starlight's standard homepage location — content directly in the `docs` root maps to `/`) instead of `.md`, since `Card`/`CardGrid` are components that need MDX. The page still uses `template: splash` frontmatter for the hero title/tagline; the `CardGrid` of three `Card`s replaces the hardcoded HTML from `layouts/index.html`.

Same base-path issue as the images applies to each `Card`'s `href` — a literal `href="/docs/guides/..."` would 404 under the `/voron-mods` base for the same reason. Since this page is `.mdx`, it can use a JS expression directly: `href={`${import.meta.env.BASE_URL}docs/guides/...`}`.

## Branding & SEO Assets

`assets/favicon.ico`, `assets/favicon.png`, `assets/favicon.svg`, `assets/mask-icon.svg`, and `assets/cover.png` are currently wired through Doks' `@hyas/seo` config (`config/_default/params.toml`'s `seo.favicons` and `seo.schemas` blocks). Once `@hyas/seo` is removed, that config mechanism goes away with it — these are real branding assets, not theme scaffolding, so they need an explicit replacement rather than silently dropping.

Decision: preserve favicon and social-preview image, using Starlight's native equivalents:

- Move `favicon.svg`/`favicon.ico`/`favicon.png`/`mask-icon.svg`/`cover.png` to `public/`.
- Set Starlight's `favicon` config option to the primary icon (`favicon.svg`).
- Add the mask-icon variant and the `og:image`/`twitter:image` tags via Starlight's `head` config — Starlight has no built-in dynamic OG-image generation, but the current site only ever used one static `cover.png` for the whole site (not per-page images), so a static `head` entry reproduces the existing behavior exactly, nothing lost.

Not migrated: `favicon-512x512.png` (only exists in `public/` build output today, not source — it's generated by `@hyas/images` from the source favicon for the `seo.schemas` Person/Organization JSON-LD logo field) and the JSON-LD structured-data markup itself. Starlight has no built-in schema.org generation; replicating it would mean hand-writing a `<script type="application/ld+json">` block via `head` config for a narrow SEO feature with no evidence it matters for this site's traffic. Flagging this as dropped rather than silently doing so — straightforward to add back later via `head` if wanted.

## Build & Deploy

Rewrite `.github/workflows/deploy.yml`:
- Remove the Hugo CLI install step entirely.
- Remove the Dart Sass `snap install` step entirely (not needed by Astro's build).
- Keep `actions/checkout`, `actions/setup-node`, `actions/configure-pages`.
- Change `actions/upload-pages-artifact`'s `path` from `./public` to `./dist` (Astro's default build output directory).
- The build step's arguments need to change, not just the underlying script. The current workflow passes `npm run build -- --baseURL "${{ steps.pages.outputs.base_url }}/"`, which only makes sense for Hugo — Astro's CLI has no `--baseURL` flag. Astro's equivalents are `--site` and `--base`, and `actions/configure-pages` already provides the right source values as separate outputs (`origin`, e.g. `https://octocat.github.io`, and `base_path`, e.g. `/repo-name`):

```yaml
run: |
  npm run build \
    -- \
    --site "${{ steps.pages.outputs.origin }}" \
    --base "${{ steps.pages.outputs.base_path }}"
```

`netlify.toml` is deleted (see Project Structure).

## Git Workflow for the Migration

Regular feature branch cut from the current `gh-pages` tip — **not** an orphan branch. The goal is a clean workspace to build the migration in without messy half-Hugo/half-Astro diffs, not a deliberate history reset. An orphan branch has no common ancestor with `gh-pages`, which forces `git merge --allow-unrelated-histories` at cutover time and produces a merge commit joining two disconnected histories for no benefit — the diff size is the same near-total rewrite either way regardless of which branching approach is used.

Plan: branch from `gh-pages`, do the migration as a sequence of commits (scaffold Astro/Starlight → styles → migrate each page → rewrite deploy workflow → remove Hugo-era files), then **squash-merge into `gh-pages`** for one clean cutover commit. Full history stays linear and intact; no unrelated-histories merge.

## Verification

- `npm run build` (now `astro build` under the hood) exits 0.
- Each migrated page renders: homepage splash, docs index, guides index, resources, privacy, and all three guides.
- Callouts render with the correct type/styling for all four variants used across the existing content.
- Disclosure blocks (the converted `details` shortcode) render and expand/collapse correctly in both locations they're used.
- All 5 images render correctly under the production `/voron-mods` base path, not just in local dev (where base-prefix bugs are invisible — test against a build with `--base /voron-mods` set, not just `astro dev`).
- Homepage feature card links resolve correctly under the same base path.
- Code blocks render with their `title="..."` labels intact.
- Sidebar shows all docs/guides pages, alphabetically ordered.
- `--sl-content-width` fix is visibly wider than Starlight's 45rem default on a large viewport, with no ToC overflow.
- Homepage renders the hero (title/tagline) and all three feature cards via `CardGrid`/`Card`, linking to the correct guides.
- Guide/docs URLs are unchanged from the current site (`/docs/guides/...`, `/docs/resources`, `/docs`) — no redirects, no broken bookmarks.
- Favicon renders correctly in the browser tab; viewing page source shows `og:image`/`twitter:image` tags pointing at `cover.png`.
- GitHub Pages deploy workflow runs green end-to-end on the feature branch (via `workflow_dispatch` or a temporary branch trigger) before the squash-merge into `gh-pages`.

## Out of Scope

- Ion or Page themes, or any third-party Starlight theme.
- Custom/dynamic sidebar sorting (e.g. by last-updated date) — confirmed unnecessary, autogenerate's alphabetical default is fine.
- Blog, categories, contributors functionality (dropped per Scope).
- i18n, versioned docs, search configuration beyond Starlight's defaults.
- The go2rtc camera-streaming guide, pending its own implementation (see Scope).
- Netlify as a deploy target (the active deploy path is GitHub Pages via Actions; `netlify.toml` is removed, not ported).
- Schema.org/JSON-LD structured data (Doks' `seo.schemas` Person/Organization markup) — dropped, see Branding & SEO Assets.

## Acceptance Criteria

- Site builds via `npm run build` with Astro/Starlight, no Hugo toolchain involved.
- `.github/workflows/deploy.yml` no longer installs Hugo or Dart Sass, and uploads `./dist`.
- All current content (homepage, docs index, guides index, resources, privacy, 3 guides) is present and renders correctly under Astro/Starlight.
- All Hugo shortcodes (`callout`, `details`) are converted to Starlight/HTML equivalents; no `{{< ... >}}` shortcode syntax remains anywhere in `src/content/docs/`.
- All 5 images are moved to `src/assets/guides/...`, referenced via relative Markdown paths, and verified to resolve correctly under the `/voron-mods` production base path (not just root-relative in local dev).
- The homepage's three feature cards are preserved via Starlight's `Card`/`CardGrid` components, with `href`s explicitly prefixed via `import.meta.env.BASE_URL`.
- The `public/` gitignore rule is removed (it was a Hugo-build-output convention; Astro's `public/` is source, and the old rule would silently hide future static assets).
- `resources/_gen/` (Hugo's generated image/Sass cache, currently tracked) is removed from the repo.
- `/docs/guides/...`, `/docs/resources`, and `/docs` URLs are identical to the current site, via content nested under `src/content/docs/docs/...` — no redirects configured or needed.
- The GitHub Actions build step passes `--site`/`--base` (not Hugo's `--baseURL`), sourced from `actions/configure-pages`'s `origin`/`base_path` outputs.
- `config/`, `@hyas/*` packages, `netlify.toml`, `hugo_stats.json`, `.hugo_build.lock`, `layouts/`, `assets/scss/`, and `assets/jsconfig.json` are removed.
- Favicon and social-preview image (`cover.png`) are preserved via Starlight's `favicon` and `head` config, pointing at assets moved to `public/`.
- `--sl-content-width` is set via the calc-based override in `src/styles/custom.css`, registered through `customCss`.
- Migration work happens on a feature branch off `gh-pages` and lands via a single squash-merge.
