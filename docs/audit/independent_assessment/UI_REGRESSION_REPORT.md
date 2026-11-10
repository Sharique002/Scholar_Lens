# Scholar Lens — UI & Frontend Regression Forensic Audit

**Document Version:** 1.0.0  
**Audit Date:** November 6, 2026  
**Auditor:** Independent Principal Software Auditor & UI/UX Architect  

---

## 1. Executive Summary

A forensic review of the user interface architecture was conducted following the elimination of the neo-brutalist theme and adoption of the unified LPU UMS institutional design system.

### Core Verification Status:
- **Design Tokens:** `static/css/institutional_tokens.css` defines the canonical palette:
  - Institutional Maroon: `#9B2335` (Primary), `#7A1B29` (Dark Heritage), `#FBEFF1` (Subtle Tint)
  - Action Orange: `#F37021` (High-Impact Action), `#E0601A` (Hover), `#1F2328` (High-Contrast Text)
  - Neutral Canvas: `#F5F5F7`
  - Clean Surfaces: Pure White `#FFFFFF` with `1px solid var(--border)` (`#E2E4E8`) and subtle box-shadows (`var(--shadow-sm)`).
- **Brutalist Style Removal:** 0 instances of `border: 3.5px solid var(--ink-black)` or harsh offset drop shadows remain in `style.css`.
- **Navigation Alignment:** Sidebar navigation properly displays 9 primary research modules (`Dashboard`, `Papers`, `Projects`, `Openings`, `Researchers`, `Collaboration`, `Facilities`, `Funding`, `Search`). The Reports link is conditionally shown for authorized executives.
- **Automated Verification:** `tests.test_ums_shell` passes 100% (7/7 tests).

---

## 2. Responsive Viewport Audit

| Viewport Width | Device Category | Layout Behavior | Audit Assessment |
|---|---|---|---|
| **360px** | Small Mobile (e.g., Galaxy S8) | Sidebar collapses off-canvas via `transform: translateX(-100%)`. Header search compresses into icon. Quick actions grid adjusts to 2 columns. | **PASS (No horizontal overflow)** |
| **390px** | Standard Mobile (e.g., iPhone 12/14) | Hamburger menu toggle accessible; top marquee renders at 32px height; main content padding 16px. | **PASS** |
| **768px** | Tablet Portrait (e.g., iPad Mini) | Off-canvas sidebar with backdrop overlay; metric cards render in $2 \times 2$ grid; cards stack cleanly. | **PASS** |
| **1024px** | Tablet Landscape / Small Desktop | Desktop sidebar visible at 232px width; main content margin 232px; quick actions span 5 items; chart canvases resize dynamically. | **PASS** |
| **1280px** | Standard Desktop Laptop | Full sidebar with collapse toggle (`«` / `»`); metric strip spans 4 equal columns; two-column dashboard grid ($7:5$ ratio). | **PASS** |
| **1440px** | Large Desktop / Workstation | Centered container constrained to max-width 1,400px; generous whitespace; readable line lengths ($\le 80$ characters). | **PASS** |

---

## 3. Component Regression Checklist

| UI Component | Legacy State | Modernized Institutional State | Regression Status |
|---|---|---|---|
| **Top Announcement Strip** | Black background with neon yellow text | Institutional Maroon (`#9B2335`) with white text and smooth marquee animation | **NO REGRESSION** |
| **Header Bar** | Floating pills with black borders | Clean 56px sticky white header with maroon accent border and search input | **NO REGRESSION** |
| **Primary Buttons** | Neon pink / yellow with 2px black border and offset drop shadow | Action Orange (`#F37021`) with dark readable text (`#1F2328`), 6px border radius, subtle elevation | **NO REGRESSION** |
| **Metric Cards** | Thick black borders with 4px offset shadow | White card surface with neutral divider border and maroon primary metric numbers | **NO REGRESSION** |
| **Showcase Hero Box** | Mint green (`#8EC5BE`) container with 3.5px black border | Pure white institutional card with 4px maroon left border accent and subtle shadow | **NO REGRESSION** |
| **Form Controls** | Neo-brutalist border with offset focus shadow | Clean `#D0D5DD` border; maroon focus ring (`#9B2335`) with accessible 2px offset | **NO REGRESSION** |
| **Status Pills** | Neon green, yellow, pink tags | Muted semantic status badges (Success `#ECFDF3`, Warning `#FFF1E8`, Danger `#FEF3F2`) | **NO REGRESSION** |
| **User Dropdown** | Misaligned admin link (superuser only) | Complete dropdown displaying My Profile, Settings, Password, and Admin Panel (staff/superuser) | **FIXED & VERIFIED** |

---

## 4. Visual Verification Verdict

The institutional redesign successfully unified the presentation layer without introducing layout breaks, text squashing, or missing stylesheet assets. All 133 static assets compile cleanly under WhiteNoise and Django's `collectstatic`.
