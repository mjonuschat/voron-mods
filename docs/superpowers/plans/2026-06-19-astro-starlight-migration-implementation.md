# Astro/Starlight Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Hugo + Doks site with Astro + Starlight, preserving every page's exact URL, content, and branding, deployed identically via the existing GitHub Pages Actions workflow.

**Architecture:** Astro/Starlight is scaffolded in place inside the existing repo (no new subdirectory, no separate package.json). Content moves from Hugo's `content/` tree into Starlight's `src/content/docs/` collection, nested one level deeper under an extra `docs/` folder so the public URLs stay byte-identical to today (`/docs/guides/...`, not Starlight's default `/guides/...`). Guide images move to `src/assets/` so Astro's `astro:assets` pipeline handles the production `/voron-mods` base path automatically; branding assets move to `public/`. The GitHub Actions deploy workflow is rewritten in place to invoke Astro instead of Hugo.

**Tech Stack:** Astro, `@astrojs/starlight`, Markdown/MDX, GitHub Actions, GitHub Pages.

## Global Constraints

- Production base path is `/voron-mods` (GitHub Pages project site at `mjonuschat/voron-mods`, full origin `https://mjonuschat.github.io`). Any link or image reference written as a literal string in Markdown/MDX/config (e.g. `/images/foo.png`, `href="/guides/foo"`) will silently 404 in production — Astro only base-prefixes assets it processes itself (`astro:assets`, bundled CSS/JS) or values read from `import.meta.env.BASE_URL` at runtime. Never write a literal root-relative path in content; use relative paths for images and `import.meta.env.BASE_URL` for any hardcoded link in MDX. `BASE_URL` is not guaranteed to have a trailing slash (it mirrors whatever `--base` was passed, untouched, under the default `trailingSlash: 'ignore'`) — strip any trailing slash and supply the `/` separator explicitly when concatenating a path onto it.
- Guide/docs URLs must stay byte-identical to today: `/docs/guides/<slug>`, `/docs/guides`, `/docs`, `/docs/resources`, `/privacy`, `/`. No redirects.
- Guides and all stub pages stay `.md`. Only the homepage (`src/content/docs/index.mdx`) is `.mdx`, because it's the only page using a component (`LinkCard`/`CardGrid`).
- Callout type names map 1:1: `note`, `tip`, `caution`, `danger`. The Doks `icon="outline/..."` parameter is dropped; Starlight's default icon per type is used instead.
- Migration happens on a feature branch cut from `gh-pages`, landing via a single squash-merge — not an orphan branch.
- Source: `docs/superpowers/specs/2026-06-19-astro-starlight-migration-design.md`.

---

## Before Task 1: Create the feature branch

```bash
git checkout -b astro-starlight-migration gh-pages
```

Expected: new branch created, currently identical to `gh-pages`.

---

## Task 1: Scaffold Astro + Starlight, remove Hugo from package.json

**Files:**
- Modify: `package.json`, `.gitignore`
- Create: `astro.config.mjs`
- Create: `src/content.config.ts`
- Create: `tsconfig.json`
- Create: `src/content/docs/index.md` (placeholder — replaced with the real homepage in Task 4)
- Create: `src/content/docs/docs/guides/index.md`

- [ ] **Step 1: Remove Hugo scripts and dependencies from package.json**

Replace the full contents of `package.json`:

```json
{
  "name": "voron-mods",
  "version": "0.0.0",
  "description": "Voron 3D printer guides",
  "author": "Morton Jonuschat",
  "license": "MIT",
  "scripts": {
    "dev": "astro dev",
    "build": "astro build",
    "preview": "astro preview",
    "format": "prettier **/** -w -c"
  },
  "dependencies": {},
  "devDependencies": {
    "prettier": "^3.2.5"
  },
  "engines": {
    "node": ">=20.11.0"
  }
}
```

- [ ] **Step 2: Install Astro and Starlight**

Run:

```bash
npm install astro @astrojs/starlight
```

Expected: `package.json`'s `dependencies` now includes `astro` and `@astrojs/starlight`; `package-lock.json` is updated.

- [ ] **Step 3: Ignore Astro's generated types directory**

Astro creates `.astro/` locally (generated TypeScript types for content collections, env vars, etc.) on every `dev`/`build`/`sync` run, starting with Step 8's build below. It's not currently in `.gitignore` — add it now, before it has a chance to show up as untracked cruft in any `git status` check later in this plan (Task 11's final check expects a clean working tree).

In `.gitignore`, add this block right before the existing `# Next.js build output` section:

```text
# Astro
.astro/
```

(`dist/` is already covered — it's ignored as a side effect of the existing `# Nuxt.js build / generate output` section further down, which happens to use the same directory name.)

- [ ] **Step 4: Create the Astro/Starlight config**

Create `astro.config.mjs`:

```js
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  integrations: [
    starlight({
      title: 'Voron Guides',
      favicon: '/favicon.svg',
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/mjonuschat/voron-mods' },
      ],
      sidebar: [
        { label: 'Guides', items: [{ autogenerate: { directory: 'docs/guides' } }] },
      ],
    }),
  ],
});
```

(`favicon` and `social` reference files/URLs added in Task 3 — harmless if `public/favicon.svg` doesn't exist yet, Astro will warn but still build. `sidebar` references `docs/guides`, populated in Task 6.)

- [ ] **Step 5: Create the content collection schema**

Create `src/content.config.ts`:

```ts
import { defineCollection } from 'astro:content';
import { docsLoader } from '@astrojs/starlight/loaders';
import { docsSchema } from '@astrojs/starlight/schema';

export const collections = {
  docs: defineCollection({ loader: docsLoader(), schema: docsSchema() }),
};
```

- [ ] **Step 6: Create tsconfig.json**

Create `tsconfig.json`:

```json
{
  "extends": "astro/tsconfigs/strict"
}
```

- [ ] **Step 7: Create a placeholder homepage so the build succeeds**

Create `src/content/docs/index.md`:

```markdown
---
title: "Voron Guides"
description: "A collection of guides & tutorials for Voron 3D Printers"
template: splash
---

Placeholder — replaced with the real homepage in Task 4.
```

- [ ] **Step 8: Create the (initially empty) guides directory the sidebar config references**

Create `src/content/docs/docs/guides/index.md` now, rather than in Task 5 where it'd otherwise land — the sidebar config above (Step 4) references `docs/guides` via `autogenerate` before any file exists there:

```markdown
---
title: "Guides"
---
```

Traced Starlight's actual autogenerate logic (`packages/starlight/utils/navigation.ts`) to check whether this matters: `entriesFromAutogenerateConfig` filters the content collection's already-resolved route list for paths under the configured directory — there's no filesystem existence check, so an empty or missing directory should just produce an empty sidebar group, not a build error. This step is a low-cost preventive measure rather than a confirmed-necessary fix; it removes any doubt for the cost of creating one stub file slightly earlier than originally planned. Task 5 no longer creates this file (moved here).

- [ ] **Step 9: Build and verify**

Run:

```bash
npm run build
```

Expected: exits 0, `dist/index.html` and `dist/docs/guides/index.html` both exist.

- [ ] **Step 10: Commit**

```bash
git add package.json package-lock.json .gitignore astro.config.mjs src/content.config.ts tsconfig.json src/content/docs/index.md src/content/docs/docs/guides/index.md
git commit -m "[TASK] Scaffold Astro/Starlight, remove Hugo from package.json"
```

## Task 2: Apply the --sl-content-width fix

**Files:**
- Create: `src/styles/custom.css`
- Modify: `astro.config.mjs`

- [ ] **Step 1: Create the custom CSS override**

Create `src/styles/custom.css`:

```css
:root {
  --sl-content-width: calc(100% - var(--sl-sidebar-width));
}
```

- [ ] **Step 2: Register the custom CSS file**

In `astro.config.mjs`, add `customCss` to the `starlight()` call:

```js
    starlight({
      title: 'Voron Guides',
      favicon: '/favicon.svg',
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/mjonuschat/voron-mods' },
      ],
      sidebar: [
        { label: 'Guides', items: [{ autogenerate: { directory: 'docs/guides' } }] },
      ],
      customCss: ['./src/styles/custom.css'],
    }),
```

- [ ] **Step 3: Build and verify the custom property is present**

Run:

```bash
npm run build
grep -r "sl-content-width" dist/_astro/*.css
```

Expected: the build succeeds, and the grep finds `--sl-content-width:calc(100% - var(--sl-sidebar-width)))` (or equivalent minified form) in one of the generated CSS files.

- [ ] **Step 4: Commit**

```bash
git add astro.config.mjs src/styles/custom.css
git commit -m "[TASK] Apply --sl-content-width fix"
```

## Task 3: Migrate branding/favicon assets, fix the public/ gitignore rule

**Files:**
- Create: `public/favicon.svg`, `public/favicon.ico`, `public/favicon.png`, `public/mask-icon.svg`, `public/cover.png` (copied from `assets/`)
- Modify: `.gitignore`
- Modify: `astro.config.mjs`

- [ ] **Step 1: Clean out the stale Hugo build output already sitting in public/**

`public/` currently exists on disk as leftover Hugo build output from a previous local `npm run build` — 77 files including a stale `favicon.ico`/`favicon.svg` at the exact destination paths Step 2 is about to `git mv` into. None of it is tracked in git (confirm with `git ls-files public/` — expect zero output), so it's safe to wipe entirely:

```bash
git ls-files public/
git clean -fdX public/
```

Expected: the `git ls-files` command prints nothing (confirming nothing under `public/` is tracked, so cleaning it is non-destructive to git history). `git clean -fdX` removes only gitignored files/directories, which right now is everything under `public/` — it must run before Step 3 removes the gitignore rule, otherwise `-X` won't match anything anymore.

- [ ] **Step 2: Move the branding assets to public/**

```bash
mkdir -p public
git mv assets/favicon.svg public/favicon.svg
git mv assets/favicon.ico public/favicon.ico
git mv assets/favicon.png public/favicon.png
git mv assets/mask-icon.svg public/mask-icon.svg
git mv assets/cover.png public/cover.png
```

- [ ] **Step 3: Remove the stale public/ gitignore rule**

In `.gitignore`, find this block near the end of the file:

```text
# Generate pages
public/
```

Delete both lines. This rule existed because Hugo's build output landed in `public/`; Astro's build output is `dist/`, and Astro's `public/` is a source directory that should be tracked normally.

- [ ] **Step 4: Add head tags for the mask-icon and social-preview image**

In `astro.config.mjs`, add a `head` array to the `starlight()` call:

```js
    starlight({
      title: 'Voron Guides',
      favicon: '/favicon.svg',
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/mjonuschat/voron-mods' },
      ],
      sidebar: [
        { label: 'Guides', items: [{ autogenerate: { directory: 'docs/guides' } }] },
      ],
      customCss: ['./src/styles/custom.css'],
      head: [
        {
          tag: 'link',
          attrs: { rel: 'mask-icon', href: 'https://mjonuschat.github.io/voron-mods/mask-icon.svg', color: 'white' },
        },
        {
          tag: 'meta',
          attrs: { property: 'og:image', content: 'https://mjonuschat.github.io/voron-mods/cover.png' },
        },
        {
          tag: 'meta',
          attrs: { name: 'twitter:image', content: 'https://mjonuschat.github.io/voron-mods/cover.png' },
        },
      ],
    }),
```

All three of these (`mask-icon`, `og:image`, `twitter:image`) are hardcoded absolute URLs, not base-aware — this is a deliberate simplification, and it matters why. Checked Starlight's source (`packages/starlight/utils/head.ts`) to confirm: the native `favicon` option (set above, `favicon: '/favicon.svg'`) is base-prefixed automatically — Starlight runs it through an internal `fileWithBase()` helper specifically for this reason. But that helper only applies to Starlight's own `favicon` option; arbitrary entries added through `head` are merged in literally, with no base-prefixing applied (confirmed in the same file — user-supplied `head` entries go straight through `mergeHead()`, no `fileWithBase()` call). So `favicon: '/favicon.svg'` is correct as a root-relative path, but anything in this `head` array needs to either be absolute or computed some other way. `astro.config.mjs` is evaluated before the `--site`/`--base` CLI flags are resolved, so there's no clean way to compute the base dynamically from within this static array — hardcoding the known production URL is the pragmatic choice. If the GitHub org/repo ever changes, this needs a manual update; getting it wrong only produces a stale icon/social-preview image, not a broken in-page link, which is why this is an acceptable simplification here in a way it wouldn't be for the homepage's actual guide links (Task 4).

- [ ] **Step 5: Build and verify**

Run:

```bash
npm run build
ls dist/favicon.svg dist/favicon.ico dist/favicon.png dist/mask-icon.svg dist/cover.png
grep -o '<link rel="shortcut icon"[^>]*>' dist/index.html
grep -o '<link rel="mask-icon"[^>]*>' dist/index.html
grep -o '<meta property="og:image"[^>]*>' dist/index.html
```

Expected: all five files exist in `dist/`, the `shortcut icon` link (Starlight's native favicon rendering) has an `href` starting with `/favicon.svg` (root-relative is correct here, with no base flag passed in this build), and the other two grep commands find their respective tags with the full hardcoded `https://mjonuschat.github.io/voron-mods/...` URLs.

- [ ] **Step 6: Commit**

```bash
git add -A public/ .gitignore astro.config.mjs
git status --short
git commit -m "[TASK] Migrate branding assets, fix public/ gitignore rule"
```

## Task 4: Migrate the homepage

**Files:**
- Modify: `src/content/docs/index.md` → rename to `src/content/docs/index.mdx`
- Delete: `content/_index.md`, `layouts/index.html`

- [ ] **Step 1: Delete the placeholder, create the real homepage as MDX**

```bash
git rm src/content/docs/index.md
```

Create `src/content/docs/index.mdx`:

```mdx
---
title: "Voron Guides"
description: "A collection of guides & tutorials for Voron 3D Printers"
template: splash
---

import { CardGrid, LinkCard } from '@astrojs/starlight/components';

export const base = import.meta.env.BASE_URL.replace(/\/$/, '');

A collection of guides & tutorials for Voron 3D Printers

<CardGrid>
	<LinkCard title="Energy Usage Tracking" href={`${base}/docs/guides/energy-usage-monitoring-tracking/`} description="Step-by-step tutorial to integrate a network-connected power meter with Moonraker, enabling real-time energy consumption monitoring and historical data tracking." />
	<LinkCard title="Optimized Bed Leveling Macros" href={`${base}/docs/guides/optimized-bed-leveling-macros/`} description="Guide to implementing a two-pass bed leveling approach, consisting of an initial coarse leveling pass for safety and speed, followed by a fine leveling pass for precise accuracy." />
	<LinkCard title="Automating Z Offset Adjustments" href={`${base}/docs/guides/automating-z-offset-adjustments/`} description="Detailed step-by-step instructions to configure Z offset adjustments for each filament type in your Slicer software, suitable for all Klipper enabled printers." />
</CardGrid>
```

`LinkCard`, not `Card`, is the component that actually renders a clickable link. Checked Starlight's source (`packages/starlight/user-components/Card.astro`): `Card`'s `Props` interface is only `{ icon?: StarlightIcon; title: string; }` — `href` isn't part of it, isn't destructured, and is silently dropped if passed. `Card` renders a plain `<article>` with no `<a>` tag anywhere in its output; it's a static box, not a link. `LinkCard.astro`'s `Props` extends `Omit<HTMLAttributes<'a'>, 'title'>` plus `description`, and spreads `...attributes` (including `href`) onto a real `<a>`. `LinkCard` has no `icon` prop (it always renders a fixed arrow icon) and no slot for body content — that's why the description text moved from a child into the `description` prop. Verified by compiling this exact block through `@mdx-js/mdx`'s `compile()`.

The `href` on each `LinkCard` is a JS expression building the URL from `import.meta.env.BASE_URL`, not a literal string. This is the only correct option for a link like this written directly in content — a plain Markdown link (`[text](/docs/guides/...)`) would have the exact same problem as the images: it's a literal string emitted as-is into the `<a href>`, with no base-prefixing applied by anything in Astro's pipeline. There's no Starlight mechanism that makes hardcoded absolute paths in Markdown/MDX body content base-aware; only assets processed through `astro:assets` (Task 7-8's images) and Starlight's own first-party config options (the `favicon` option in Task 3) get that treatment automatically.

`BASE_URL`'s trailing slash isn't guaranteed — Astro's config schema (`packages/astro/src/core/config/schemas/relative.ts`) only force-adds or force-strips a trailing slash on `base` when `trailingSlash` is explicitly `'always'` or `'never'`; the default `'ignore'` (unset here) leaves `base` exactly as passed to `--base` on the CLI. Since Task 9's build command passes `--base "/voron-mods"` with no trailing slash, plain `${base}docs/...` concatenation would silently produce `/voron-modsdocs/...`. Stripping any trailing slash from `base` and hardcoding the `/` separator in the template literal makes this correct regardless of `trailingSlash`'s value. Verify the actual rendered `href` values in Task 11.

The `base` declaration must be `export const`, not a bare `const`. MDX's compiler only recognizes a top-level block as code (ESM) if it starts with `import` or `export` — confirmed by compiling both forms through `@mdx-js/mdx`'s `compile()`: a bare `const base = ...;` gets parsed as a markdown paragraph (literally rendered as the text `const base = ...;`), and `base` is then undefined wherever the `LinkCard` `href`s reference it, throwing `base is not defined` at build time. `export const` is recognized as ESM and hoisted above the generated `_createMdxContent` function, where it's reachable via ordinary closure — the `export` keyword itself isn't what makes it accessible, it's what makes MDX treat the line as code instead of prose in the first place.

- [ ] **Step 2: Delete the old Hugo homepage files**

```bash
git rm content/_index.md layouts/index.html
```

- [ ] **Step 3: Build and verify**

Run:

```bash
npm run build
grep -o "Voron Guides" dist/index.html
grep -c "sl-link-card" dist/index.html
grep -o 'href="[^"]*docs/guides[^"]*"' dist/index.html
```

Expected: build exits 0, "Voron Guides" appears in the output, the `sl-link-card` count is 3 (confirms `LinkCard`'s own class, not the ambiguous `card` substring both `Card` and `LinkCard` would match), and the `href` grep prints three links — one per guide. The `href` check specifically is what proves these are real clickable links rather than `Card`'s static, non-linking box (`Card` accepts no `href` prop and would have rendered with this same `grep -c "card"` count satisfied while producing zero actual links — checking for the link-bearing class and the actual `href` values is what catches that).

- [ ] **Step 4: Commit**

```bash
git add -A src/content/docs/index.mdx
git rm -r --cached content/_index.md layouts/index.html 2>/dev/null || true
git commit -m "[TASK] Migrate homepage to Starlight LinkCard/CardGrid"
```

## Task 5: Migrate the docs index, resources, and privacy pages

**Files:**
- Create: `src/content/docs/docs/index.md`
- Create: `src/content/docs/docs/resources.md`
- Create: `src/content/docs/privacy.md`
- Delete: `content/docs/_index.md`, `content/docs/guides/_index.md`, `content/docs/resources.md`, `content/privacy.md`

All four source pages are stubs (front matter only, little or no body) — ported as-is. The guides index (`src/content/docs/docs/guides/index.md`) was already created back in Task 1, since the sidebar's `autogenerate` config needed that directory to exist from the very first build — only its old Hugo source file still needs deleting here.

- [ ] **Step 1: Create the docs index**

Create `src/content/docs/docs/index.md`:

```markdown
---
title: "Docs"
---
```

- [ ] **Step 2: Create the resources page**

Create `src/content/docs/docs/resources.md`:

```markdown
---
title: "Resources"
---

Link to valuable, relevant resources.
```

- [ ] **Step 3: Create the privacy page**

Note: this page lives directly under `src/content/docs/`, not nested under `docs/docs/`, because Hugo's `/docs/...` permalink rule only applies to content typed `docs`; `privacy.md` is typed `legal` and is already at root `/privacy/` today.

Create `src/content/docs/privacy.md`:

```markdown
---
title: "Privacy Policy"
---
```

- [ ] **Step 4: Delete the old Hugo source files**

```bash
git rm content/docs/_index.md content/docs/guides/_index.md content/docs/resources.md content/privacy.md
```

- [ ] **Step 5: Build and verify**

Run:

```bash
npm run build
ls dist/docs/index.html dist/docs/guides/index.html dist/docs/resources/index.html dist/privacy/index.html
```

Expected: build exits 0, all four files exist at the listed paths (confirming the nested `docs/docs/...` URL structure produces `/docs/...` URLs, and `privacy.md` produces `/privacy/` without nesting).

- [ ] **Step 6: Commit**

```bash
git add -A src/content/docs/docs/ src/content/docs/privacy.md
git commit -m "[TASK] Migrate docs index, resources, and privacy pages"
```

## Task 6: Migrate the Optimized Bed Leveling Macros guide

**Files:**
- Create: `src/content/docs/docs/guides/optimized-bed-leveling-macros.md`
- Delete: `content/docs/guides/optimized-bed-leveling-macros.md`

This guide has no images and no `details` shortcode — it's the simplest of the three, used here to prove out the callout conversion and sidebar autogenerate before tackling the more complex guides.

- [ ] **Step 1: Create the migrated guide**

Create `src/content/docs/docs/guides/optimized-bed-leveling-macros.md`:

```markdown
---
title: "Optimized Bed Leveling Macros"
description: "How to use a dual pass leveling approach for Z_TILT_ADJUST or QUAD_GANTRY_LEVEL"
---

## Introduction

These optimized macros strike a balance between safety and time efficiency by combining the benefits of large and small Z-Hop values. The leveling procedure is divided into two passes:

Pass 1: Initial Coarse Leveling

- Utilizes a large Z-Hop value to prevent scratching the print surface
- Minimizes probing samples to quickly determine bed position
- Relaxes tolerance requirements to ensure bed levelness within 1mm

Pass 2: Fine Leveling and Accuracy

- Employs normal settings for accuracy and retries
- Reduces Z-Hop distance, leveraging the knowledge that the bed is already approximately level

This two-pass approach ensures a efficient and safe leveling process, optimizing time savings while maintaining accuracy.

:::danger[Important Compatibility Notice]
These macros are not compatible with dockable probes, as they override the default bed leveling functionality. Using these macros with dockable probes may result in unexpected behavior or errors.
:::

## QUAD_GANTRY_LEVEL (Voron 2.4)

This macro renames and extends the existing QUAD_GANTRY_LEVEL command, implementing the two-pass leveling process. By replacing the default functionality, no additional modifications to the configuration are required. The macro executes the following steps:

Pass 1: Initial Coarse Leveling - Lifts the head to 10mm  
Pass 2: Fine Leveling - Lifts the head to 2mm  

```ini title="printer.cfg"
[gcode_macro QUAD_GANTRY_LEVEL]
rename_existing: BASE_QUAD_GANTRY_LEVEL
gcode:
    # Pass 1: Initial Coarse Leveling
    BASE_QUAD_GANTRY_LEVEL HORIZONTAL_MOVE_Z=10 RETRY_TOLERANCE=1
    # Pass 2: Fine Leveling and Accuracy
    BASE_QUAD_GANTRY_LEVEL HORIZONTAL_MOVE_Z=2
```

## Z_TILT_ADJUST (Voron Trident)

This macro renames and extends the existing Z_TILT_ADJUST command, implementing the two-pass leveling process. By replacing the default functionality, no additional modifications to the configuration are required. The macro executes the following steps:

Pass 1: Initial Coarse Leveling - Moves bed down by 10mm  
Pass 2: Fine Leveling - Moves bed down by 2mm  

```ini title="printer.cfg"
[gcode_macro Z_TILT_ADJUST]
rename_existing: BASE_Z_TILT_ADJUST
gcode:
    # Pass 1: Initial Coarse Leveling
    BASE_Z_TILT_ADJUST HORIZONTAL_MOVE_Z=10 RETRY_TOLERANCE=1
    # Pass 2: Fine Leveling and Accuracy
    BASE_Z_TILT_ADJUST HORIZONTAL_MOVE_Z=2
```

:::note
Printers equipped with lead screws tend to exhibit reduced bed and gantry sagging, minimizing the impact of these issues. As a result, the advantages of the two-pass leveling approach is less significant.
:::

## Optional Tuning Parameters

The following parameters in the macros can be adjusted to futher optimize the leveling process:

- **HORIZONTAL_MOVE_Z**: Specifies the intermediate move height (in mm) between probes
- **RETRY_TOLERANCE**: Defines the maximum allowable deviation between the largest and smallest probed points, triggering retry leveling if exceeded
- **SAMPLES**: Specifies the number of probe samples to use per leveling point
```

- [ ] **Step 2: Delete the old Hugo source file**

```bash
git rm content/docs/guides/optimized-bed-leveling-macros.md
```

- [ ] **Step 3: Build and verify**

Run:

```bash
npm run build
ls dist/docs/guides/optimized-bed-leveling-macros/index.html
grep -o "callout-danger\|callout-note" dist/docs/guides/optimized-bed-leveling-macros/index.html | sort -u
grep -o "Optimized Bed Leveling Macros" dist/docs/index.html
```

Expected: the guide page exists, both `danger` and `note` aside styling classes are present (Starlight's actual class names may differ slightly from Doks' — confirm by inspecting the rendered output if this exact grep doesn't match, e.g. try `starlight-aside--danger`), and the guide's title appears somewhere reachable from the sidebar (rendered into `dist/docs/index.html`'s sitewide nav, or check any other guide page's sidebar markup).

- [ ] **Step 4: Commit**

```bash
git add -A src/content/docs/docs/guides/optimized-bed-leveling-macros.md
git commit -m "[TASK] Migrate Optimized Bed Leveling Macros guide"
```

## Task 7: Migrate the Automating Z Offset Adjustments guide

**Files:**
- Create: `src/content/docs/docs/guides/automating-z-offset-adjustments.md`
- Create: `src/assets/guides/automatic-z-offset-ajustments/prusaslicer-filament-settings.png`
- Create: `src/assets/guides/automatic-z-offset-ajustments/mainsail-toolhead-z-offset.png`
- Delete: `content/docs/guides/automatic-z-offset-adjustments.md`, `assets/images/guides/automatic-z-offset-ajustments/`

This guide introduces the `details` shortcode conversion and the first images. The folder name `automatic-z-offset-ajustments` keeps the pre-existing source typo ("ajustments") rather than the guide's correctly-spelled filename — this mismatch already exists today and isn't part of this migration's scope to fix.

- [ ] **Step 1: Move the images**

```bash
mkdir -p src/assets/guides/automatic-z-offset-ajustments
git mv assets/images/guides/automatic-z-offset-ajustments/prusaslicer-filament-settings.png src/assets/guides/automatic-z-offset-ajustments/
git mv assets/images/guides/automatic-z-offset-ajustments/mainsail-toolhead-z-offset.png src/assets/guides/automatic-z-offset-ajustments/
```

- [ ] **Step 2: Create the migrated guide**

Create `src/content/docs/docs/guides/automating-z-offset-adjustments.md`:

```markdown
---
title: "Automating Z Offset Adjustments"
description: "Perfect First Layers: Automating Z Offset Adjustments"
---

## Introduction

Printing with diverse filament materials often necessitates Z offset adjustments for optimal bed adhesion and first layer squish. Manually executing these adjustments for each print job be inefficient and errors prone. This guide provides a comprehensive solution, detailing how to configure your Slicer to automatically incorporate necessary Z offset adjustments for each print job. Additionally, we will cover the modification of the `PRINT_END` macro to ensure the Z offset is reset to its default value upon print job completion, streamlining your printing process.

## Prerequisites

To utilize this guide, ensure you have the following:

- A 3D printer configured with Klipper firmware
- A compatible Slicer software that supports filament-specific start G-code, such as:
  - PrusaSlicer
  - SuperSlicer
  - OrcaSlicer
- Enable "Advanced" settings in your Slicer software to access the necessary configuration options.

## Modifying the PRINT_END Macro

The printer.cfg file should already contain a `PRINT_END` macro definition, as this is a standard configuration in Voron setups. If you require a template, refer to the callout section below. To modify the `PRINT_END` macro, append the following command to its end. If your macro utilizes the `SAVE_GCODE_STATE` and `RESTORE_GCODE_STATE` commands, ensure that the added command follows the `RESTORE_GCODE_STATE` command. This is crucial because `RESTORE_GCODE_STATE` also restores the saved G-code offset, which could result in incremental changes to the offset between print jobs, rather than resetting to the baseline offset.

```ini title="printer.cfg"
    SET_GCODE_OFFSET Z=0
```

The `SET_GCODE_OFFSET` command effectively resets the positional offset on the Z-axis to zero, thereby ensuring that all subsequent G-Code commands will execute without any Z-axis offsets. This resets the baseline for Z-axis positioning, allowing subsequent print jobs to adjust from known starting point.

:::tip[No PRINT_END macro?]
The `PRINT_END` macro should be part of your `printer.cfg` as it is an integral part of the stock Voron Klipper configuration. Check the code snippet below in case you don't have one defined yet.

<details>
<summary>Macro: PRINT_END</summary>

```ini title="printer.cfg"
[gcode_macro PRINT_END]
gcode:
    # safe anti-stringing move coords
    {% set th = printer.toolhead %}
    {% set x_safe = th.position.x + 20 * (1 if th.axis_maximum.x - th.position.x > 20 else -1) %}
    {% set y_safe = th.position.y + 20 * (1 if th.axis_maximum.y - th.position.y > 20 else -1) %}
    {% set z_safe = [th.position.z + 2, th.axis_maximum.z]|min %}

    SAVE_GCODE_STATE NAME=STATE_PRINT_END

    M400                           ; wait for buffer to clear
    G92 E0                         ; zero the extruder
    G1 E-5.0 F1800                 ; retract filament

    TURN_OFF_HEATERS

    G90                                      ; absolute positioning
    G0 X{x_safe} Y{y_safe} Z{z_safe} F20000  ; move nozzle to remove stringing
    G0 X{th.axis_maximum.x//2} Y{th.axis_maximum.y - 2} F3600  ; park nozzle at rear
    M107                                     ; turn off fan

    BED_MESH_CLEAR

    # The purpose of the SAVE_GCODE_STATE/RESTORE_GCODE_STATE
    # command pair is to restore the printer's coordinate system
    # and speed settings since the commands above change them.
    # However, to prevent any accidental, unintentional toolhead
    # moves when restoring the state, explicitly set MOVE=0.
    RESTORE_GCODE_STATE NAME=STATE_PRINT_END MOVE=0
```

</details>
:::

## Configuring Filament Settings in Your Slicer

This section uses PrusaSlicer as an example, but the process applies to other slicers as well.

### Step 1: Access Custom G-Code

In your Slicer, navigate to Filament Settings and select the Custom G-code entry (highlighted in blue in the screenshot below).

### Step 2: Add Start G-Code

```gcode title="Start G-Code"
SET_GCODE_OFFSET Z_ADJUST=0.3
```

![PrusSlicer Filament Settings](../../../../assets/guides/automatic-z-offset-ajustments/prusaslicer-filament-settings.png)

Note that the `SET_GCODE_OFFSET` command is utilized again, this time with the `Z_ADJUST` parameter, differing from the `Z` parameter used in the `PRINT_END` macro. The key distinction between these parameters is that `Z` sets the positional offset to the specified value, whereas `Z_ADJUST` modifies the existing offset by adding or subtracting the given value. For instance, executing `SET_GCODE_OFFSET Z=-0.2` followed by `SET_GCODE_OFFSET Z_ADJUST=0.3` results in a cumulative positional offset of **0.1** for the Z axis. This highlights the importance of resetting the offset post-print to maintain the correct Z offset.

## Verification Process

To confirm that the adjustments are being applied correctly, perform the following steps:

1. Slice and initiate a new print job.
2. Observe the Z offset adjustment during the print job preparation phase. If the configuration is correct, the WebUI displays the desired Z offset in the Toolhead card, as shown in the screenshot below:

   ![Mainsail Toolhead Z-Offset](../../../../assets/guides/automatic-z-offset-ajustments/mainsail-toolhead-z-offset.png)

## Further Reading

- Klipper [SET_GCODE_OFFSET](https://www.klipper3d.org/G-Codes.html#set_gcode_offset) documentation
```

- [ ] **Step 3: Delete the old Hugo source file and emptied image directory**

```bash
git rm content/docs/guides/automatic-z-offset-adjustments.md
rmdir assets/images/guides/automatic-z-offset-ajustments 2>/dev/null || true
```

- [ ] **Step 4: Build and verify**

Run:

```bash
npm run build
ls dist/docs/guides/automating-z-offset-adjustments/index.html
grep -c "<img" dist/docs/guides/automating-z-offset-adjustments/index.html
grep -o "<details>" dist/docs/guides/automating-z-offset-adjustments/index.html
grep -o "starlight-aside--tip\|callout-tip" dist/docs/guides/automating-z-offset-adjustments/index.html | head -1
grep -o "printer.cfg" dist/docs/guides/automating-z-offset-adjustments/index.html | head -1
```

Expected: the guide page exists, the `<img>` count is 2, `<details>` is present, the tip-aside class grep matches something (confirms `:::tip[...]` rendered with type-specific styling, not just as plain text — if neither candidate class name matches, inspect the actual rendered HTML for whatever class Starlight does use and adjust this check), and `printer.cfg` appears (confirms the `title="printer.cfg"` code-block labels survived conversion — Expressive Code renders these as visible frame titles, so this also doubles as a sanity check that the code blocks themselves rendered). Then manually verify in a browser (`npm run preview` or check `dist/` directly) that both images actually load — `astro:assets` rewrites image `src` attributes to hashed, optimized filenames, so confirm the referenced file exists in `dist/_astro/` rather than just trusting the tag count.

- [ ] **Step 5: Commit**

```bash
git add -A src/content/docs/docs/guides/automating-z-offset-adjustments.md src/assets/guides/automatic-z-offset-ajustments/
git commit -m "[TASK] Migrate Automating Z Offset Adjustments guide"
```

## Task 8: Migrate the Energy Usage Monitoring guide

**Files:**
- Create: `src/content/docs/docs/guides/energy-usage-monitoring-tracking.md`
- Create: `src/assets/guides/energy-usage-monitoring/shelly-mqtt-settings.png`
- Create: `src/assets/guides/energy-usage-monitoring/mainsail-sensor-data.png`
- Create: `src/assets/guides/energy-usage-monitoring/mainsail-job-history.png`
- Delete: `content/docs/guides/energy-usage-monitoring.md`, `assets/images/guides/energy-usage-monitoring/`

The largest of the three guides — five callouts, one `details` shortcode nested inside a `caution` callout, and three images.

- [ ] **Step 1: Move the images**

```bash
mkdir -p src/assets/guides/energy-usage-monitoring
git mv assets/images/guides/energy-usage-monitoring/shelly-mqtt-settings.png src/assets/guides/energy-usage-monitoring/
git mv assets/images/guides/energy-usage-monitoring/mainsail-sensor-data.png src/assets/guides/energy-usage-monitoring/
git mv assets/images/guides/energy-usage-monitoring/mainsail-job-history.png src/assets/guides/energy-usage-monitoring/
```

- [ ] **Step 2: Create the migrated guide**

Create `src/content/docs/docs/guides/energy-usage-monitoring-tracking.md`:

```markdown
---
title: "Energy Usage Monitoring & Tracking"
description: "How to track energy consumption of print jobs using a Shelly power meter, Moonraker sensors and Mainsail"
---

## Introduction

Moonraker's extended data collection capabilities enable seamless integration with additional sensor sources, including power meters. This feature allows for the tracking of energy consumption data within Moonraker's job history component. Leveraging energy monitors like the Shelly 1PM series, you can gain insights into the energy usage per print job. This guide provides a step-by-step walkthrough for setting up a MQTT server to facilitate data exchange between Shelly and Moonraker, as well as configuring Moonraker to poll and store energy consumption data. Additionally, this guide covers the configuration of Mainsail and Moonraker sensors to track energy usage in the job history.

## Prerequisites

- A power meter or sensor capable of publishing measurements to an MQTT server is required. Compatible devices include the Shelly PM series (e.g., [Shelly 1PM Pro](https://www.shelly.com/en/products/shop/shelly-pro-1pm) or [Shelly 1PM Mini](https://www.shelly.com/en/products/shop/shelly-1-pm-mini-gen3)) and [Tasmota](https://tasmota.github.io/docs/)-based devices. Please note that device installation is not covered in this guide.
- The power meter must be configured to operate on the same network as the Raspberry Pi that controls your printer to allow communication and data exchange.
- A recent version of Mainsail installation (minimum version 2.12.0) is also required.

:::note
This guide assumes the use of a Shelly 1PM device. Please ensure your device is compatible and properly installed before proceeding.
:::

## MQTT Server

MQTT (Message Queuing Telemetry Transport) is a lightweight, machine-to-machine communication protocol that enables Internet of Things (IoT) components to exchange messages. In this application, the Powermeter utilizes MQTT to periodically publish measurement data, while Moonraker subscribes to these messages to receive the data. To facilitate this communication, we will install an MQTT Server on the Raspberry Pi controlling the 3D printer.

### Installation

Please execute the following commands via SSH to complete the installation.

:::note
The guide is using [Mosquitto](https://mosquitto.org/) as the MQTT server.
:::

1. Install the necessary software components by running the following command

   ```bash title="Installing the Mosquitto server"
   sudo apt install -y mosquitto mosquitto-clients
   ```

1. Configure the Mosquitto MQTT server to automatically start on system boot

   ```bash title="Starting Mosquitto on printer startup"
   sudo systemctl enable mosquitto.service
   ```

### Configuration

To enable the MQTT server to receive messages from the power meter over the network, it is essential to configure the server to listen on a designated network port. The subsequent steps will guide you through the setup process for an unauthenticated (anonymous) connection, ensuring seamless communication between the power meter and the MQTT server.

:::danger[Important Security Note]
If you plan to expose your 3D printer or Raspberry Pi to the public internet, it is crucial to implement an authenticated and encrypted connection to ensure secure communication. This guide does not cover authentication and encryption setup. Please refer to the Mosquitto documentation on [Authentication Methods](https://mosquitto.org/documentation/authentication-methods/) and [SSL/TLS Support](https://mosquitto.org/man/mosquitto-conf-5.html) for comprehensive instructions on configuring a secure connection. This will help protect your device and data from unauthorized access.
:::

1. Execute the following command to access and modify the configuration file

   ```bash title="Editing the configuration file"
   sudo nano /etc/mosquitto/mosquitto.conf
   ```

1. Append the following configuration settings to the end of the file

   ```ini title="mosquitto.conf"
   listener 1883
   allow_anonymous true
   ```

1. Exit the editor and save the file by pressing **CTRL-X**, then confirm with **Y** and **Enter**
1. Apply the new configuration by restarting Mosquitto

   ```bash title="Restarting the Mosquitto service"
   sudo systemctl restart mosquitto
   ```

## Power Meter

Next, configure the power meter to publish measurements at regular intervals to the MQTT server, enabling data exchange and tracking.

### Configuration

1. Identify the IP address of your Raspberry Pi by executing the following command:

   ```bash title="Determining the primary IP address"
   hostname -I
   ```

   The resulting output should resemble the following:

   ```text title="Output"
   py@voron: $ hostname -I
   198.51.100.60 198.51.100.61 2600:1700:5430:87af::1106 2001:0db8:5dc9:b0ba:f8a8:7e3c:45e2:faab 2001:0db8:5dc9:b0ba:f8a8:7e3c:45e2:faac
   ```

   Take note of the primary IP address, **198.51.100.60**, displayed in the first column of the output. This information is essential for the next steps, so please document it for later use.

   :::note
   Keep in mind that the actual output may vary due to differences in system settings and configurations.
   :::

1. Open a web browser and enter the IP address of your Shelly device to access its web-based interface and configure settings.
1. Navigate to **Settings > MQTT** in the **Connectivity** section.
1. Configure the following settings:
    - **Enable**: Checked
    - **Connection type**: No SSL
    - **MQTT Prefix**: my-printer
    - **MQTT Control**: Enabled
    - **Generic status update over MQTT**: Enabled
    - **Server**: IP address of your Raspberry Pi (determined in step 1), followed by `:1883`, for example **198.51.100.60:1883**
    - **Client ID**: my-printer
    - **Username** and **Password**: Leave blank

   ![Shelly MQTT Settings](../../../../assets/guides/energy-usage-monitoring/shelly-mqtt-settings.png)
1. Click **Save Settings** to apply the changes. A restart of the Shelly might be required.

## Moonraker

Configure Moonraker to integrate additional sensor sources, enabling real-time data tracking in Mainsail and historical data analysis in the job history.

### MQTT Configuration

1. Execute the following command to access and modify the configuration file

   ```bash title="Editing the Moonraker configuration file"
   sudo nano ~/printer_data/config/moonraker.conf
   ```

1. Append the following configuration settings to the file to configure Moonraker to receive messages from the MQTT server

   ```ini title="moonraker.conf"
   [mqtt]
   address: 127.0.0.1
   enable_moonraker_api: False
   ```

### Sensor Configuration

1. Append the following configuration block to establish a sensor that subscribes to MQTT messages from the Shelly 1PM

   ```ini title="moonraker.conf"
   [sensor powermeter]
   type: mqtt
   name: Shelly 1PM
   parameter_power:
     units=W
   parameter_voltage:
     units=V
   parameter_current:
     units=A
   parameter_energy:
     units=kWh
   state_topic: my-printer/status/switch:0
   state_response_template:
     {% set notification = payload|fromjson %}
     {set_result("power", notification["apower"]|float)}
     {set_result("voltage", notification["voltage"]|float)}
     {set_result("current", notification["current"]|float)}
     {set_result("energy", notification["aenergy"]["total"]|float / 1000)}
   ```

   This configuration enables the extraction of key data points from Shelly 1PM status updates, including:

    - Current mains voltage
    - Current power draw
    - Current power usage
    - Total energy consumption (in kilowatt-hours)

1. Apply the new configuration by restarting Moonraker

   ```bash title="Restarting the Mooraker service"
   sudo systemctl restart moonraker
   ```

1. Confirm Data Exchange

   To ensure the successful publication of measurements from the power meter and Moonraker's ability to process them, navigate to the Mainsail Web UI for your printer.

   If the integration is functioning correctly, you should observe four new measurements from your sensor in the 'Miscellaneous Card' on the dashboard, as depicted in the screenshot below:

   ![Mainsail Sensor Data Display](../../../../assets/guides/energy-usage-monitoring/mainsail-sensor-data.png)

   This verification step confirms the accurate exchange of data between the power meter and Moonraker, enabling real-time monitoring and analysis of energy consumption.

   :::caution[Troubleshooting Data Exchange Issues]
   If the expected data fails to appear in the Web UI, some troubleshooting will need to be performed.

   <details>
   <summary>Troubleshooting steps</summary>

   1. Review the `moonraker.log` file for any configuration errors related to MQTT integration.
   2. Confirm that the power meter is publishing data in the expected format. Utilize a tool like [MQTT Explorer](http://mqtt-explorer.com/) to connect to the MQTT server and verify real-time updates and message content.

   </details>
   :::

### Historical Data

Moonraker allows tracking auxillary sensor data in the job history. To facilitate persisting this data additional history fields need to be configured for the sensor.

1. Execute the following command to access and modify the Moonraker configuration file

   ```bash title="Editing the Moonraker configuration file"
   sudo nano ~/printer_data/config/moonraker.conf
   ```

2. Enhance sensor definition with history fields

   Append the following configuration lines to the previously defined sensor:

   ```ini title="moonraker.conf"
   history_field_energy_consumption:
     parameter=energy
     desc=Energy consumption
     strategy=delta
     units=kWh
     init_tracker=true
     precision=6
     exclude_paused=false
     report_total=true
     report_maximum=true
   history_field_average_power:
     parameter=power
     desc=Average power draw
     strategy=average
     units=W
     report_total=false
     report_maximum=true
   history_field_max_power:
     parameter=power
     desc=Maximum power draw
     strategy=maximum
     units=W
     init_tracker=true
     report_total=false
     report_maximum=false
   history_field_average_current:
     parameter=current
     desc=Average current draw
     strategy=average
     units=A
     report_total=false
     report_maximum=true
   history_field_max_current:
     parameter=current
     desc=Maximum current draw
     strategy=maximum
     units=A
     init_tracker=true
     report_total=false
     report_maximum=false
   ```

   This modification adds fields for current draw, power usage, and energy consumption, which will be recorded in the job history upon completion of a print job.

3. Apply the new configuration by restarting Moonraker

   ```bash title="Restarting the Mooraker service"
   sudo systemctl restart moonraker
   ```

4. Verify data tracking in Mainsail

   To confirm the successful integration of power meter measurements and Moonraker's job history, access the Mainsail Web UI for your printer. If the configuration has been completed correctly, you should see additional columns in the Job History section, as depicted in the screenshot below:

   ![Mainsail Job History Display](../../../../assets/guides/energy-usage-monitoring/mainsail-job-history.png)

   :::note
   The newly added fields will be blank for existing entries in the job history. As new print jobs are completed, these fields will be populated with the relevant data.
   :::

## Further Reading

- Moonraker [sensor configuration](https://moonraker.readthedocs.io/en/latest/configuration/#sensor) documentation
- Shelly [web interface guide](https://kb.shelly.cloud/knowledge-base/shelly-pro-1pm-web-interface-guide)
```

- [ ] **Step 3: Delete the old Hugo source file and emptied image directory**

```bash
git rm content/docs/guides/energy-usage-monitoring.md
rmdir assets/images/guides/energy-usage-monitoring 2>/dev/null || true
rmdir assets/images/guides 2>/dev/null || true
```

- [ ] **Step 4: Build and verify**

Run:

```bash
npm run build
ls dist/docs/guides/energy-usage-monitoring-tracking/index.html
grep -c "<img" dist/docs/guides/energy-usage-monitoring-tracking/index.html
grep -o "<details>" dist/docs/guides/energy-usage-monitoring-tracking/index.html
grep -o "starlight-aside--caution\|callout-caution" dist/docs/guides/energy-usage-monitoring-tracking/index.html | head -1
grep -o "moonraker.conf" dist/docs/guides/energy-usage-monitoring-tracking/index.html | head -1
```

Expected: the guide page exists, the `<img>` count is 3, `<details>` is present, the caution-aside class grep matches something (same caveat as Task 6/7 — adjust the candidate class name if neither matches the actual rendered output), and `moonraker.conf` appears (confirms code-block title labels survived). Between Task 6 (note, danger), Task 7 (tip), and this task (caution), all four callout types have now been explicitly verified to render with type-specific styling, not just as plain text. Same manual image-loading check as Task 7.

- [ ] **Step 5: Commit**

```bash
git add -A src/content/docs/docs/guides/energy-usage-monitoring-tracking.md src/assets/guides/energy-usage-monitoring/
git commit -m "[TASK] Migrate Energy Usage Monitoring guide"
```

## Task 9: Fix the GitHub Actions deploy workflow

**Files:**
- Modify: `.github/workflows/deploy.yml`

- [ ] **Step 1: Rewrite the build job**

Replace the full contents of `.github/workflows/deploy.yml`:

```yaml
# Workflow for building and deploying an Astro/Starlight site to GitHub Pages
name: Deploy Starlight site to GitHub Pages

on:
  # Runs on pushes targeting the default branch
  push:
    branches:
      - gh-pages

  # Allows you to run this workflow manually from the Actions tab
  workflow_dispatch:

# Sets permissions of the GITHUB_TOKEN to allow deployment to GitHub Pages
permissions:
  contents: read
  pages: write
  id-token: write

# Allow only one concurrent deployment, skipping runs queued between the run in-progress and latest queued.
# However, do NOT cancel in-progress runs as we want to allow these production deployments to complete.
concurrency:
  group: "pages"
  cancel-in-progress: false

# Default to bash
defaults:
  run:
    shell: bash

jobs:
  # Build job
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - name: Setup Pages
        id: pages
        uses: actions/configure-pages@v4
      - name: Install dependencies
        run: npm ci
      - name: Build production website
        run: |
          npm run build \
            -- \
            --site "${{ steps.pages.outputs.origin }}" \
            --base "${{ steps.pages.outputs.base_path }}"
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./dist

  # Deployment job
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

Changes from the Hugo version: no Hugo CLI install, no Dart Sass install, no `submodules`/`fetch-depth` checkout options (Astro has no Hugo-module equivalent needing them), `npm ci` always runs unconditionally (Astro's `package-lock.json` always exists, unlike Hugo's optional lockfile), `--site`/`--base` replace `--baseURL`, and the artifact path is `./dist` instead of `./public`.

- [ ] **Step 2: Validate the YAML**

Run:

```bash
python3 -c "import yaml, sys; yaml.safe_load(open('.github/workflows/deploy.yml'))" && echo "valid YAML"
```

Expected: prints `valid YAML` with no error. (This only validates YAML syntax, not GitHub Actions semantics — full validation happens when the workflow actually runs after this branch merges.)

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "[TASK] Rewrite deploy workflow for Astro/Starlight"
```

## Task 10: Remove remaining Hugo/Doks files

**Files:**
- Delete: `config/`, `netlify.toml`, `hugo_stats.json`, `.hugo_build.lock`, `resources/`, `layouts/`, `assets/scss/`, `assets/jsconfig.json`, `assets/js/custom.js`, `assets/images/.gitkeep`, `assets/svgs/.gitkeep`, `content/` (if anything remains), `assets/` (if empty)

By this point every piece of content, branding, and configuration this repo actually used has already moved to its Astro/Starlight equivalent in Tasks 1-9. This task is pure deletion — confirm nothing unexpected remains before removing.

- [ ] **Step 1: Confirm content/ is fully migrated and list what's left in assets/**

Run:

```bash
find content -type f
find assets -type f
```

Expected: `content/` finds nothing (every file was removed in Tasks 4-8). `assets/` finds exactly six remaining files: `assets/scss/common/_custom.scss`, `assets/scss/common/_variables-custom.scss`, `assets/jsconfig.json`, `assets/js/custom.js`, `assets/images/.gitkeep`, `assets/svgs/.gitkeep` — all confirmed-empty Doks placeholders, none of them migrated anywhere because none had real content. If `find assets` shows anything else, stop and figure out what it is before continuing — don't delete something this plan didn't account for.

- [ ] **Step 2: Remove the remaining Hugo/Doks files and directories**

```bash
git rm -r config/ netlify.toml hugo_stats.json .hugo_build.lock resources/ layouts/ assets/scss/ assets/jsconfig.json assets/js/custom.js assets/images/.gitkeep assets/svgs/.gitkeep
rmdir assets/js assets/images assets/svgs 2>/dev/null || true
rmdir content assets 2>/dev/null || true
```

`git rm` on individual files (the three `.gitkeep`/`custom.js` removals) doesn't clean up their now-empty parent directories the way `git rm -r` on a whole directory does — without the extra `rmdir` calls for `assets/js`, `assets/images`, `assets/svgs`, the final `rmdir assets` would fail since those three empty directories would still be sitting inside it.

- [ ] **Step 3: Build and verify nothing broke**

Run:

```bash
npm run build
echo "exit: $?"
```

Expected: exits 0. This is the real test that nothing in `config/`, `layouts/`, or `assets/scss/` was secretly still load-bearing — Astro never read any of them, so removing them shouldn't change the build at all.

- [ ] **Step 4: Commit**

```bash
git commit -m "[TASK] Remove remaining Hugo/Doks files"
```

## Task 11: Full verification against the production base path

**Files:** none (verification only)

Every prior task's build check ran without `--base` set, which is exactly the condition under which the literal-absolute-path bugs this plan fixed would NOT have shown up. This task is the one that actually exercises the production configuration.

- [ ] **Step 1: Build with the real production base path**

```bash
npm run build -- --site "https://mjonuschat.github.io" --base "/voron-mods"
```

Expected: exits 0.

- [ ] **Step 2: Verify image src attributes are base-prefixed**

```bash
grep -c "<img" dist/docs/guides/automating-z-offset-adjustments/index.html
grep -o 'src="/voron-mods/_astro/[^"]*"' dist/docs/guides/automating-z-offset-adjustments/index.html
grep -c "<img" dist/docs/guides/energy-usage-monitoring-tracking/index.html
grep -o 'src="/voron-mods/_astro/[^"]*"' dist/docs/guides/energy-usage-monitoring-tracking/index.html
```

Expected: the `<img>` counts are 2 and 3 (matching Tasks 7/8), and the `src="/voron-mods/_astro/..."` grep returns that many matches on each page. Don't grep for the page's own slug (e.g. "automating-z-offset") inside the `src` value — `astro:assets` hashes filenames from the *image's* own basename (`prusaslicer-filament-settings.<hash>.png`, etc.), which has nothing to do with the page it's embedded on, so a slug-based grep would never match regardless of whether base-prefixing actually worked.

- [ ] **Step 3: Verify the homepage card links are base-prefixed**

```bash
grep -o 'href="[^"]*docs/guides[^"]*"' dist/index.html
```

Expected: every matched `href` starts with `/voron-mods/docs/guides/...`. If any link is missing the `/voron-mods` prefix, double-check Task 4's `LinkCard` `href` expressions actually use `import.meta.env.BASE_URL` as written and weren't accidentally hardcoded as literal strings during implementation.

- [ ] **Step 4: Verify the favicon link is base-prefixed, and the mask-icon link is the correct hardcoded absolute URL**

```bash
grep -o '<link rel="shortcut icon"[^>]*>' dist/index.html
grep -o '<link rel="mask-icon"[^>]*>' dist/index.html
```

Expected: the favicon `href` starts with `/voron-mods/favicon.svg` (Starlight's native `favicon` option is base-aware, confirmed via its source in Task 3 — this build's `--base /voron-mods` flag should now show up here, unlike the un-flagged builds in every earlier task). The mask-icon `href` is the unchanged hardcoded `https://mjonuschat.github.io/voron-mods/mask-icon.svg` — it doesn't respond to the `--base` flag at all, by design (see Task 3 Step 4), so this check is really just confirming the literal string is still there, not that base-prefixing happened.

- [ ] **Step 5: Verify URL structure matches the current site exactly**

```bash
ls dist/index.html dist/privacy/index.html dist/docs/index.html dist/docs/resources/index.html dist/docs/guides/index.html dist/docs/guides/optimized-bed-leveling-macros/index.html dist/docs/guides/automating-z-offset-adjustments/index.html dist/docs/guides/energy-usage-monitoring-tracking/index.html
```

Expected: all eight files exist — this is the full page inventory from the spec, confirming every page landed at its intended URL with no extras or omissions.

- [ ] **Step 6: Verify the sidebar lists all three guides, alphabetically**

```bash
grep -o 'href="[^"]*docs/guides/[a-z-]*/"' dist/docs/guides/index.html | sort -u
```

Expected: three sidebar links, one per guide. Alphabetically by filename, the order should be `automating-z-offset-adjustments`, `energy-usage-monitoring-tracking`, `optimized-bed-leveling-macros` — confirm the printed order matches (autogenerate sorts by filename, so this is really checking that all three guide files were picked up, not that some unrelated sort logic kicked in).

- [ ] **Step 7: Rebuild without the base override for local dev sanity, then report final status**

```bash
npm run build
git status --short
```

Expected: builds cleanly with no flags (confirming local `npm run dev`/`npm run build` still work without requiring the production flags), and `git status --short` shows a clean working tree (everything from this task was verification-only, no files changed).

Report: confirm all checks in Steps 2-6 passed, or describe exactly which one failed and what the actual output was instead.

A few things this plan cannot verify from the command line, and should be checked manually in a browser before considering the migration fully done:
- The `--sl-content-width` fix is visibly wider on a large viewport, and the right-hand Table of Contents doesn't overflow (Task 2 only confirmed the CSS property's *presence* in the build output, not its rendered effect).
- The converted `<details>`/`<summary>` disclosure blocks (Tasks 7-8) actually expand and collapse on click.
- All five images load and display correctly, not just that an `<img>` tag with a plausible-looking `src` exists (Step 2 confirmed the base prefix is present, not that the file at that path actually renders a real image).

- [ ] **Step 8: Squash-merge into gh-pages**

```bash
git checkout gh-pages
git merge --squash astro-starlight-migration
git commit -m "[TASK] Migrate site from Hugo/Doks to Astro/Starlight"
```

Expected: single new commit on `gh-pages` containing the full migration diff.

- [ ] **Step 9: Push and confirm the real GitHub Actions deploy succeeds**

```bash
git push origin gh-pages
```

This plan validated the rewritten workflow's YAML syntax (Task 9) but cannot trigger or observe an actual GitHub Actions run from this environment. After pushing, check the Actions tab on GitHub (or `gh run watch` if the `gh` CLI is authenticated) and confirm the "Deploy Starlight site to GitHub Pages" workflow completes both the `build` and `deploy` jobs successfully. If it fails, the most likely failure points are the `--site`/`--base` values not matching what `actions/configure-pages` actually outputs for this specific repo, or an `npm ci` failure from a `package-lock.json` that wasn't committed — check the build job's logs first.
