# Sell-Safe Website Design Plan

**Status:** Plan only (no app code). Prepared for build tomorrow.  
**Product:** AI sales assistant for Instagram sellers (WhatsApp coming soon). Answers buyers, drafts catalogs from posts, takes orders, and catches fake payment proof.  
**Audience:** Nigerian small online sellers + Meta hackathon judges. Trustworthy, premium, simple — never technical.  
**Stack target:** Next.js App Router (`web/`), Tailwind, shadcn/ui, Magic UI, selective 21st.dev blocks. Keep existing light/dark themes and `PlatformTabs`.

---

## 0. Skills used and rules taken

| Skill / guide | Key rules applied |
|---|---|
| **Refero Design** (`refero-design/SKILL.md`) | Research before designing; lock a primary direction (not an average of references); preserve token *roles*; synthesize into a decision ledger; mandatory craft refs (type, color, motion, copy, anti-slop). |
| **Refero anti-AI-slop** | No cards-everywhere; no dark-by-default; no calm-editorial serif autopilot; indigo/violet only when brand requires it. **Here the logo explicitly requires blue→violet** — use it as a *decorative / brand-mark* gradient, not as surface paint. Neutrals dominate. |
| **Refero typography** | Clarity over decoration; consistent type scale; denser/simpler for product UI; display personality allowed on marketing surfaces. |
| **Refero color** | 4 layers (neutrals, brand, semantic, decorative); fewer colors; OKLCH-aware steps; brand accent rare. |
| **Refero motion** | Motion must give feedback, continuity, or hierarchy; shorter/subtler when unsure; marketing may be more expressive than product UI. |
| **Refero copywriting** | Clarity > respect > character; living words; verbs; facts over adjectives; Nigerian seller context. |
| **Apple Design / HIG** (`onboarding`, `motion`, `branding`, `accessibility`, `writing`) | Teach through interactivity; optional skippable onboarding with defaults; motion purposeful and optional; brand accent judicious; branding defers to content; no color-only meaning. |
| **Frontend UI Engineering** | Semantic tokens; WCAG AA; keyboard/focus; empty/error/loading states; mobile-first; avoid AI aesthetic. |
| **Make interfaces feel better** | Concentric radii; interruptible transitions; stagger rare entrances; `tabular-nums`; scale `0.96` on press; `prefers-reduced-motion`; never `transition: all`. |
| **User frontend design rules** | One composition in first viewport; brand as hero-level signal; expressive fonts (not Inter/system); atmospheric background; full-bleed hero plane; hero budget (brand, one headline, one line, CTA group, one visual); no hero overlays/cards; one job per section; 2–3 intentional motions. |
| **Existing `docs/design.md` + `web/`** | Keep light/dark tokens, PlatformTabs URL sync, plain Nigerian English, max content ~1080–1200px, green for success/primary actions already in CSS — evolve, don’t discard. |

**MCP note:** Live MCP for Magic UI, 21st.dev, shadcn, and Refero was unavailable in this agent session (discovery errors / Refero needs desktop auth). Research used public docs: `magicui.design`, `21st.dev`, `ui.shadcn.com`, plus logo color quantization.

---

## 1. Design principles and feeling

**Feeling:** Calm confidence — like a trusted shop assistant who already knows your stock. Premium Meta-adjacent (smooth blue→violet light), never flashy crypto, never “AI purple SaaS.”

1. **Trust before cleverness** — Every screen answers “Will this protect my money?” before “Is this cool?”
2. **Show, don’t explain** — Prefer interactive demos (chat reply, fake-vs-real proof) over feature paragraphs.
3. **Skip anytime** — Onboarding is optional, short, with defaults and “Do this later” on every step (Apple agency + existing plan).
4. **One job per section** — Landing sections don’t compete; the payment demo is the signature moment.
5. **Brand in the mark, not the wallpaper** — Gradient lives in the logo, hero ambient shapes, and verifying states; UI chrome stays neutral.

**Signature element:** Interactive fake-vs-real payment demo where the Sell-Safe shield *scans*, then flips to green **CONFIRMED** or amber/red **SUSPICIOUS**.

---

## 2. Brand system

### 2.1 Colour tokens (from logo + existing web)

Quantized from `sell-safe.logo.jpg` / `sell-safe.logo2.jpg`:

| Role | Token | Light | Dark | Notes |
|---|---|---|---|---|
| Canvas | `--background` | `#FFFFFF` | `#0A0A0B` | Keep existing |
| Text | `--foreground` | `#071942` | `#EDEDED` | Wordmark navy on light |
| Muted surface | `--muted` | `#F4F5FB` | `#18181B` | Cool tint of brand blue |
| Muted text | `--muted-foreground` | `#52525B` | `#A1A1AA` | Existing |
| Border | `--border` | `#E4E4E7` | `#27272A` | Existing |
| Brand blue | `--brand-blue` | `#2876FE` | `#4B8FFF` | Logo start |
| Brand mid | `--brand-mid` | `#5A55F9` | `#7B76FF` | Logo mid |
| Brand violet | `--brand-violet` | `#6E4AF7` | `#9B7CFF` | Logo end |
| Primary CTA | `--primary` | `#2876FE` | `#4B8FFF` | Connect actions (shift from green) |
| Primary fg | `--primary-foreground` | `#FFFFFF` | `#071942` | |
| Success / CONFIRMED | `--success` | `#0F9D58` | `#22C55E` | Keep existing green |
| Warning / PENDING | `--warning` | `#B45309` | `#F59E0B` | |
| Danger / SUSPICIOUS | `--danger` | `#DC2626` | `#F87171` | |
| Platform IG | accent only | Instagram gradient on icon | | Never Meta trademark marks |
| Platform WA | accent only | `#25D366` | | Waitlist only |

**Contrast targets:** Body text ≥ 4.5:1 on canvas; large headings ≥ 3:1; verdict badges always include text + icon (never colour alone).

### 2.2 Gradients

```css
--gradient-brand: linear-gradient(135deg, #2876FE 0%, #5A55F9 55%, #6E4AF7 100%);
--gradient-brand-soft: linear-gradient(135deg, rgba(40,118,254,0.14), rgba(110,74,247,0.10));
--gradient-scan: linear-gradient(90deg, transparent, rgba(40,118,254,0.55), transparent);
--gradient-flow-shape: radial-gradient(ellipse at 30% 20%, rgba(40,118,254,0.22), transparent 55%),
                       radial-gradient(ellipse at 80% 60%, rgba(110,74,247,0.18), transparent 50%);
```

**Angle:** 135° (top-left blue → bottom-right violet), matching the logo stroke.

**Roles:** `--gradient-brand` = logo stroke + primary shimmer CTA only. `--gradient-brand-soft` / `--gradient-flow-shape` = hero atmosphere. `--gradient-scan` = verifying spinner only.

### 2.3 Typography

| Role | Font | Why |
|---|---|---|
| Display + UI | **Plus Jakarta Sans** (Google Fonts) | Geometric, rounded terminals echo the logo wordmark; friendlier than Inter for Nigerian sellers; not a Meta clone. |
| Mono / money / IDs | **Geist Mono** | Already planned in `docs/design.md`; tabular for ₦ amounts. |
| Fallback stack | `Plus Jakarta Sans, Geist Sans, ui-sans-serif, system-ui, sans-serif` | |

**Scale**

| Token | Size / line | Weight | Use |
|---|---|---|---|
| `display` | 48/56 (32/40 mobile) | 700 | Hero H1 only |
| `h1` | 36/44 (28/36 m) | 700 | Page titles |
| `h2` | 28/36 (24/32 m) | 600 | Section titles |
| `h3` | 20/28 | 600 | Cards / steps |
| `body` | 16/26 | 400 | Default |
| `small` | 14/20 | 400–500 | Helper, captions |
| `micro` | 12/16 | 500 | Badges, timestamps |

`text-wrap: balance` on headings; `pretty` on body; `font-variant-numeric: tabular-nums` on money and counters.

### 2.4 Spacing, radius, shadows

- **Spacing scale:** 4, 8, 12, 16, 24, 32, 48, 64, 96. Section vertical rhythm 64–96.
- **Content max:** 1120px marketing; 1080px onboarding (existing).
- **Radius:** `sm` 8 (inputs/buttons), `md` 12 (interactive panels), `lg` 16 (hero mock), `xl` 24 (ambient blobs only), `pill` 999 (tabs / waitlist chip).
- **Concentric rule:** outer = inner + padding.
- **Shadows:** Prefer 1px borders. Soft elevation only for sticky nav and the active payment-demo panel: `0 1px 2px rgba(7,25,66,0.04), 0 12px 32px rgba(40,118,254,0.08)`.

### 2.5 Iconography

- **Lucide** outline icons, stroke 1.75–2 to match semibold labels.
- One set only; `currentColor`; fill only for selected/active.
- Custom: Sell-Safe shield SVG for brand moments and verifying states.

### 2.6 Logo system (redraw, don’t paste JPG)

Source JPGs stay as reference only. SVG drafts live in `docs/design/logo/`:

| File | Use |
|---|---|
| `mark-icon.svg` | Full-colour icon |
| `mark-wordmark.svg` | Icon + “Sell-Safe” navy wordmark |
| `mark-mono.svg` | One-colour via `currentColor` |
| `mark-dark.svg` | Dark surfaces (lifted gradient + `#EDEDED` wordmark) |
| `favicon.svg` | 32×32 with soft square frame |

**Usage rules**

| Placement | Variant | Size |
|---|---|---|
| Nav | Wordmark (light/dark swap) | 28–32px icon height |
| Hero | Optional large icon (48–64px) beside or above brand name — brand is hero-level, not eyebrow-only | |
| Payment demo | Icon as verifying spinner | 40–56px |
| Footer | Wordmark mono or colour | 24px |
| Favicon / PWA | `favicon.svg` → also export 32/180 PNG later | |

**Clear space:** ≥ 0.25× icon width on all sides. Don’t stretch, don’t recolour gradient stops, don’t place on busy photos without a scrim.

**Logo motion**

1. **Intro (page load, once):** Shield path draws ~600ms (`stroke-dashoffset`), check strokes on ~280ms after, gradient sweep across stroke ~400ms. Total ≤ 1.1s. Skip entirely under `prefers-reduced-motion` (show final mark).
2. **Hover (nav):** Soft scale 1→1.03 + gradient shift 8% along the axis, 180ms `cubic-bezier(0.2,0,0,1)`.
3. **Verifying spinner:** Horizontal scan band (`--gradient-scan`) loops inside the shield for 1.2–2s while checking proof; then fill/stroke snaps to `--success` (CONFIRMED) or `--danger`/`--warning` (SUSPICIOUS). Always pair with text badge.

---

## 3. Motion system

| Tier | Duration | Easing | Examples |
|---|---|---|---|
| Micro | 120–180ms | `cubic-bezier(0.2, 0, 0, 1)` | Hover colour, press `scale(0.96)`, tab underline |
| Transition | 200–280ms | same | Dialog/sheet, accordion, platform tab cross-fade |
| Entrance | 400–600ms | ease-out | BlurFade section reveals, logo intro |
| Demo theatre | 800–1600ms staged | ease-out + stagger ~100ms | Chat typing, payment scan → verdict |

**Animates:** Section enter (BlurFade), logo intro once, chat bubble sequence, BorderBeam on payment panel while verifying, NumberTicker for fake amounts, Marquee trust strip (paused on hover/focus).

**Never animates:** Cursor blink loops that never end without pause; parallax that moves text; continuous hero particles; hover on every list row; layout thrash on typing.

**Reduced motion:** No BlurFade offset/blur (opacity only or instant); no BorderBeam/Marquee/Orbit; logo final state; payment demo still works with instant badge swap.

---

## 4. Information architecture and sitemap

```
/                       Marketing landing (new hero → demo → features → waitlist → FAQ)
/onboard                Chat-style onboarding (Instagram first)
/?platform=instagram    Legacy/advanced connect (keep PlatformTabs)
/?platform=whatsapp     Waitlist-forward
/?platform=messenger    Coming-soon / advanced
/status                 Webhook / connection check
/dashboard              Orders, verdicts, catalog drafts (auth)
/faq                    Full FAQ (landing embeds top 5)
/privacy                Data practices (Meta review)
```

**Primary path:** Landing CTA → Instagram connect → onboarding steps → dashboard.  
**Secondary:** Landing → WhatsApp waitlist.  
**Escape hatches:** “Do this later”, FAQ, Privacy, Status.

---

## 5. Landing page — section-by-section

**Layout shell:** Sticky blur nav (logo wordmark, Features, How it works, FAQ, ThemeToggle, primary “Connect Instagram”). Full-bleed hero atmosphere (`DotPattern` + soft brand radial). Then constrained sections. Footer.

**Platform tabs:** Keep below fold or in onboarding — not in the hero (hero has one job).

### 5.1 Hero

| | Spec |
|---|---|
| **Layout** | Split ≥1024px: copy left (brand + H1 + sub + CTA pair), animated chat mock right. Mobile: brand → H1 → sub → CTAs → chat mock full width. First viewport = one composition. |
| **Components** | Structure inspired by **21st.dev** `HeroSection – Dual CTAs` (`uniquesonu`) — install then restyle; **do not ship stock glass cards**. Hero visual: **21st.dev** `Chat Messages` (`nexus-ui`) or custom `HeroChatMock` built on shadcn `Message` primitives. Atmosphere: Magic UI **Dot Pattern**. Primary CTA: Magic UI **Shimmer Button**. Entrance: Magic UI **Blur Fade**. Optional accent word: Magic UI **Animated Gradient Text** on one short phrase only (“fake payment proof”). |
| **Animation** | BlurFade stagger: brand → headline → sub → CTAs → chat. Chat: buyer bubble in → typing dots → Sell-Safe reply. Logo intro once. Reduced motion: static final chat. |
| **Copy** | **Brand:** Sell-Safe (wordmark). **H1 options (pick one):** (A) “Sell on Instagram. Catch fake payments.” (B) “Your AI shop assistant that checks every payment.” (C) “Answer buyers. Confirm payments. Sleep better.” **Recommended:** A. **Sub:** “Sell-Safe replies to your DMs, builds a catalog from your posts, and flags fake transfer screenshots before you send goods.” **Primary CTA:** “Connect Instagram”. **Secondary:** “Join WhatsApp waitlist”. |
| **Responsive** | CTAs stack full-width &lt;640px; chat mock max-height 420px with fade. |

### 5.2 Trust strip

| | Spec |
|---|---|
| **Layout** | Single quiet row under hero — not a card grid. Logos/text chips for: Paystack · Bank alerts · USDC on Base · Built for Meta hackathon. |
| **Components** | Magic UI **Marquee** (`pauseOnHover`), muted labels. |
| **Animation** | Slow marquee; static wrap on reduced motion. |
| **Copy** | “Checks payments with real Paystack webhooks, bank alerts, and on-chain USDC on Base — not guesswork.” |
| **Responsive** | Fade edges on desktop; two-line wrap on mobile without marquee if reduced motion. |

### 5.3 How it works (3 steps)

| | Spec |
|---|---|
| **Layout** | Centered H2 + 3 equal columns (stack on mobile). Numbers 01–03 as sequence (justified). No decorative cards — icon + title + one sentence. |
| **Components** | **21st.dev** `How It Works Steps` (`ln-dev7/how-it-works-01`) as structure; restyle to tokens. Or custom with Lucide. |
| **Animation** | BlurFade on scroll once. |
| **Copy** | **H2:** “Up and selling in three steps.” **1 Connect** — “Link Instagram in one tap. No developer setup for the happy path.” **2 Teach** — “Approve the catalog we draft from your posts. Tell us your prices and policies in chat.” **3 Protect** — “When a buyer sends payment proof, Sell-Safe checks it. Fake screenshots get SUSPICIOUS. Real money gets CONFIRMED.” |
| **Responsive** | Vertical stack with step connectors as simple borders. |

### 5.4 Fake-vs-real payment demo (highlight)

| | Spec |
|---|---|
| **Layout** | Full-bleed soft brand wash; centered interactive panel (this *is* an interaction → panel allowed). Three choices: Fake screenshot · Real Paystack/bank · USDC on Base. Outcome area with shield + verdict badge. |
| **Components** | Evolve existing `PaymentSafetyDemo`. Frame: Magic UI **Border Beam** while verifying (`colorFrom=#2876FE`, `colorTo=#6E4AF7`). Verdict: shadcn **Badge** + custom **ShieldSpinner**. Amounts: Magic UI **Number Ticker** + `tabular-nums`. Tabs: shadcn **Tabs**. Optional Magic UI **Animated List** for check steps (“Reading receipt…”, “Matching Paystack…”, “Verdict”). |
| **Animation** | Click → shield scan 1.2s → BorderBeam → badge pop `scale 0.96→1`. Theatre only; not on every hover. |
| **Copy** | **H2:** “See a fake payment get caught.” **Sub:** “Tap a proof type. Sell-Safe checks real payment rails — not the picture alone.” **Fake outcome:** “SUSPICIOUS — This looks edited. Don’t send the goods yet.” **Real:** “CONFIRMED — Paystack (or bank alert) matches. Safe to pack.” **Crypto:** “CONFIRMED — USDC received on Base.” |
| **Responsive** | Choices stack; sticky “Try it” on short mobile viewports optional. |

### 5.5 Features grid

| | Spec |
|---|---|
| **Layout** | 2×2 on desktop (not a 6-card bento dump). Each feature: icon + title + one sentence. Prefer open sections over bordered cards unless the tile opens a dialog. |
| **Components** | Custom grid; optional Magic UI **Bento Grid** only if we keep 4 tiles max. Icons Lucide. |
| **Animation** | BlurFade; hover = colour/opacity only (≤150ms). |
| **Copy** | **H2:** “Built for how you already sell.” **1** “Answers buyers in your tone — English, Pidgin, or Yoruba samples.” **2** “Drafts your catalog from Instagram posts — you approve, edit, or skip.” **3** “Takes orders in chat so nothing gets lost in DMs.” **4** “Flags fake proof; confirms Paystack, bank alerts, and USDC on Base.” |
| **Responsive** | 1 col mobile, 2 col ≥768. |

### 5.6 Catalog-from-posts preview

| | Spec |
|---|---|
| **Layout** | Split: left copy + CTA “See it in onboarding”; right horizontal scroll of product tiles drafted from posts (synthetic images only). |
| **Components** | shadcn **Scroll Area**, **Badge** (“Draft”), **Button**. Optional Magic UI **Blur Fade**. |
| **Animation** | Soft scroll hint; tiles fade in once. |
| **Copy** | **H2:** “Your posts become a shop list.” **Sub:** “We read your recent posts and suggest names and prices. You approve what looks right — nothing goes live without you.” **Tile labels:** e.g. “Black leather bag · ₦15,000 · Draft”. |
| **Responsive** | Snap-scroll tiles 80% width on mobile. |

### 5.7 WhatsApp coming-soon waitlist

| | Spec |
|---|---|
| **Layout** | One focused band: headline, one line, phone field with `+234` prefix (reuse `WhatsAppWaitlist` pattern), submit. Secondary text about Instagram being ready now. |
| **Components** | shadcn **Input** / **Input Group**, **Button**, **Field**, sonner **Toast**. Optional Magic UI **Orbiting Circles** with IG + WA icons *behind* copy at low opacity — omit if it fights simplicity. |
| **Animation** | Success: check icon cross-fade; toast “We’ll message you on WhatsApp when ready”. |
| **Copy** | **H2:** “Coming soon to WhatsApp.” **Sub:** “Leave your number. We’ll text you when Sell-Safe can run your WhatsApp shop the same way.” **CTA:** “Join the waitlist”. **Helper:** “Instagram is ready today — connect above.” |
| **Responsive** | Full-width field + button stack. |

### 5.8 FAQ

| | Spec |
|---|---|
| **Layout** | **21st.dev** `Two-Column FAQ` (`ln-dev7/faqs-02`) or centered accordion if short. Left: “Questions sellers ask” + link to `/privacy`. Right: accordion. |
| **Components** | shadcn **Accordion** (base of 21st block). |
| **Animation** | Height transition 200ms; reduced motion = instant. |
| **Copy (draft Q&As)** | **Do I need a developer?** “No for Instagram Login. Advanced webhook setup is optional under Docs.” **Will it reply without me?** “Yes, after you connect and approve your catalog and tone.” **What is SUSPICIOUS?** “The receipt didn’t match a real Paystack, bank, or on-chain payment. Pause and check before sending goods.” **What is CONFIRMED?** “We saw a matching real payment signal. Safe to fulfil.” **Is WhatsApp ready?** “Not yet — join the waitlist.” **What data do you store?** “See Privacy — we keep what we need to reply and verify payments, nothing more.” |
| **Responsive** | Single column &lt;1024. |

### 5.9 Footer

| | Spec |
|---|---|
| **Layout** | Logo wordmark, links (Docs, Status, FAQ, Privacy), “Built for the Meta Global AI Hackathon”, theme already in nav. Minimal — no giant wordmark gimmick. |
| **Components** | Custom; shadcn **Separator**. |
| **Copy** | “Sell-Safe — AI sales assistant for Instagram sellers.” |

---

## 6. Onboarding flow (chat-style)

**Route:** `/onboard` (also reachable after hero CTA). Pattern: messenger-like thread where Sell-Safe asks, seller answers. Progress: thin top stepper (shadcn-inspired) without trapping users.

| Step | Screen | States | Empty / error | Skip |
|---|---|---|---|---|
| 0 | Welcome + “Connect Instagram” | idle / connecting / connected | Error: “Couldn’t reach Instagram. Try again.” | “Do this later” → dashboard empty |
| 1 | Sample AI reply (reuse `SampleReplyDemo` tone) | generating / shown | Retry if mock fails | Skip |
| 2 | Catalog from posts | loading drafts / list / editing | Empty: “No posts found yet — add items manually or skip.” | “Skip catalog for now” |
| 3 | Business details (chat) | prompts for shop name, city, currency ₦ | Validation inline | Later |
| 4 | Policies (few at a time) | delivery, returns, payment methods with defaults pre-checked | — | Accept defaults + later |
| 5 | Payment demo (same as landing, shorter) | interactive | — | Later |
| 6 | Done | CTA “Open dashboard” | — | — |

**UI components:** shadcn `Button`, `Input`, `Textarea`, `Checkbox`, `Switch`, `Dialog` (edit product), `Toast` (sonner), `Progress` or step dots, `Alert` for warnings (“Instagram Business account needed”). Chat bubbles custom or 21st `Chat Messages` adapted.

**Rules (Apple onboarding):** Interactive teaching; defaults so sellers can finish fast; never dump licensing in-flow; permission copy honest (“Sell-Safe needs Instagram access to read DMs and posts you choose”).

---

## 7. Dashboard essentials

Minimal judge- and seller-ready surface (`/dashboard`):

| Area | Content | Components |
|---|---|---|
| **Orders** | List: buyer handle, item, amount (₦ tabular), status | shadcn `Table` or `Item` list, `Badge`, `Empty` |
| **Payment verdicts** | CONFIRMED / SUSPICIOUS / PENDING with reason | `Badge` + shield icon; filter `Tabs` |
| **Catalog drafts** | Approve / edit / dismiss drafted products | `Dialog` edit, `Button` approve |

Empty states invite the next action (“Connect Instagram to see orders”). No analytics vanity charts for v1.

---

## 8. Accessibility and performance

### Accessibility (WCAG AA)

- Contrast: tokens above; verify brand blue buttons on white (≥4.5:1 for label).
- Focus: visible 2px ring using `--brand-blue` at 40% offset; never remove outlines.
- Keyboard: all CTAs, tabs, accordion, demo choices, dialogs; Radix patterns for Tabs/Dialog/Accordion.
- Verdicts: text + icon + colour.
- `prefers-reduced-motion: reduce` disables theatre animations.
- Hit targets ≥ 44px on touch.
- Live regions for connect status, waitlist, demo verdict (`aria-live="polite"`).

### Performance budget

- Lighthouse ≥ 90 performance / a11y / best practices on landing.
- No WebGL heroes; DotPattern SVG only.
- Lazy-mount Magic UI theatre below the fold (`dynamic` + `inView`).
- Fonts: `next/font` for Plus Jakarta Sans + Geist Mono; `font-display: swap`.
- Images: synthetic catalog only; AVIF/WebP; width/height set.
- JS: prefer CSS for micro-interactions; Motion/Framer only where Magic UI needs it.

---

## 9. Component inventory

| Component | Source | Install | Where used |
|---|---|---|---|
| Button, Input, Textarea, Label, Field, Checkbox, Switch | **shadcn** | `npx shadcn@latest add button input textarea label field checkbox switch` | Forms, waitlist, onboarding |
| Tabs, Accordion, Dialog, Sheet, Badge, Alert, Separator, Skeleton, Progress, Scroll Area, Table, Empty, Sonner | **shadcn** | `npx shadcn@latest add tabs accordion dialog sheet badge alert separator skeleton progress scroll-area table empty sonner` | Demo, FAQ, dashboard, loading |
| Navigation Menu / Dropdown (theme) | **shadcn** | `npx shadcn@latest add dropdown-menu` | Nav ThemeToggle (existing) |
| Message / Bubble (if available in installed shadcn version) | **shadcn** | `npx shadcn@latest add message` (or custom bubbles) | Hero chat, onboarding |
| Shimmer Button | **Magic UI** | `npx shadcn@latest add @magicui/shimmer-button` | Hero primary CTA |
| Blur Fade | **Magic UI** | `npx shadcn@latest add @magicui/blur-fade` | Section entrances |
| Dot Pattern | **Magic UI** | `npx shadcn@latest add @magicui/dot-pattern` | Hero atmosphere |
| Border Beam | **Magic UI** | `npx shadcn@latest add @magicui/border-beam` | Payment demo verifying |
| Number Ticker | **Magic UI** | `npx shadcn@latest add @magicui/number-ticker` | Demo amounts |
| Marquee | **Magic UI** | `npx shadcn@latest add @magicui/marquee` | Trust strip |
| Animated Gradient Text | **Magic UI** | `npx shadcn@latest add @magicui/animated-gradient-text` | Optional hero phrase |
| Animated List | **Magic UI** | `npx shadcn@latest add @magicui/animated-list` | Demo check steps |
| Orbiting Circles | **Magic UI** | `npx shadcn@latest add @magicui/orbiting-circles` | Optional waitlist (cut if noisy) |
| Hero dual CTAs (structure) | **21st.dev** | `npx shadcn@latest add "https://21st.dev/r/uniquesonu/hero-section-enterprise-ready-landing-page-hero-with-dual-ctas?api_key=$API_KEY_21ST"` | Landing hero shell — restyle heavily |
| Chat Messages | **21st.dev** | `npx shadcn@latest add "https://21st.dev/r/nexus-ui/chat-messages?api_key=$API_KEY_21ST"` | Hero chat mock reference |
| How It Works Steps | **21st.dev** | `npx shadcn@latest add "https://21st.dev/r/ln-dev7/how-it-works-01?api_key=$API_KEY_21ST"` | 3-step section |
| Two-Column FAQ | **21st.dev** | `npx shadcn@latest add "https://21st.dev/r/ln-dev7/faqs-02?api_key=$API_KEY_21ST"` | FAQ |
| SellSafeLogo, ShieldSpinner, HeroChatMock, PaymentTheatre, TrustMarquee | **Custom** | — | Brand moments |
| PlatformTabs, ThemeToggle, WhatsAppWaitlist, PaymentSafetyDemo, SampleReplyDemo | **Existing `web/components`** | — | Evolve in place |

Prefer **fewer** Magic UI pieces: core set = Shimmer Button, Blur Fade, Dot Pattern, Border Beam, Number Ticker, Marquee. Treat Animated List / Orbiting / Gradient Text as optional.

---

## 10. Build order for tomorrow (checklist)

Priority: **hero + payment demo first.** Small, testable tasks.

### Morning — foundation + hero

- [ ] **T1** Add design tokens to `web/app/globals.css` (brand blues/violet, success/warning/danger, gradients) without breaking existing light/dark.  
  *Files:* `web/app/globals.css`, optionally `web/tailwind.config.ts`
- [ ] **T2** Install Plus Jakarta Sans + wire `next/font`; keep Geist Mono for money.  
  *Files:* `web/app/layout.tsx`
- [ ] **T3** Copy SVG logos into `web/public/brand/` and build `SellSafeLogo` (colour / mono / dark / wordmark / favicon link).  
  *Files:* `docs/design/logo/*` → `web/public/brand/`, `web/components/SellSafeLogo.tsx`
- [ ] **T4** Install Magic UI core: shimmer-button, blur-fade, dot-pattern.  
  *Cmd:* `npx shadcn@latest add @magicui/shimmer-button @magicui/blur-fade @magicui/dot-pattern`
- [ ] **T5** Build landing hero: brand, H1, sub, dual CTAs, DotPattern atmosphere, BlurFade.  
  *Files:* `web/components/landing/Hero.tsx`, update `web/app/page.tsx` or new `LandingHome.tsx`

### Midday — signature demo + chat visual

- [ ] **T6** Build `HeroChatMock` (buyer question → typing → AI reply in ₦).  
  *Files:* `web/components/landing/HeroChatMock.tsx`
- [ ] **T7** Install Border Beam + Number Ticker; upgrade `PaymentSafetyDemo` into theatre with ShieldSpinner scan → CONFIRMED/SUSPICIOUS.  
  *Cmd:* `npx shadcn@latest add @magicui/border-beam @magicui/number-ticker`  
  *Files:* `web/components/PaymentSafetyDemo.tsx`, `web/components/ShieldSpinner.tsx`
- [ ] **T8** Trust strip Marquee.  
  *Cmd:* `npx shadcn@latest add @magicui/marquee`  
  *Files:* `web/components/landing/TrustStrip.tsx`

### Afternoon — rest of landing

- [ ] **T9** How-it-works 3 steps (21st install or custom).  
  *Files:* `web/components/landing/HowItWorks.tsx`
- [ ] **T10** Features grid (4) + catalog preview scroll.  
  *Files:* `web/components/landing/Features.tsx`, `CatalogPreview.tsx`
- [ ] **T11** Restyle WhatsApp waitlist band + FAQ accordion + footer with logo.  
  *Files:* `WhatsAppWaitlist.tsx`, `landing/Faq.tsx`, layout footer

### Evening — onboarding + dashboard skeleton

- [ ] **T12** `/onboard` chat shell with steps 0–6 + “Do this later” + defaults.  
  *Files:* `web/app/onboard/page.tsx`, `web/components/onboard/*`
- [ ] **T13** `/dashboard` essentials: orders, verdicts, catalog drafts + empty states.  
  *Files:* `web/app/dashboard/page.tsx`
- [ ] **T14** A11y + reduced-motion pass; Lighthouse check; replace JPG logo usages.  
  *Files:* globals + components

**Do not touch:** `.env`, backend payment verdict logic, real customer data.

---

## 11. References browsed and inspiration

| Link | Inspired |
|---|---|
| https://magicui.design/docs/components | Catalog of restrained motion primitives |
| https://magicui.design/docs/components/shimmer-button | Primary CTA shimmer (brand gradient, not black default) |
| https://magicui.design/docs/components/blur-fade | Section entrance hierarchy |
| https://magicui.design/docs/components/border-beam | Verifying state on payment panel |
| https://magicui.design/docs/components/number-ticker | ₦ amounts without layout shift |
| https://magicui.design/docs/components/marquee | Trust strip |
| https://magicui.design/docs/components/dot-pattern | Soft hero atmosphere (not particle soup) |
| https://magicui.design/docs/components/animated-list | Optional demo checklist |
| https://magicui.design/docs/components/orbiting-circles | Optional waitlist (likely cut) |
| https://magicui.design/docs/components/animated-gradient-text | Optional single hero phrase |
| https://21st.dev/ | Registry model; prefer author components over AI average |
| https://21st.dev/community/components/s/landing-page | Hero / how-it-works / FAQ shortlist |
| https://21st.dev/@uniquesonu/components/hero-section-enterprise-ready-landing-page-hero-with-dual-ctas | Dual-CTA hero structure |
| https://21st.dev/@nexus-ui/components/chat-messages | Animated chat mock for hero |
| https://21st.dev/@ln-dev7/components/how-it-works-01 | 3-step how-it-works |
| https://21st.dev/@ln-dev7/components/faqs-02 | Two-column FAQ |
| https://ui.shadcn.com/docs/components | Forms, tabs, dialogs, accordion, empty, sonner |
| https://cursor.com/download (via `docs/design.md`) | Platform picker pattern — keep for advanced connect, not hero |
| Apple HIG onboarding / motion / branding | Skippable teach-by-doing; purposeful motion; accent restraint |
| Logo files `sell-safe.logo.jpg`, `sell-safe.logo2.jpg` | Palette `#2876FE → #6E4AF7`, navy `#071942`, soft shield geometry |

---

## Decision ledger (reference lock)

| Decision | Source | Role preserved | Why |
|---|---|---|---|
| Blue→violet 135° gradient | Logo + brief (Meta-*inspired*) | Decorative / mark / CTA shimmer only | Brand-required; not full-page indigo wash |
| Neutrals + green success | Existing `globals.css` + product verdicts | Surfaces + CONFIRMED | Continuity with built web + payment truth |
| Plus Jakarta Sans | Refero type + logo geometry | Display/UI | Premium, friendly, non-Inter |
| Payment demo as signature | Product + brief | Hero of product story | Unique vs generic SaaS feature grids |
| Fewer Magic UI animations | Motion guides + a11y | Theatre moments only | Prefer quality over quantity |
| Keep PlatformTabs + themes | Existing product | Advanced connect | Don’t break hackathon docs path |
| Chat-style onboarding + skip | Brief + Apple onboarding | Agency | Sellers finish fast or defer |

---

## Logo draft index

```
docs/design/logo/
  mark-icon.svg      # full-colour icon
  mark-wordmark.svg  # icon + Sell-Safe
  mark-mono.svg      # currentColor
  mark-dark.svg      # dark surfaces
  favicon.svg        # 32 app icon
```

Refine paths against the JPG at implementation time (optical weight of wave + check) before shipping.
