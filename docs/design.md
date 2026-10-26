# Design: Sell-Safe Connect (web onboarding site)
A simple modern site that shows sellers how to connect Sell-Safe to **WhatsApp, Instagram and Facebook Messenger**. Pattern borrowed from Cursor's download page (https://cursor.com/download): pick your platform, then get only the steps for that platform.

Stack (planned): Next.js App Router + Tailwind + shadcn/ui, deployed to Vercel. **Docs only right now, no code.**

## Research sources
- Refero MCP: returned `NO_SUBSCRIPTION`, so it was skipped.
- Mobbin MCP: "requires a paid plan", so it was skipped.
- Used instead: the public patterns of cursor.com/download plus the guideline resources listed at the end (all links checked and loading on Oct 26, 2026).

## Page map
| Route | Purpose |
|---|---|
| `/` | Hero + platform picker (WhatsApp / Instagram / Messenger) + numbered steps + status check |
| `/?platform=instagram` | Deep link to one platform (tab state lives in the URL) |
| `/status` | Check webhook connection for a seller (calls the backend health/verify status) |
| `/faq` | Common errors (verify token mismatch, IG account not Business, test-number recipients) |
| `/privacy` | What data Sell-Safe stores (needed for Meta app review later) |

## Layout (desktop ≥1024px)
```
┌───────────────────────────────────────────────┐
│ Logo  Sell-Safe            Docs  FAQ  [Theme] │  top bar 64px
├───────────────────────────────────────────────┤
│  Connect Sell-Safe to your shop               │  hero H1
│  Pick where your buyers message you.          │
│  [ WhatsApp | Instagram | Messenger ]         │  segmented control
├───────────────┬───────────────────────────────┤
│ Prerequisites │ ① Create a Meta app           │
│ card (sticky) │   text, screenshot slot       │
│ • FB account  │ ② Add WhatsApp product        │
│ • Phone       │   [ code block  ⧉ copy ]      │
│ • ~15 min     │ ③ Paste webhook URL + token   │
│               │ ④ Send a test message  [Check]│
└───────────────┴───────────────────────────────┘
```
- Max content width 1080px; steps column ~680px; sidebar 280px, sticky.
- Mobile: single column, prerequisites collapse into an accordion above step 1, segmented control scrolls horizontally if needed.

## Components
| Component | Base (shadcn/ui) | Notes |
|---|---|---|
| `PlatformTabs` | Tabs (Radix) | segmented look; arrow-key navigation; syncs `?platform=`; icon + label |
| `Steps` / `StepCard` | custom | numbered circle, title, body, optional screenshot + code; "Done" checkbox saved in localStorage |
| `CodeBlock` | custom | mono text, copy button with "Copied" toast (sonner), masks secrets (shows `••••`) |
| `ScreenshotPlaceholder` | AspectRatio + Skeleton | 16:10 slot, caption, "screenshot coming" until real redacted images exist |
| `StatusCheck` | Button + Badge | states: idle, checking (spinner), connected (green), failed (red with fix link) |
| `Callout` | Alert | info / warning ("Instagram must be a Business account") |
| `ThemeToggle` | DropdownMenu | light / dark / system |
| `Footer` | custom | links, "Built for the Meta Global AI Hackathon" |

## Typography
- Font: Geist Sans and Geist Mono (Vercel, open source) or Inter as fallback.
- Scale: H1 40/48 semibold (28/36 mobile) · H2 24/32 semibold · H3 18/28 medium · body 16/26 · small 14/20 · code 14/22 mono.
- Max line length ~70 characters.

## Color tokens (CSS variables, shadcn style)
| Token | Light | Dark |
|---|---|---|
| `--background` | #FFFFFF | #0A0A0B |
| `--foreground` | #0A0A0B | #EDEDED |
| `--muted` | #F4F4F5 | #18181B |
| `--muted-foreground` | #52525B | #A1A1AA |
| `--border` | #E4E4E7 | #27272A |
| `--primary` (brand: safe green) | #0F9D58 | #22C55E |
| `--primary-foreground` | #FFFFFF | #052E16 |
| `--warning` | #B45309 | #F59E0B |
| `--danger` | #DC2626 | #F87171 |
| `--success` | #15803D | #4ADE80 |
Platform accents, used only on tab icons: WhatsApp #25D366, Instagram gradient (icon only), Messenger #0084FF. Don't use platform logos without checking Meta brand rules (TODO verify).
Contrast: all text is AA (4.5:1) or better; check with a contrast checker.

## Spacing, radius, elevation
- 4px base: 4, 8, 12, 16, 24, 32, 48, 64. Section gap 64; step gap 24; card padding 24 (16 mobile).
- Radius: 8 for inputs/buttons, 12 for cards, 999 for the segmented control.
- Elevation: borders first; one soft shadow for the active tab and sticky card only.

## Motion
- 150–200ms ease-out for hover/tab change; steps cross-fade + 8px slide on platform switch.
- Copy button: icon swap to a check for 1.5 s.
- Status check: spinner, then a badge pop (scale 0.96→1).
- Respect `prefers-reduced-motion`: no slide, fade only.

## Dark/light
Follows the system by default, with a toggle stored in localStorage; no flash on load. Screenshots need light and dark variants or a neutral frame.

## Accessibility
- Tabs follow the WAI-ARIA tabs pattern (Radix handles roles and keyboard).
- Steps are an ordered list (`<ol>`), each with a heading.
- Copy buttons have `aria-label="Copy webhook URL"` and announce "Copied" via an aria-live region.
- Focus rings always visible; hit targets ≥ 44px; no info by color alone (status badges include text).
- Screenshots have alt text describing the action.

## Responsive rules
| Breakpoint | Behaviour |
|---|---|
| < 640px | one column, full-width tabs, code blocks scroll horizontally, sticky "Next step" button |
| 640–1023px | one column, wider margins |
| ≥ 1024px | two columns with sticky prerequisites |

## Copy tone
Plain, friendly Nigerian English; short sentences; second person ("Paste your webhook URL"). Every step starts with a verb. Explain why in one line when a step is confusing. No jargon without a hint (e.g. "verify token: a password you make up so Meta knows it's your server"). Optional later: Pidgin toggle.

## Content
Per-platform steps live in `docs/web_content/` (one file per platform). Copy them into `web/content/` when the site is built. Every step not yet checked against Meta's current docs is marked **TODO verify**.

## Design resources to borrow from (links checked Oct 26, 2026)
- Apple Human Interface Guidelines: https://developer.apple.com/design/human-interface-guidelines
- Apple design agent skill (community repo, not from Apple): https://github.com/dickwu/apple-design-skill
- Anthropic agent skills repo (has a frontend design skill, TODO verify contents): https://github.com/anthropics/skills
- shadcn/ui: https://github.com/shadcn-ui/ui
- Vercel Geist design system: https://vercel.com/geist/introduction · font: https://github.com/vercel/geist-font
- Vercel web interface guidelines: https://vercel.com/design/guidelines · https://github.com/vercel-labs/web-interface-guidelines
- Radix Primitives: https://github.com/radix-ui/primitives · Radix Colors: https://www.radix-ui.com/colors
- Linear Method (product and quality principles): https://linear.app/method
- Sonner toasts: https://github.com/emilkowalski/sonner
- Pattern reference: https://cursor.com/download
