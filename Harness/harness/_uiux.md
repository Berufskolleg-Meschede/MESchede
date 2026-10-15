# MESchede UI and UX guide

## Purpose and use in the harness

Read this file before creating or changing frontend screens, components, styling, or user flows. Apply it to MESchede work in this repository. This document defines the agreed design direction and the expected behavior of future changes; it does not imply that every requirement is already implemented.

The product is a Manufacturing Execution System for Berufskolleg Meschede. Users need to inspect production and delivery orders, recognize problems, maintain order data, and understand machine availability.

The agreed direction is **functional, restrained, industrial minimalism with natural typography**. The interface should feel deliberately built for daily workshop use. Prioritize readable data, clear actions, predictable interactions, and domain-specific content.

When implementing a change:

1. Identify the user's task and the information needed to complete it.
2. Reuse the existing layout, tokens, components, and terminology.
3. Implement the interaction, including loading, empty, failure, and success states.
4. Check keyboard use, responsive layout, and visual consistency.
5. Verify the changed behavior and keep this guide aligned with intentional design changes.

Do not redesign unrelated screens, replace the visual language, add libraries, or invent data to fill a layout. Explicit project-owner instructions may change this guide; record the resulting decision here.

## Design principles

- Function comes first. Every prominent element should help users understand or act on production data.
- Keep decoration quiet. Use alignment, spacing, typography, and thin borders to establish hierarchy.
- Use color sparingly and consistently. Reserve the warm primary accent for important actions and focus; use muted status colors for state.
- Make tables comfortable to scan. Keep IDs, articles, quantities, statuses, and actions aligned.
- Use familiar controls and explicit labels. Users should not have to discover gestures or interpret decorative icons.
- Keep important information visible. Minimalism must not remove labels, units, error explanations, or useful context.
- Use real manufacturing terminology. Avoid generic dashboard filler, marketing copy, or invented operational metrics.
- Make changes predictable. Preserve context, show pending actions, and report failures where users can recover.

## Visual boundaries

Do not introduce:

- Glowing badges, neon colors, pulsing status lights, or animated counters.
- Staggered card or table entrances, zooming dialogs, or decorative motion.
- Decorative gradients, glass effects, large drop shadows, or background illustrations.
- Oversized display numbers, condensed display fonts, or uppercase labels with wide tracking throughout the interface.
- A different bright accent for every metric, rainbow charts, or a card around every individual data point.
- Large pill-shaped panels, ornamental icons, decorative technical textures, or marketing-style hero sections.

Thin borders, subtle hover colors, visible focus outlines, and small overlay shadows are appropriate. A keyboard focus indicator serves interaction and must remain visible.

## Color system

The current default is a graphite dark interface. Use semantic Tailwind tokens backed by `app/globals.css`. Change shared tokens centrally instead of introducing local variations of background or text colors.

| Token | Current value | Role |
| --- | --- | --- |
| `background` | `#202423` | Application canvas |
| `foreground` | `#eef0ee` | Primary text |
| `card` | `#282d2b` | Tables and grouped content |
| `card-foreground` | `#eef0ee` | Text on panels |
| `popover` | `#2d3230` | Menus and dialogs |
| `popover-foreground` | `#eef0ee` | Text on overlays |
| `primary` | `#d99c68` | Main actions and warm accent |
| `primary-foreground` | `#202423` | Text on primary actions |
| `secondary`, `muted`, `accent` | `#343b37` | Hover, selected, and subdued surfaces |
| `secondary-foreground`, `accent-foreground` | `#eef0ee` | Text on these surfaces |
| `muted-foreground` | `#acb5ae` | Supporting text and metadata |
| `destructive` | `#e79b93` | Errors and destructive actions |
| `border` | `#434b46` | Structural separators |
| `input` | `#59635c` | Control boundaries |
| `ring` | `#d99c68` | Keyboard focus |
| `sidebar` | `#252a27` | Navigation surface |
| `sidebar-accent` | `#343b37` | Active navigation |
| `sidebar-border` | `#434b46` | Navigation separators |

Sidebar foreground, primary, and ring tokens match the equivalent main tokens. Chart tokens currently use `#d99c68`, `#92afbc`, `#9eb5a1`, `#b7b0a0`, and `#e79b93`; their presence does not justify adding charts.

The stylesheet also contains light-theme fallback tokens. A complete light-theme flow or theme switcher has not been designed. Do not infer that it is part of the current scope.

## Typography

- Main font: `Arial, Helvetica, sans-serif`. Use the system stack without downloading fonts.
- Technical identifiers: `"SFMono-Regular", Consolas, "Liberation Mono", monospace`.
- Page titles: 24 px, semibold, with slight negative tracking (`text-2xl font-semibold tracking-tight`).
- Section titles: 16 px, semibold (`text-base font-semibold`).
- Dialog titles and brand: 18 px, semibold.
- Main UI and table text: 14 px. Supporting metadata, table headers, and status labels: 12 px.
- Metric values: 24 px, semibold, with tabular numerals.
- Use normal sentence case and natural spacing. Preserve German noun capitalization.
- Reserve monospace for order IDs and machine identifiers. Labels, navigation, forms, and explanatory copy use the main font.
- Right-align comparable numeric columns and use `tabular-nums`. Keep units visible.
- Maintain legibility at browser zoom and on small screens. Do not shrink text to fit a layout.

## Layout, spacing, and surfaces

- Desktop shell: 240 px left navigation (`md:w-60`) with a vertically scrolling main content area.
- Below the medium breakpoint, place navigation above the content in a horizontal, scrollable row.
- Page container: `mx-auto max-w-7xl space-y-6 p-5 md:p-8 lg:p-10`.
- Use a restrained spacing scale: 4, 8, 12, 16, 20, 24, 32, and 40 px.
- Typical section padding: 20 px horizontally and 16 px vertically.
- Page headers have a thin bottom border, one clear title, and a short supporting line when useful.
- Panels use `bg-card`, a 1 px `border-border`, and `rounded-sm`.
- The base radius token is 6 px; `rounded-sm` resolves to 2 px and standard controls may use 6 px.
- Group summary values into a single strip with thin separators. Use two columns on small screens and four on larger screens.
- Use larger whitespace between tasks or sections and smaller spacing within a related group.
- Let actions wrap naturally. Keep tables horizontally scrollable within their own container; avoid horizontal scrolling of the entire page.
- Preserve useful columns on small screens. Do not hide the order status, quantity, or available actions to make a table fit.

## Navigation and information architecture

| Route | Navigation label | Purpose |
| --- | --- | --- |
| `/` | — | Redirect to `/dashboard` |
| `/dashboard` | Übersicht | Operational overview |
| `/production-orders` | Fertigungsaufträge | Production order management |
| `/delivery-orders` | Lieferaufträge | Delivery order management |
| `/analytics` | Analysen | Observed production and delivery runs, quantities, and durations |

The dashboard page title is **Betriebsübersicht**. The brand is **MESchede**, with a small **MES** descriptor and **Berufskolleg Meschede** below it.

Mark the active navigation item with a subtle filled surface, stronger text, and `aria-current="page"`. Use icons alongside visible labels. Keep the same navigation order across screens.

The existing `/machines` route is an empty placeholder and is not in navigation. Machine information currently lives on the dashboard. Add a dedicated page only when its purpose and functionality are implemented.

## Dashboard behavior

Order content by operational usefulness:

1. Page heading and a short explanation.
2. A compact summary strip: **Offene Aufträge**, **In Bearbeitung**, **Aufträge mit Fehler**, **Maschinen online**.
3. An open-orders table as the main content.
4. Machine availability and article quantities below it.

Open orders combine production and delivery orders and exclude `completed`. Sort `error` first, then `in_progress`, then `pending`, with ascending ID within each status. Show the order ID, area, article, quantity, and status.

Production and delivery IDs may overlap. Keep the area visible and use a composite identity when combining records. Order links currently lead to the corresponding order list; they do not open a detail view. Do not present them as detail links unless that behavior is implemented.

Machine rows show name, technical ID, type, and a readable online/offline status. Display the online count as a fraction, such as `3 / 4`.

The current **Geplante Stückzahlen** section sums quantities from all production orders by article, including completed orders, and explicitly says **Summe aller Fertigungsaufträge je Artikel**. This is an aggregate of order quantities, not a measure of remaining work, actual output, throughput, or completion. Rename it or change its calculation if the intended meaning changes.

## Analytics behavior

The analytics page lists persisted production and delivery runs separately and filters them by date range and order type. Show planned and actual quantities in distinct columns. Compute processed units from confirmed good plus defective results only; if either result is unknown, display the result as unknown. Never substitute planned quantity for produced quantity. Derive elapsed duration from observed start and end timestamps only. For a run that has an observed start but no end, show an explicitly provisional duration; without a start observation, show duration as unknown.

Quantity bars are thin, static, and subdued (`#98aaa0` on a secondary surface). Visible article names and quantities must communicate the data without requiring the bars. Do not add donuts, gauges, or animated charts merely to decorate the dashboard.

## Order management screens

- Use the same shared screen pattern for production and delivery orders.
- Place the page title and total count at the top, with **Neuer Auftrag** as the main action.
- Show compact status totals for all orders, independent of search results.
- Place article/order search and a status filter directly above the table.
- Default the status filter to **Alle Status**.
- Search is trimmed, case-insensitive, and matches article names, raw and padded order IDs, and article IDs.
- Combine search and status with AND: results must satisfy both controls.
- Display a result count such as **2 von 5 Aufträgen**, updated through a polite live region.
- Keep controls visible when no results match so users can adjust them.
- Default columns: **ID**, **Artikel**, **Menge**, **Status**, **Aktionen**.
- Format order IDs as `#0001`; padding is a minimum width and must not truncate larger IDs.
- Use article names where available and `Artikel #<id>` as the fallback.
- Right-align quantities and display **Stk.** beside them.
- Keep hover feedback subtle. Rows must not imply that they are clickable unless they support a row action.
- Place secondary row actions in an end-aligned menu with **Bearbeiten** and **Löschen**.
- Give the icon-only menu an accessible name such as **Aktionen für Auftrag 4**.

For future persistent deletion, provide a reversible undo flow or an explicit confirmation identifying the affected order. The current demo screen deletes immediately and has no undo; it must not be treated as the reference behavior for irreversible production data changes.

## Forms and dialogs

- Reuse the shared order dialog for create and edit.
- Titles: **Neuer Auftrag** and **Auftrag bearbeiten**.
- Provide a short dialog description and visible labels for **Artikel**, **Menge**, and **Status**.
- Connect each label to its control with matching `htmlFor` and `id`.
- Article selection must reference an available article. Never silently submit article ID `0`.
- Quantity is a required positive integer: minimum `1`, step `1`, validated before saving.
- New orders default to quantity `1`, status `pending`, and the first available article. Edit forms initialize from the selected order.
- Use **Erstellen** for create, **Speichern** for edit, **Abbrechen** for cancel, and **Speichert…** while a save is pending.
- Disable duplicate submissions while saving. Disable creation when prerequisite article data is unavailable.
- Keep the form open with its values intact if saving fails. Explain the failure inside the dialog.
- Update the list from the successful API response and close the dialog after success.
- Support Enter to submit through a real form. Keep Cancel separate from submission.
- Use the existing dialog primitive for focus containment, keyboard dismissal, and focus restoration.
- Use a restrained overlay and small shadow. Avoid animated opening or closing effects.

When adding asynchronous flows, prevent competing actions during submission or ensure that dismissal cannot produce stale state or duplicate changes.

## Status vocabulary and presentation

| Data value | Visible label | Dot color |
| --- | --- | --- |
| `pending` | Ausstehend | `#c7b485` |
| `in_progress` | In Bearbeitung | `#92afbc` |
| `error` | Fehler | `#e79b93` |
| `completed` | Abgeschlossen | `#9eb5a1` |
| `online` | Online | `#9eb5a1` |
| `offline` | Offline | `#939c95` |

Use a small static 6 px dot beside a 12 px readable label. Color supplements text; it must never be the only indicator. Unknown statuses display their supplied text with a neutral dot. Preserve the API values and use German labels only for presentation.

Offline means unavailable; do not imply a fault or cause that the data does not provide. Completed means the order has that status; do not invent completion timestamps or progress percentages.

## Loading, empty, failure, and success states

- Loading: use short contextual text such as **Lade Aufträge…**. Dashboard metrics use `—` until available.
- Empty dataset: explain that no records exist, for example **Keine Aufträge vorhanden.** Keep a valid create action available.
- Empty filter result: use **Keine Aufträge für diese Suche gefunden.** Do not imply that records were deleted or that loading failed.
- Failed data load: show a visible error and a useful recovery action or instruction. Unavailable data must not be presented as confirmed zero values.
- Failed mutation: keep the current data and explain that the requested action did not complete.
- Success: reflect the confirmed change in the relevant list and counts. Do not show success before the operation completes.
- Avoid indefinite loading states, silent promise failures, and raw backend exceptions in product copy.
- Preserve input when recovery is possible. Clear stale errors when starting a new action.

Use polite live announcements for changing result counts and alerts for failures. Do not add loud success toasts for every routine action when the change is already obvious in the interface.

## Copy and terminology

The product UI is in German. Keep terminology consistent across navigation, headings, tables, dialogs, and error messages.

- Prefer **Fertigungsaufträge**, **Lieferaufträge**, **Artikel**, **Menge**, **Status**, and **Maschinen**.
- Use short action verbs and concise, specific messages.
- Explain what happened and what the user can do next.
- Avoid marketing language, playful operational messages, unexplained acronyms, and technical implementation details in normal workflows.
- Show units beside values. Format future dates and numbers consistently for German readers.
- Include timestamps or freshness indicators only when backed by real data. Never imply live connectivity from a static demo.

## Accessibility and responsive interaction

- Use semantic navigation, headings, sections, tables, buttons, links, and forms.
- Keep one main page heading and a logical section hierarchy.
- Make every action keyboard reachable with a visible focus indicator.
- Preserve native link and button behavior; use links for navigation and buttons for actions.
- Label inputs explicitly. Give icon-only controls meaningful accessible names.
- Hide decorative icons, dots, and duplicate data bars from assistive technology.
- Keep status meaning in text and ensure text and controls remain distinguishable from their backgrounds.
- Maintain usable hit areas; existing row action buttons are 32 px and standard buttons are 36 px. Increase controls where touch use requires it.
- Check long German labels, long article names, large IDs, large quantities, empty tables, and narrow screens.
- Preserve dialog focus behavior and ensure overflowing content remains reachable.
- Respect `prefers-reduced-motion`. Keep essential information independent of animation and hover.

## Motion and icons

Use Lucide icons with a consistent 1.5 px stroke and generally 14–16 px size. Icons support actions and labels; do not give every section a decorative icon.

Allow brief, subtle color transitions for hover and focus. Avoid layout shifts, counter animations, pulsing, staggered reveals, and zoom/slide effects on menus or dialogs. New motion needs a functional reason.

## Implementation conventions

The frontend uses Next.js App Router, React, TypeScript, Tailwind CSS, Radix primitives, and Lucide icons.

| Location | Responsibility |
| --- | --- |
| `app/globals.css` | Semantic colors, fonts, shared CSS, reduced-motion handling |
| `app/layout.tsx` | Default dark theme, application shell, document language |
| `components/sidebar.tsx` | Brand, responsive navigation, active-route treatment |
| `components/stat-card.tsx` | Compact neutral summary values |
| `components/status-badge.tsx` | Status vocabulary and static indicators |
| `components/orders-section.tsx` | Shared order table, filters, forms, and mutations |
| `components/ui/` | Reusable accessible UI primitives |
| `app/dashboard/page.tsx` | Operational overview and its data calculations |
| `lib/types.ts` | Domain types and API status values |
| `lib/api.ts` | Data access and current demo behavior |

Use `cn` from `lib/utils.ts` when composing conditional classes. Prefer semantic utilities such as `bg-card`, `text-muted-foreground`, and `border-border`. Reuse existing primitives rather than recreating their accessibility behavior. If a design value becomes shared, move it into a central token or component.

Keep client components focused on interactive behavior. Avoid new font downloads, animation frameworks, chart libraries, or design systems unless required by an approved feature. Preserve create, edit, delete, filtering, and navigation behavior when restyling.

## Current scope and implementation gaps

These facts describe the current implementation; they are not permission to preserve weak behavior in future work:

- `USE_MOCK` is currently `true` in `lib/api.ts`. Data and edits live in memory and reset on full reload. Persistence and live machine telemetry are not implemented.
- A localhost backend URL and endpoint paths exist, but end-to-end live integration is not verified. Article and machine endpoints required by the frontend are not currently registered in the checked-in backend entry point. Changing `USE_MOCK` alone does not establish a working integration.
- The `/machines` page is an empty placeholder.
- Dashboard order links open category lists, not individual records.
- Delete currently acts immediately, without confirmation, pending feedback, or undo.
- Order summary counts initially display zero while loading; the dashboard already uses `—`. Future work should distinguish unknown values from confirmed zero consistently.
- A failed order load can still show the normal empty-table message beneath its error. Future work should give unavailable data its own table state.
- Saving disables the submit button, but other dialog controls and dismissal are not fully locked during the request. Improve this when supporting slower or persistent operations.
- The quantity section aggregates all production orders; it is not a measurement of unfinished work.
- Full keyboard, touch, zoom, and assistive-technology audits have not been completed. The existing primitives and labels are a starting point, not a certification.

Do not claim production readiness, live synchronization, persistence, or complete accessibility based on the appearance of the prototype.

## Issue 29: agreed order overview and recovery

The following is agreed target behavior for issue #29; it does not change the current implementation gaps described above. The detailed contract and acceptance criteria are in `../../docs/specs/issue-29-order-production-overview.md`.

- Extend the existing production and delivery pages as separate operational views. Distinguish waiting MES orders from product units belonging to the active run.
- Keep the dashboard as a separate, read-only summary of both areas. Retain the order type beside IDs and links so equal IDs cannot be confused.
- Show planned, processed, successful, and failed quantities separately. Missing product results remain visibly incomplete; unknown quantities are not confirmed zero values.
- Mark connectivity and freshness independently from the order's last known business state. Do not switch silently to demo data after a connection failure.
- Display unresolved run reviews when opening the app and after reload. A dashboard warning links to the corresponding order page; review inputs live on that page.
- The review records the run outcome and known successful/failed quantities without a required explanation or free-text note. Unknown quantities remain unknown, and manual results are labelled as manual.
- Reviewing a run does not send PLC start, stop, or reset commands. Open required reviews block new starts of both order types; resolving a review alone does not prove machine readiness.
- Display one shared dispatch order across production and delivery, oldest accepted first. The MES allows only one active dispatch across both types.
- Manual order creation/start belongs to the separate issue #30. This overview work does not turn the demo status selector into an authoritative live-run control.

## Issue 30: agreed manual order entry

The following is agreed target behavior, not an implementation claim. The contract and acceptance criteria are in `../../docs/specs/issue-30-manual-order-start.md`.

- Add **Neuer Auftrag** to both order pages and use one shared entry/review flow. Keep the dashboard read-only.
- Show business order ID and PLC order number as separate editable fields, each with an automatically suggested unused value. Suggestions do not reserve identifiers; conflicts remain visible and require renewed confirmation after changes.
- Support multiple product rows with a quantity per row. Preserve visible row order when creating units; show total quantity and the confirmed capacity limit.
- Select products from the authoritative PLC specifications catalog. Do not default silently to a product or substitute mock articles after a catalog failure.
- Read product choices from the persistent catalog mirror. **Produktdaten abgleichen** explicitly requests a PLC read and database synchronization, without submitting an order. Keep existing input after synchronization; validate changed ID/text pairs again before admission. Failed or stale catalog data block new orders while retaining the last known products.
- Offer an editable serial start number; serials increase across all product rows within that order. Show the resulting range and reject overflow.
- Prefill editable date and time from local plant time. Send date/time without a timezone offset and keep planned values separate from observed run timestamps.
- Customer number is optional. Priority and parameters are editable under **Weitere Angaben**, using model defaults; priority does not reorder MES FIFO.
- Show all effective values in **Auftrag prüfen** before **Auftrag annehmen**. Entry-step submission only opens the summary.
- Lock editing, repeat confirmation, and dialog dismissal during submission. Preserve values after a confirmed rejection.
- Treat accepted, waiting for start confirmation, confirmed running, and failure/review as distinct states. `202` alone cannot confirm PLC start.
- After an uncertain response or reload, check stored admission before retry. Keep the attempted identifiers and full payload unchanged; when checking fails, offer another check and block retries of that attempt.
- After acceptance, refresh the list and keep the accepted order's detail reachable and updated independently of filters and pagination. A refresh failure does not erase confirmed acceptance.

## Completion checklist for UI changes

Issue #29 completion displays mapped successful and failed unit results. A
correlated completed PLC order assumes success for missing or unmapped unit
signals and does not require a manual review. Keep the quantity origin visible
when the UI labels assumed success. If a stored completion is already at PLC
idle after a manual command reset, show it as completed and clear the stale
review notice.

Before considering a UI or UX change complete:

- The screen follows the industrial minimal direction and central tokens.
- Typography, spacing, borders, and status meanings match related screens.
- Primary tasks are obvious and all displayed controls perform their stated actions.
- Loading, empty, no-match, error, pending, and success states are handled where relevant.
- Search, filters, form validation, and mutations preserve context and remain consistent.
- Keyboard focus, labels, result announcements, and dialog behavior are checked.
- Narrow layouts and long or unusual domain data remain usable.
- The rendered screen has been inspected; visual verification is distinct from compilation.
- Run `npm run lint` and `npm run build` for code changes; verify the affected interactions in the browser when available.
- Confirm the development server serves the latest CSS before judging colors or typography.
- Report limitations honestly and update this guide if the agreed direction changes.
