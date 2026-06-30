# Kanso — Design System Reference

> Source: `https://kanso.framer.media/` (Framer template, light variant)
> Captured: 2026-05-29 at 1440×900 viewport

## Executive summary

Kanso is a **minimalist, editorial design-studio aesthetic** built on a near-monochrome palette (off-white canvas, soft greys, deep near-black), generous whitespace, and a single sans-serif (Inter) used across an extreme size range — from oversized display headlines (~210 px) down to 14 px micro-labels. The visual language pairs **calm content with subtle structural cues**: numbered section counters (`(01)`, `(02)`…), an eyebrow slash (`/`) before every section title, soft 16 px rounded containers, and a small set of darker "panel" sections (services, testimonials, footer) to break rhythm. Motion is restrained — short 200 ms ease curves on color/opacity, hover reveals on cards, no parallax-y gimmicks.

---

## 1. Layout & Grid

### Page shell

| Token | Value |
|---|---|
| Page background | `#FFFFFF` |
| Outer padding (mobile-safe) | `40px` horizontal on `<main>` children |
| Section container | `max-width: 1600px`, padding `120px 40px` (top/bottom), centered |
| Hero container exception | `padding: 140px 40px 120px` |
| Section internal gap (default) | `80px` between heading-block and content-block |
| Services / dark-panel container | container padding `120px 80px`, sits inside `40px` outer gutter |
| Sticky nav header | `padding: 0 40px`, nav inner padding `6px`, height `45px` |

### Section structure

Every section follows the same vertical rhythm:

```
┌─ Section (1600px max, 40px gutters, 120px top/bottom) ──┐
│                                                         │
│  Eyebrow row:                                           │
│   "/  About us                                  (01)"   │   ← 14px, grey, full-width row, slash left, counter right
│                                                         │
│  H2 headline (54–64px Inter Medium)                     │
│  Optional sub-copy (18px grey)                          │
│                                                         │
│  ── 80px gap ──                                         │
│                                                         │
│  Content block (cards, list, grid, image)               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Grids observed

- **Selected Work**: 2-column grid, ~677 px each, 6 px column gap, project cards fill row.
- **Why us "Benefits"**: 4-column flex row, 6 px gap. Card widths vary (342 / 330 / 342 / 330) — feels like a fixed 2-column "feature module" duplicated.
- **Services list**: single-column vertical list inside a dark rounded panel; each row spans `1112 px` inside `120 80` panel padding; rows ~70 px tall.
- **Process**: 2-column layout — left column holds heading + CTA, right column holds 4 stacked cards (gap `6 px`, padding `32 px` per card).
- **Pricing**: 2 cards side-by-side (~647 px each); each card is split inner-left content / inner-right details list (inside one rounded shell).
- **Testimonials**: 3 cards in a row (~396 px wide × 380 px tall) inside a dark `1360 × 826` panel; carousel controls top-right.
- **FAQs**: 2-column layout — left for heading & CTA, right is a `646 px` accordion stack (6 px gap, 6 px outer padding).
- **Blog**: featured card (677 px, large) + 2 smaller stacked cards.

### Spacing scale (observed)

```
4   6   8   10   12   14   16   20   24   32   40   48   64   80   120   140
```

`6 px` is the canonical "tight gap" between sibling cards. `40 px` is the gutter. `80 px` is the rhythm between headline and content. `120 px` is the rhythm between sections.

---

## 2. Typography

Single typeface, one family throughout.

```css
font-family: Inter, "Inter Placeholder", sans-serif;
/* Tag chips use Inter Tight 700; everything else uses Inter */
```

### Type scale

| Role | Size | Line height | Tracking | Weight | Notes |
|---|---|---|---|---|---|
| Display / Hero `<h1>` | **210 px** | 189 px (~0.9) | `-14.73px` (-7%) | 500 | "Kanso®" — fills viewport width |
| Mega footer wordmark | **146 px** | 132 px | `-10.25px` | 500 | "Kanso® Studio" |
| Section H2 (default) | **54 px** | 59 px (1.1) | `-2.7px` (-5%) | 500 | About / Why us / FAQs |
| Section H2 (emphasis) | **64 px** | 70 px (1.1) | `-3.2px` (-5%) | 500 | Selected Work, Pricing, Services list items |
| Card title H3 (large) | **24 px** | 31 px (1.3) | `-0.96px` (-4%) | 600 | Process steps, "Play Showreel" |
| Card title H3 (small) | **18 px** | 23 px (1.3) | `-0.72px` (-4%) | 600 | Project name, FAQ question |
| Body / lede | **18 px** | 23 px | `-0.72px` | 500 | Service descriptions; muted grey in many places |
| Body default | **16 px** | 22 px (1.4) | `-0.64px` (-4%) | 500 | Most paragraphs |
| Body long-read | **16 px** | 22 px | `-0.48px` (-3%) | 400 | FAQ answer copy (lighter weight) |
| Meta / nav / micro | **14 px** | 17 px (1.2) | `-0.56px` (-4%) | 500 | Nav links, eyebrows, "(01)" counters, project year |
| Numeric stat / rating | 14 px | 15 px | `-0.42px` | 400 | "4.9/5" |
| Tag pill | **13 px** | 16 px | `normal` | **700** | "Insights", "Strategy" — uses **Inter Tight** |

### Weights in use

- `400` — long-form FAQ body, stat numerals
- `500` — **default** (body, nav, headings, eyebrows)
- `600` — small card titles & process step titles (Lune, Discover, Play Showreel)
- `700` — only on category tag chips (Inter Tight)

### Tracking rule

All Inter text uses **negative tracking** that scales with size:
- Display: `-7%`
- Headlines (54–64 px): `-5%`
- Body/meta: `-3% to -4%`

When recreating any heading, set `letter-spacing` to roughly `-0.05em` for h2 and `-0.07em` for hero.

---

## 3. Color system

The site exposes Framer-generated tokens but uses **8 colors total**. Map them by role:

### Raw tokens (from CSS custom properties)

```css
/* Pulled from :root */
--token-neutral-white:   #FFFFFF;     /* page background */
--token-neutral-50:      #F6F6F6;     /* page bg accent / nav bg base */
--token-neutral-100:     #EBEBEB;     /* card bg, sign-up input bg, button bg */
--token-neutral-100-90:  #EBEBEBE6;   /* nav background with 90% alpha (over blur) */
--token-neutral-300:     #A8A8A8;     /* tertiary text (muted-er) */
--token-neutral-500:     #757575;     /* secondary text / subhead grey */
--token-neutral-700:     #4D4D4D;     /* tertiary text on light bg */
--token-ink:             #121212;     /* dark panel bg (services, testimonials, footer) */
--token-ink-deep:        #0A0A0A;     /* primary text & near-black on light */
--token-ink-true:        #000000;     /* tag-chip text only */
```

### Semantic mapping

| Role | Value | Where it's used |
|---|---|---|
| Surface / page | `#FFFFFF` | body, default sections |
| Surface / soft | `#F6F6F6` | none in light theme directly (kept for tokens) |
| Surface / card | `#EBEBEB` | benefit cards, pricing input, sign-up input, secondary CTA bg |
| Surface / dark panel | `#121212` | services panel, testimonials panel, footer |
| Surface / true-dark | `#0A0A0A` | "Start a project" pill, dark benefit card, testimonial card inside dark panel |
| Surface / nav (translucent) | `rgba(235, 235, 235, 0.9)` + `backdrop-filter: blur(8px)` | sticky nav |
| Text / primary on light | `#0A0A0A` | headlines, body |
| Text / primary on dark | `#FFFFFF` | dark-panel headlines |
| Text / secondary | `#757575` | sub-copy, hero subtitle, FAQ body |
| Text / tertiary | `#4D4D4D` | testimonial quote, less-emphasis labels |
| Text / quaternary | `#A8A8A8` | service descriptions on dark, footer body, faint labels |
| Border / divider | (rarely used; layout relies on `6 px` gaps & `#EBEBEB` fills instead of borders) |
| Brand accent | _none_ | Kanso uses zero brand color — neutrality is the brand |

### Contrast notes

- Body text on light surfaces lands on `#0A0A0A` (essentially black) for very high contrast.
- On dark panels (`#121212`), primary is `#FFFFFF`; secondary drops to `#A8A8A8` — comfortably above WCAG AA for body.

---

## 4. Component inventory

### 4.1 Nav (sticky pill)
```
position: relative; (visually fixed-feeling via short page chrome)
header padding: 0 40px
nav: width 1360px, height 45px, padding 6px, gap 48px between groups
nav background: rgba(235,235,235,0.9)
backdrop-filter: blur(8px)
border-radius: 0 0 16px 16px   ← only bottom corners
```
- Left cluster: small monogram + live local time (`29 May, 4:29 pm`) at 14 px / `#4D4D4D`.
- Right cluster: text links at 14 px / 500 / `#0A0A0A`, separated by `48 px`.
- Trailing CTA: **dark pill button** (`#0A0A0A` bg, white text, `30 px` radius, `8 × 20 px` padding).
- Final "+" icon button to the far right (menu opener).

### 4.2 Buttons / pills

Three variants, all share `30 px` radius, `12 px` font, `6 px` icon gap:

```css
/* Primary (dark) */
background: #0A0A0A; color: #FFF;
padding: 8px 20px; border-radius: 30px; gap: 6px;

/* Secondary (light) — default for most CTAs */
background: #EBEBEB; color: #0A0A0A;
padding: 8px 20px; border-radius: 30px; gap: 6px;

/* Secondary large (in dark-panel context, e.g. "See pricing") */
background: #EBEBEB; color: #0A0A0A;
padding: 12px 24px; border-radius: 30px;

/* Pricing CTA "Get started" */
background: #EBEBEB; padding: 12px 24px; border-radius: 30px;
```

All buttons end with a trailing **`+` icon** (~6 px gap from label) — this is a signature treatment, used on every CTA except the dark nav button.

### 4.3 Section header block

```
┌──────────────────────────────────────────────────────┐
│ / About us                                    (01)   │  ← 14px / 500 / #757575
│                                                      │
│ We're a design studio focused on…                    │  ← H2 54px / 500
│ simple, purposeful, and elegant solutions.           │  ← inline span, color #757575 (same size)
└──────────────────────────────────────────────────────┘
```
- The H2 mixes black + grey text **inline** (no `<em>`/`<span>` class style — it's a literal `<span style="color:#757575">`). Use a `<span class="muted">` pattern.
- The eyebrow + counter row sits on its own line, full container width, justified ends.
- Section ordinal uses parentheses, lowercase zero-padded: `(01)`, `(02)`, … `(09)`.

### 4.4 Project card (Selected Work)

```
border-radius: 16px
overflow: hidden
background: #EBEBEB
padding: 6px 6px 12px
display: flex (column), gap: 12px
inner image: width 100%, aspect ~4:3 (665×499), object-fit: cover, no inner radius
meta row: title (18/600) on left, year + category (14/500/#4D4D4D) on right
```
- **Hover**: the title/category overlays the image bottom (image stays, metadata slides up and is rendered with light text over the photo). Net effect: card "fills" with media on hover; metadata is read against the image.
- Transition: `all` + `color 0.2s cubic-bezier(0.44, 0, 0.56, 1)`.

### 4.5 Service list row (dark panel)

Sits inside a `#121212` rounded panel (`16 px` radius, `120 × 80 px` padding).
```
each row: ~70px tall, full container width
left: H3 "Brand Identity" 64px / 600 / #FFFFFF
right: numeral "1" 64px / 600 / #4D4D4D (same size & weight, dimmer)
```
- No row divider line — rows separate by their natural type rhythm and the dim numeral on the right.
- The list is interactive (likely an accordion expanding to show the sub-bullets shown on the home page summary).

### 4.6 Benefit cards (Why us, 4-up grid)

`border-radius: 16px`, `overflow: hidden`, 4 cards in a row with `6 px` gap.

- **Card 1**: light bg (`#EBEBEB`), image at top, headline + CTA at bottom (`Purposeful Design for Modern Brands.` + small "Get started +" pill). List of bullets below image.
- **Card 2**: light bg, stat block ("4.9/5", "100+ Happy clients worldwide") + testimonial quote stacked. Mini-avatars row at top.
- **Card 3**: light bg, **stacked feature blocks** with small icon + title + body each (Streamlined Process, Scalable Design, 24/7 Dedicated Support). Each sub-block has subtle separation (likely a `1 px` rule or padding).
- **Card 4**: **dark** (`#0A0A0A`) bg, large faded portrait, "Design with intent. / No excess, no fluff." at the bottom in white.

The grid is intentionally a **mosaic** — different content templates living in same-sized shells.

### 4.7 Pricing card

```
container: #FFFFFF on light section (or #EBEBEB if inverted)
border-radius: 11px
inner: split 2-column — left (50%) for headline+description+price, right (50%) for feature list & CTA
left padding: 24 px
toggle pill (Monthly / Project based): 218×44, #EBEBEB bg, 30px radius, 6px inner padding
```
- Price: 64 px font, weight 600, the `/month` suffix in smaller secondary grey.
- Feature list: 16 px / 500, bullet via small "•" 4 px dot.
- "Get started" CTA: full-width-ish pill at bottom-right of right column.

### 4.8 Process card

```
background: #FFFFFF (sits in a 6-px-gap stack)
border-radius: 11px
padding: 32px
content: numeral top-right (24/600/#757575) | H3 title 24/600 + body 16/400
```
4 cards stacked vertically inside a 2-column section (heading left, cards right).

### 4.9 Testimonial card

Lives in a `#121212` panel. Card itself:
```
width 396 × height 380
background: #0A0A0A
border-radius: 16px
padding: 24px
```
- One card variant shows a **video thumbnail** with a centered Play circle + small avatar bottom-left.
- Other cards: 5-star row + rating top, blockquote middle, avatar+name+role bottom.
- Carousel chevrons (prev/next) sit at top-right of the panel as 32 px circular ghost buttons.

### 4.10 FAQ accordion

```
container (right column): 646 × 548, padding 6px, gap 6px (between rows)
each row collapsed: full-width 634 × 71
background: #FFFFFF, border-radius: 11px
question: 18px / 500 / -0.54px / #0A0A0A on left
"+" icon button on right (circular)
```
- Numbered ("1. ", "2. ") inline with the question text.
- Expansion likely uses height animation; icon rotates `+` → `×` on open.

### 4.11 Blog card

Featured (large) + 2 standard cards in a 3-column layout:
```
border-radius: 16px, overflow: hidden
image fills top portion, no padding around image
text block sits below image (or overlaid for featured)
tag chip top-right of image: #FFFFFF pill, 13px Inter Tight 700, padding ~6×12, full-rounded
date label 14/500/#757575 above title
title 18/600/#0A0A0A
description 16/400/#757575
```

### 4.12 Footer

```
background: #121212; color: white; full viewport width
padding: ~80px outer
display: huge wordmark "Kanso® Studio" (146 px) + 3-column meta below
columns: tagline + email/phone | newsletter form | nav links + social
newsletter input: #EBEBEB bg, 47px height, 33px radius (matches button radius)
```
Bottom-row legal links + "Designed in Framer / By Thaer" tagline.

---

## 5. Motion & animation

### Easing & duration

```css
/* Default transition observed on links/buttons */
transition: color 0.2s cubic-bezier(0.44, 0, 0.56, 1);
```

- `cubic-bezier(0.44, 0, 0.56, 1)` ≈ **easeInOutQuart** — symmetric, gentle, calm.
- Duration default: **200 ms**. Use this single curve+duration for everything unless specifically scrolling-driven.

### Interaction patterns observed

| Element | Behavior |
|---|---|
| Nav links | Subtle color shift on hover (no underline). Likely also a small Y-offset slide using duplicate text — note `<span>About</span><span>About</span>` pattern in DOM hints at a **two-line vertical hover swap** (the second `About` slides up to replace the first). |
| Project card | Image stays; metadata slides up & overlays bottom of image. ~200 ms. |
| Buttons | Color/background subtly shifts (likely darker grey on light pill, lighter on dark pill). |
| Tag chips | No hover (decorative). |
| Carousel arrows | Standard hover lift / fill darken. |
| FAQ row | Height auto-grow on expand; `+` rotates 45° to `×`. |
| Scroll | No parallax. Section reveals (subtle fade-in / Y-translate on first appearance) are likely present — recreate with `IntersectionObserver` + 400 ms ease-out fade-up. |

### The duplicate-text hover idiom

Many links repeat their label twice in DOM (`About About`, `Projects Projects`, `Start a project Start a project`). This is a Framer pattern for a **vertical-slide hover effect**: both copies stack inside an `overflow: hidden` box; on hover, the stack translates `-100%` Y so the second copy replaces the first. Recreate with:

```css
.link { overflow: hidden; height: 1em; line-height: 1em; }
.link__inner { display: flex; flex-direction: column; transition: transform .2s cubic-bezier(.44,0,.56,1); }
.link:hover .link__inner { transform: translateY(-1em); }
```

---

## 6. Visual language

### Border radii

A small, deliberate palette:

| Radius | Where |
|---|---|
| `0px` | full-bleed images inside cards (cards round, images don't) |
| `10–11px` | pricing card, process card, FAQ row, "Buy Template" floating CTA |
| `16px` | project cards, benefit cards, blog cards, testimonial card, dark panels, nav bottom |
| `30px` | buttons / pills |
| `33px` | sign-up button (slightly larger pill) |
| `40 / 65px` | rare; mostly for circular icon buttons |
| `100%` | avatars, circular icon buttons (the `+` in CTAs), prev/next chevrons |

> **Rule of thumb:** containers = `16 px`, inner inputs/cards = `11 px`, buttons = `30 px`, icon buttons = `100%`.

### Shadows

Used sparingly — only on **floating overlays** (the persistent "Buy Template — $99" sticky CTA, dropdown menus). Body content has **no shadows**; depth comes from background tints, not elevation.

```css
/* Floating CTA shadow */
box-shadow:
  rgba(0,0,0,0.02) 0 0.6px 0.6px 0,
  rgba(0,0,0,0.06) 0 2.3px 2.3px 0,
  rgba(0,0,0,0.25) 0 10px 10px 0;

/* Subtle dropdown / popover shadow */
box-shadow:
  rgba(0,0,0,0.17) 0 0.6px 1.6px -1.5px,
  rgba(0,0,0,0.14) 0 2.3px 6px -3px,
  rgba(0,0,0,0.02) 0 10px 26px -4.5px;
```

### Image treatment

- **Black & white / desaturated** photography dominates (hero portrait, About showreel, Card 4 portrait, blog featured) — but **not as a CSS filter**; the source images are toned.
- Project thumbnails are full color (Aren = saturated white hood, Lune = grey product).
- Images **always sit inside a rounded container**, the image itself is square-cornered and `object-fit: cover`.
- Aspect ratios cluster around **4:3** (project cards, blog) and **16:9** (showreel).

### Iconography

- Stroked, monoweight, geometric. Every CTA ends in a small `+` glyph in its own ~14 px circle.
- Stars (testimonials) are filled, deep grey/black.
- FAQ +/× toggle is the same `+` icon, no fill.
- No emoji, no illustrative icons.

### Special micro-pattern: section eyebrow

```html
<div class="eyebrow-row">
  <span>/</span>          <!-- 14px / 500 / #A8A8A8 -->
  <span>About us</span>   <!-- 14px / 500 / #0A0A0A -->
  <span class="ordinal">(01)</span>  <!-- 14px / 500 / #757575, justified right -->
</div>
```
This appears at the **start of every numbered section** and is the single most identity-defining motif on the site.

---

## 7. Replication notes — building a new page that feels native

If you're adding a page, follow these rules **exactly**:

1. **Container**: every section gets `max-width: 1600px`, `padding: 120px 40px`, `margin: 0 auto`. Never deviate from the 40 px outer gutter or the 120 px vertical rhythm.
2. **Always start a section with the eyebrow row** (`/ Section name … (NN)`), even for utility pages — it is the load-bearing identity element.
3. **Headlines are 54 px by default, 64 px for emphasized landing-style sections**. Always Inter 500, always negative tracking ~`-5%`, always line-height `1.1`. Mix in muted-grey words inline rather than using italics or color emphasis.
4. **Body is 16/500 with `-0.04em` tracking**. For long reading (FAQ-like answers, legal pages) drop weight to 400 and lighten tracking to `-0.03em` — never raise size.
5. **Two colors of text only on light bg**: `#0A0A0A` for primary, `#757575` for secondary. Use `#4D4D4D` and `#A8A8A8` only when explicitly de-emphasizing inside a card or on dark bg.
6. **CTAs are always pills**. Default is `#EBEBEB` bg + black text + trailing `+`. The single dark pill is reserved for the **primary** action on the page (nav, hero, footer newsletter).
7. **Cards live in groups of 2 / 3 / 4 with a 6 px gap, on a 16 px outer radius**. Never use shadows for card depth; differentiate with bg fill instead (light `#EBEBEB` vs dark `#0A0A0A`).
8. **Dark panels (`#121212`)** break rhythm every 3–4 sections. Use one when the content is a "feature list" or "social proof" block. Their inner padding jumps to `120 × 80`.
9. **Photography is desaturated B&W for portraits, full color for products**. Always rounded outer container, never CSS filter.
10. **Motion is 200 ms `cubic-bezier(0.44, 0, 0.56, 1)`**. Don't reach for spring or longer durations. The hover idiom for nav/CTA labels is the vertical-slide duplicate-text trick.
11. **No borders, no shadows, no dividers**. Depth and separation come from 6 px gaps and tinted surfaces only. The only shadow allowed is the floating sticky CTA's soft drop.
12. **End every section with whitespace, not a divider**. The 120 px bottom-padding does the job.
13. **Sticky floating CTAs** (right-side stacked pills) live on every page and use a white bg + soft drop shadow + 10 px radius — they are distinct from inline pills.
14. **Footer wordmark** at 146 px is the visual rhyme of the hero — every page should end on it.

### Minimal CSS starter

```css
:root {
  --bg: #FFFFFF;
  --surface: #EBEBEB;
  --surface-dark: #121212;
  --surface-darker: #0A0A0A;
  --text: #0A0A0A;
  --text-muted: #757575;
  --text-faint: #A8A8A8;
  --text-tertiary: #4D4D4D;
  --radius-card: 16px;
  --radius-inner: 11px;
  --radius-pill: 30px;
  --gap-tight: 6px;
  --gap-content: 80px;
  --gap-section: 120px;
  --gutter: 40px;
  --ease: cubic-bezier(0.44, 0, 0.56, 1);
  --dur: .2s;
}
html, body { background: var(--bg); color: var(--text); }
body { font-family: Inter, "Inter Placeholder", sans-serif; font-weight: 500; }

.container { max-width: 1600px; margin: 0 auto; padding: var(--gap-section) var(--gutter); }
.h1 { font-size: 210px; font-weight: 500; line-height: .9; letter-spacing: -.07em; }
.h2 { font-size: 54px; font-weight: 500; line-height: 1.1; letter-spacing: -.05em; }
.h2--lg { font-size: 64px; }
.h3 { font-size: 24px; font-weight: 600; line-height: 1.3; letter-spacing: -.04em; }
.h3--sm { font-size: 18px; }
.body { font-size: 16px; line-height: 1.4; letter-spacing: -.04em; }
.meta { font-size: 14px; line-height: 1.2; letter-spacing: -.04em; color: var(--text-muted); }

.pill { display:inline-flex; align-items:center; gap:6px; padding:8px 20px; border-radius:var(--radius-pill); background:var(--surface); color:var(--text); font-size:12px; transition: background var(--dur) var(--ease); }
.pill--dark { background: var(--surface-darker); color:#fff; }

.card { background: var(--surface); border-radius: var(--radius-card); overflow: hidden; padding: 6px 6px 12px; }
.panel-dark { background: var(--surface-dark); color:#fff; border-radius: var(--radius-card); padding: 120px 80px; }

.eyebrow-row { display:flex; justify-content:space-between; font-size:14px; color: var(--text-muted); margin-bottom: var(--gap-content); }
```

---

## 8. Quick-reference cheatsheet

| Thing | Value |
|---|---|
| Container | `max-width: 1600px; padding: 120px 40px;` |
| Font | `Inter, "Inter Placeholder", sans-serif` (weights 400/500/600) |
| Hero size | 210 / 189 / -7% / 500 |
| Headline | 54 / 60 / -5% / 500 |
| Body | 16 / 22 / -4% / 500 |
| Meta | 14 / 17 / -4% / 500 / `#757575` |
| Primary text | `#0A0A0A` |
| Secondary text | `#757575` |
| Card bg | `#EBEBEB` |
| Dark panel | `#121212` |
| Dark pill / accent | `#0A0A0A` |
| Card radius | 16 px |
| Inner radius | 11 px |
| Pill radius | 30 px |
| Tight gap | 6 px |
| Content gap | 80 px |
| Section padding | 120 px (top & bottom) |
| Transition | `0.2s cubic-bezier(0.44, 0, 0.56, 1)` |
| Shadow (only floats) | `0 0.6px 0.6px rgba(0,0,0,.02), 0 2.3px 2.3px rgba(0,0,0,.06), 0 10px 10px rgba(0,0,0,.25)` |

---

## Screenshot reference

All captures in `design-research/`:

| File | Section |
|---|---|
| `00-fullpage.png` | Full page composite |
| `01-viewport-hero.png` | Hero + nav |
| `02-about.png` | About + showreel |
| `03-projects.png` | Selected Work grid |
| `04-whyus.png` | Why us 4-card mosaic |
| `05-services.png` | Dark services list |
| `06-process.png` | 4-step process cards |
| `07-pricing.png` | Pricing card |
| `08-testimonials.png` | Dark testimonials panel |
| `09-faq.png` | FAQ accordion |
| `10-blog.png` | Blog 3-up |
| `11-footer.png` | Footer wordmark |
| `12-project-hover.png` | Project card hover state |
