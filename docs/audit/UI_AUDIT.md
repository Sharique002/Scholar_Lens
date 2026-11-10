# Scholar Lens — Comprehensive UI/UX Audit & Alignment Report

**Document Version:** 1.0.0  
**Audit Date:** November 6, 2026  
**Auditor:** UI/UX Engineering Lead & Frontend Architect  
**Scope:** Design System Integrity, Layout Shell, Templates, Component Tokens, Alignment, and Responsiveness  

---

## 1. Executive Summary & Root Cause Analysis

Scholar Lens currently exhibits a dual design system conflict resulting from an architectural evolution:
1. **Legacy Design System (`static/css/style.css` - 57,688 bytes):**
   - Built on a **neo-brutalist aesthetic** characterized by heavy `2px` to `3.5px` solid black borders (`var(--ink-black)`: `#141416`), hard-edged offset drop shadows (`box-shadow: 4px 6px 0 var(--ink-black)`), rounded pill geometry (`border-radius: 9999px` / `28px`), and a vibrant pastel palette (yellow `#FFDD33`, pink `#FF3388`, cyan `#35E0D0`, mint `#86E8DC`, purple `#8B5CF6`).
2. **Institutional Design System (`static/css/ums.css` - 14,852 bytes):**
   - Designed around the **LPU UMS university portal specification**: Primary Maroon (`#9B2335`), Dark Maroon (`#7A1B29`), Maroon Tint (`#FBEFF1`), Primary Action Orange (`#F37021`), Orange Hover (`#E0601A`), Neutral Canvas (`#F5F5F7`), Card White (`#FFFFFF`), Border Neutral (`#E2E4E8`), Text Ink (`#1F2328`), and Muted Text (`#5B6270`).
   - Geometric foundation uses subtle, professional borders (`1px solid #E2E4E8`), modern elevation shadows (`0 1px 3px rgba(0, 0, 0, 0.05)`), and clean institutional radius tokens (`4px` to `8px`).

Because `templates/base.html` loads both files sequentially:
```html
<link rel="stylesheet" href="{% static 'css/style.css' %}?v=1.7">
<link rel="stylesheet" href="{% static 'css/ums.css' %}?v=1.0">
```
Component styling suffers from specificity conflicts, mismatched margins, overlapping border rules, and visual incongruities between legacy templates and new institutional pages.

---

## 2. Systematic UI Defect Breakdown

### 2.1 Conflicting Color Tokens & Visual Hierarchy

| Affected Selector / Element | Current File & Rule | Visual Problem | Prescribed Institutional Solution |
|---|---|---|---|
| `.module-showcase-box` | `style.css:320`: `background-color: #8EC5BE; border: 3.5px solid var(--ink-black); box-shadow: 6px 8px 0 var(--ink-black);` | Harsh mint-green container with thick brutalist black border and offset shadow clashes violently with maroon header and white card canvas. | Replace with institutional showcase card: `background: #FFFFFF; border: 1px solid #E2E4E8; border-left: 4px solid #9B2335; box-shadow: 0 1px 3px rgba(0,0,0,0.06); border-radius: 8px;`. |
| `.metric-strip-item` | `style.css:280`: `border: 2px solid var(--ink-black); box-shadow: 2px 2px 0 var(--ink-black); background: #FFF;` | Rigid black borders and harsh drop shadows make dashboard metrics feel like an indie web comic rather than a university portal. | Replace with clean stat card: `border: 1px solid #E2E4E8; box-shadow: 0 1px 2px rgba(0,0,0,0.05); border-radius: 6px; padding: 16px;`. |
| `.badge-tag-pill` / `.badge` | `style.css`: Uses legacy pink (`#FF3388`), cyan (`#35E0D0`), and purple (`#8B5CF6`). | Inconsistent badge semantics; status colors lack institutional uniformity and fail WCAG AA contrast against colored backgrounds. | Standardize to semantic token map: Success (Green `#12B76A`), Warning (Orange `#F37021`), Danger (Crimson `#B42318`), Info/Neutral (Maroon `#9B2335` on `#FBEFF1`). |
| `.btn-pill-white` / `.btn-secondary` | `style.css:180`: `border: 2px solid var(--ink-black); box-shadow: 2px 2px 0 var(--ink-black);` | Buttons look uneven next to institutional orange primary buttons (`#F37021`). | Refactor to institutional secondary: `background: #FFFFFF; border: 1px solid #E2E4E8; color: #1F2328; border-radius: 6px;`. |
| `.preview-chip-status` | `style.css`: Hardcoded cyan and lime styling. | High saturation distracts user focus. | Use subtle status pill: `background: #ECFDF3; color: #027A48; border: 1px solid #A6F4C5;`. |

---

### 2.2 Layout Shell, Header & Sidebar Alignment

| Component | Location | Issue Description | Root Cause | Remediation Plan |
|---|---|---|---|---|
| **Top Announcement Strip** | `templates/base.html:81-91` | Marquee text scrolls at 75s; on high-DPI and mobile screens, text can flicker or overlap with sticky header during fast scrolling. | Infinite CSS animation on `.marquee-track` without touch pause handling. | Add `animation-play-state: paused` on hover/touch and verify reduced-motion media query. |
| **Sidebar Collapse Behavior** | `templates/base.html:97`, `static/css/ums.css:394` | Collapsing sidebar (`body.sidebar-collapsed`) reduces width to `64px`, but icons without text sometimes shift leftwards due to `gap: 12px` inheritance. | `.ums-nav-link` flex container retains gap even when label is hidden. | Set `gap: 0; justify-content: center;` on collapsed links. |
| **Sidebar Role Navigation** | `templates/base.html:108` | `{% if user.is_staff or user.is_superuser or 'dean' in user.username.lower %}` | Fragile check `'dean' in user.username.lower` fails if a Dean's username does not contain the substring "dean" (e.g., `dr_sharma`). | Inject `is_dean` and `is_office` flags directly via context processor and use `{% if is_office or is_dean %}`. |
| **Header Search Field** | `templates/base.html:36-40` | Search form is hardcoded to 320px width; on tablet screens (768px - 1024px), it crowds the user dropdown. | Fixed `width: 320px` in `.ums-header-search`. | Change to responsive flex: `width: clamp(180px, 25vw, 320px);`. |
| **Notification Bell Badge** | `templates/base.html:48` | Inline styles `style="font-size: 0.65rem; position: absolute; top: 4px; right: 4px;"`. | Inline styling overriding CSS classes; badge position clips on smaller screens. | Move to dedicated `.ums-bell-badge` CSS class with `transform: translate(25%, -25%)`. |
| **Main Content Container** | `static/css/ums.css:412` | `main.ums-main` has `margin-left: 232px; max-width: 1280px; width: 100%; box-sizing: border-box;`. | On wide screens (> 1600px), fixed margin causes off-center appearance with vast empty space on the right. | Keep fixed sidebar offset while centering the inner container: `padding: 24px 32px; margin: 0 0 0 232px;`. |

---

### 2.3 Form Usability & Input Alignment

| Form / View | Template | Audit Finding | Severity | Fix |
|---|---|---|---|---|
| **Registration / Login Forms** | `templates/accounts/login.html`, `templates/accounts/register.html` | Input boxes use `style.css` inputs with `border: 2px solid var(--ink-black)`. When focused, outline changes abruptly. | Medium | Standardize to `.ums-input`: `border: 1px solid #E2E4E8; border-radius: 6px; padding: 10px 14px; font-size: 14px; transition: border-color 0.15s, box-shadow 0.15s;` Focus: `border-color: #9B2335; box-shadow: 0 0 0 3px rgba(155, 35, 53, 0.15);`. |
| **Paper Upload Drag & Drop** | `templates/papers/upload.html` | File dropzone has dashed neo-brutalist border and bulky padding. File size indicator is text-only without progress bar. | Low | Modernize dropzone with clean SVG upload cloud, `#9B2335` accents, and client-side 20MB validation feedback. |
| **Booking Date/Time Picker** | `templates/facilities/detail.html` | Start and end inputs use standard text inputs or raw browser inputs without minimum interval validation. | Medium | Add clear HTML5 `type="datetime-local"` attributes with `step="1800"` (30 min increments) and dynamic min-date set to current time. |
| **Opportunity Application** | `templates/opportunities/detail.html` | PDF upload error displays on page reload instead of modal alert if validation fails. | Medium | Provide inline error message inside application modal without closing modal on invalid submission. |
| **Funding Call Date Inputs** | `templates/funding/create.html` | Deadline field uses plain text input requiring manual `YYYY-MM-DD` formatting. | Medium | Enforce `<input type="date">` widget in Django form definition. |

---

### 2.4 Tables, Queues & Data Density

| Queue / Table | Template | Audit Finding | Fix |
|---|---|---|---|
| **Verification Queue** | `templates/researchers/verification_queue.html` | Table lacks horizontal scrolling container; long researcher headlines cause text wrap that pushes action buttons off-screen on tablets. | Wrap table in `.table-responsive` with `overflow-x: auto; -webkit-overflow-scrolling: touch;`. |
| **Deduplication Review Queue** | `templates/papers/dedup_queue.html` | Side-by-side title comparison uses 50/50 flex box. On screens under 1024px, titles squash vertically and token differences are hard to scan. | Stack comparison vertically on viewports `< 992px`; add color-coded diff tokens (green for additions, red for deletions). |
| **Author Disambiguation Queue** | `templates/papers/author_queue.html` | Confidence score displays as plain integer (e.g., `85%`) without visual indicator. | Add color-graded confidence meter: `score >= 90` (green), `80-89` (amber), `< 80` (red). |
| **At-Risk Projects Board** | `templates/projects/at_risk.html` | Milestone progress percentage and risk tags misaligned vertically in table cells. | Add `.align-middle` utility and flex container for risk chips. |
| **Academic Year Reports Table** | `templates/analytics/research.html` | Per-researcher productivity table in Dean section has no sticky header when scrolling through hundreds of records. | Add `thead th { position: sticky; top: 56px; background: #FFFFFF; z-index: 10; }`. |

---

### 2.5 Responsive Viewport Audit Matrix

| Viewport Breakpoint | Target Devices | Current Behavior | Issues Observed | Resolution |
|---|---|---|---|---|
| **>= 1440px** | Large Desktop / 4K Monitors | Application shell loads cleanly. Sidebar is fixed at 232px. | Main content container looks slightly stretched on ultra-wide screens. | Constrain `.ums-main-container` max-width to `1400px` with margin auto. |
| **1280px - 1439px** | Standard Laptops (MacBook Air, Dell XPS) | Baseline target layout. | Dashboard quick action tiles occasionally break into 3+2 layout. | Use `grid-template-columns: repeat(5, 1fr)` at `>= 1200px`. |
| **992px - 1279px** | Small Laptops & Large Tablets (Landscape) | Sidebar remains visible. Content area narrows. | Search bar in header starts crowding account menu; tables begin truncating. | Reduce search input width; enable horizontal table scrolling. |
| **768px - 991px** | Tablets (iPad Portrait, Android Tablets) | Sidebar drops to slide-out drawer (`transform: translateX(-100%)`). Hamburger menu appears. | Hamburger button touch target is `36px` (below 44px minimum). Filter columns on papers list take 40% width. | Expand hamburger touch target to `44px x 44px`; stack filters above paper catalog. |
| **390px - 767px** | Modern Smartphones (iPhone 14/15/16, Galaxy S23) | Mobile drawer functions. Single column layout. | Metric strip items stack into tall column; quick action buttons take 2 rows of 2. | Render metric strip as 2x2 grid with compact numbers; optimize quick actions to clean 2-column grid. |
| **<= 389px** | Small Smartphones (iPhone SE, Galaxy A-series) | Mobile view. | Marquee text causes subtle horizontal page wobble if margins overflow; user name in header truncates awkwardly. | Enforce `overflow-x: hidden` on `body, html`; hide user name and show avatar dot only at `< 400px`. |

---

### 2.6 Accessibility & WCAG 2.1 AA Compliance

1. **Color Contrast:**
   - Primary Maroon `#9B2335` on White `#FFFFFF`: **Contrast Ratio 6.8:1** (Passes WCAG AAA for normal text).
   - Primary Action Orange `#F37021` with Dark Ink `#1F2328`: **Contrast Ratio 5.9:1** (Passes WCAG AA).
   - *Defect:* Legacy yellow `#FFDD33` with white text: **Contrast Ratio 1.2:1** (Severe failure). Standardize all orange/yellow action items to high-contrast dark text `#1F2328`.
2. **Keyboard Navigation & Focus:**
   - Focus ring currently applied in `ums.css:499`: `:focus-visible { outline: 2px solid #9B2335 !important; outline-offset: 2px !important; }`.
   - *Defect:* Certain custom dropdowns in `main.js` do not trap focus or close on `Escape` key.
   - *Remediation:* Add `keydown` event listener for `Escape` and arrow-key traversal.
3. **Screen Readers & ARIA Labels:**
   - Collaboration network graph includes full HTML table fallback for screen readers.
   - *Defect:* SVG timeline bars in Milestones lack `aria-label` detailing milestone title, due date, and risk state.
   - *Remediation:* Add descriptive `aria-label` to every milestone timeline segment.

---

## 3. Design Token Consolidation Plan

We will consolidate all styling into a single unified institutional design token file (`static/css/institutional_tokens.css`) and clean up `static/css/style.css` so that:
1. Neo-brutalist 3.5px black borders are completely removed in favor of `1px solid #E2E4E8`.
2. Offset black drop shadows (`box-shadow: 4px 6px 0 #141416`) are replaced by soft ambient shadows (`0 1px 3px rgba(0, 0, 0, 0.05)`).
3. Vibrant pinks and cyans are eliminated; semantic status colors follow university portal standards.
4. All major pages (Dashboard, Papers, Researchers, Projects, Openings, Facilities, Funding, Analytics, Office Hub) adhere to the unified LPU institutional design system.
