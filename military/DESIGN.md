# Design system — Military Proposal Builder

Every color, font size, spacing value and corner radius in `index.html` comes from the tokens
below (declared as CSS custom properties on `:root`). No ad-hoc values in markup or JS templates.

## 1. Palette (restrained: one brand blue, one navy, greys, three semantic colors)

| Token | Value | Use |
|---|---|---|
| `--navy-900` | `#141C30` | Header background, dark surfaces |
| `--navy-800` | `#1F2A44` | Primary dark button, table header, footer |
| `--navy-700` | `#2B3A5C` | Dark hover |
| `--blue-600` | `#0077BB` | Primary button hover / pressed |
| `--blue-500` | `#0092E4` | Primary button, links, selected chip, focus ring (Wilkins brand blue) |
| `--blue-100` | `#D6ECFB` | Selected row tint, info panel border |
| `--blue-50`  | `#EEF7FD` | Selected row / info panel background |
| `--grey-900` | `#0F172A` | Body text |
| `--grey-700` | `#334155` | Secondary text |
| `--grey-500` | `#64748B` | Muted text, captions (min on white: 4.6:1) |
| `--grey-300` | `#CBD5E1` | Borders (strong) |
| `--grey-200` | `#E2E8F0` | Borders, dividers |
| `--grey-100` | `#F1F5F9` | Page background, subtle fills |
| `--white`    | `#FFFFFF` | Cards, inputs |
| `--green-600` / `--green-50` | `#15803D` / `#ECFDF5` | Success, profit, "current card" badge |
| `--amber-700` / `--amber-50` | `#B45309` / `#FFFBEB` | Warnings: reconfirm, unsaved edits |
| `--red-600` / `--red-50`     | `#DC2626` / `#FEF2F2` | Errors, destructive actions |

On dark backgrounds (`--navy-*`) text is `--white` at 100% for primary and 72% for secondary.
Never place `--grey-500` on navy. Category accents are 4 px left borders only, never text.

## 2. Type (system UI stack, tabular numerals for money)

| Token | Size / line | Weight | Use |
|---|---|---|---|
| `--text-xs`  | 0.75rem / 1.35 | 500–600 | Badges, table captions, help text |
| `--text-sm`  | 0.875rem / 1.45 | 400–600 | Default body, inputs, buttons |
| `--text-md`  | 1rem / 1.5 | 600 | Card titles, base names |
| `--text-lg`  | 1.125rem / 1.4 | 700 | Section headings, totals |
| `--text-xl`  | 1.375rem / 1.3 | 700 | Page title |

Hierarchy on every panel: one `--text-lg` heading, `--text-md` item titles, `--text-sm` body,
`--text-xs` metadata. Money uses `font-variant-numeric: tabular-nums`.

## 3. Spacing (4 px base)

`--sp-1` 4 px · `--sp-2` 8 px · `--sp-3` 12 px · `--sp-4` 16 px · `--sp-5` 24 px · `--sp-6` 32 px.
Card padding `--sp-4` (mobile) / `--sp-5` (desktop). Gaps between cards `--sp-4`. Inline gaps `--sp-2`.

## 4. Radii and elevation

`--r-sm` 6 px (inputs, chips, badges) · `--r-md` 10 px (buttons, rows, panels) · `--r-lg` 14 px (cards) · `--r-full` pill.
`--shadow-sm` for cards, `--shadow-lg` for the mobile menu and toasts. Nothing else casts a shadow.

## 5. Components

**Buttons** (`.btn`): 40 px tall (44 px on touch), `--r-md`, `--text-sm` 600, padding 0 `--sp-4`.
Variants: `.btn-primary` (blue fill, white text), `.btn-dark` (navy fill), `.btn-secondary` (white,
grey border), `.btn-ghost` (transparent, blue text), `.btn-danger-ghost`. States for all:
hover (darker fill / grey-100), pressed (`transform: translateY(1px)`, darkest fill), focus-visible
(2 px blue ring offset 2 px), disabled (40% opacity, no hover, `cursor: not-allowed`), busy
(`.is-busy` shows a spinner and disables). Each view has exactly one primary button.

**Inputs** (`.input`, `.select`): 40 px, `--r-sm`, grey-300 border, white fill; focus = blue border
+ ring; `.is-invalid` = red border + `.field-error` message directly below; compact `.input-sm`
(32 px) inside table rows only.

**Cards** (`.card`): white, grey-200 border, `--r-lg`, `--shadow-sm`. Base cards inside the media
panel use `.subcard` (grey-200 border, `--r-md`, no shadow).

**Chips** (`.chip`): pill, `--text-xs` 600, 32 px tall, grey border; `.is-on` = blue fill white text.
**Badges** (`.badge`): pill, `--text-xs` 600, tinted background + dark text of the same hue.
**Rows** (`.row`): hover grey-100; `.is-on` blue-50 background; 4 px category accent on the left.

## 6. Layout and breakpoints

- ≥ 1024 px: three columns (targets 3 / media 6 / proposal 3 of 12), max width 1700 px.
- < 1024 px: single column with a fixed bottom tab bar (Targets · Media · Proposal); only the active
  panel is shown, switching with a 150 ms fade. Header actions collapse into a menu button.
- No element may exceed the viewport width; tables inside the pricing editor become stacked cards
  below 768 px. All sizing is `rem`/percent so text zoom up to 200% reflows instead of clipping.
- Tap targets ≥ 44 × 44 px on touch devices (`@media (pointer: coarse)`).

## 7. Motion

150 ms `ease-out` for hover/fade/menu; 200 ms for panel switches; details chevrons rotate 90°.
`prefers-reduced-motion: reduce` disables all transitions.

## 8. States

- Loading: full-panel skeleton while data indexes; buttons show `.is-busy` while exporting.
- Empty: illustrated message + the one action that fills the panel.
- Error: red panel with the message and a retry action (missing libraries, unreadable file).
- Forms: inline field errors, toast on success (green) / failure (red) / info (navy).
