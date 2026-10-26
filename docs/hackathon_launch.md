# Hackathon Launch
Deadline Nov 4, 9:00 PM ET (Nov 5, 02:00 WAT). Target submit Nov 4, 18:00 WAT. **TODO verify** submission platform (Devpost vs Cerebral Valley) and required fields from the official hackathon page/email.

## Submission checklist
- [ ] Public GitHub repo, MIT license, clean history (gitleaks run)
- [ ] README: pitch, GIF, architecture image, setup, Meta models used
- [ ] Demo video ≤3 min, unlisted YouTube/Loom link works logged-out
- [ ] Live deployment URL + WhatsApp test number instructions (or video is enough – check rules)
- [ ] Screenshots: catalog, buyer chat (Pidgin + Yoruba), SUSPICIOUS verdict, CONFIRMED by webhook, daily summary
- [ ] Write-up filled; track = Indie
- [ ] `LLM_PROVIDER=meta` in production and proof of Meta model calls (logs/screenshot)
- [ ] Confirmation email/screenshot saved

## Judging angle
- **Meta models are the core:** Muse vision for catalog and receipt extraction, Muse Spark for multilingual chat and tool calling, Muse Image and SAM 3.1 where the demo uses them, all on the Meta Model API. State the exact ids once verified (**TODO verify**). Groq is a dev fallback and must be labeled as such if the demo still uses it.
- **Meta platforms:** WhatsApp Cloud API, Instagram, Messenger – one brain, three channels.
- **Real problem, real user:** founder's own fake-alert story; Nigerian languages.
- **Safety:** ledger/webhook beats screenshot; "don't release goods" rule; no false confirmations in eval.
- **Efficiency:** Jev routes cheaply so Muse is called only when needed. Intron Sahara handles voice notes.

## Demo storyboard (≈2:45) – draft by Oct 30, record Nov 1 (rough) and Nov 3 (final ×2)
| Time | Scene | Visual | Voiceover |
|---|---|---|---|
| 0:00–0:20 | Hook | Me on camera / fake alert screenshot | "Last year someone almost walked away with my goods using a fake transfer screenshot. It happens to sellers every day." |
| 0:20–0:35 | Intro | Logo + one-liner | "Sell-Safe is a WhatsApp shop assistant powered by Meta Muse that sells for you and catches fake payments." |
| 0:35–1:00 | Catalog | Seller sends photo → product card | "Snap a photo, Muse vision writes the listing." |
| 1:00–1:30 | Buyer chat | Buyer in Pidgin, then Yoruba, orders | "Buyers ask in Pidgin or Yoruba; it answers from your real catalog and takes the order." |
| 1:30–2:05 | Fake caught | Edited screenshot → ⚠️ SUSPICIOUS + reasons + DON'T RELEASE | "The receipt looks real. Sell-Safe checks the bank side: no money arrived, the reference was reused." |
| 2:05–2:25 | Real pay | Paystack test transfer → ✅ CONFIRMED by bank webhook | "Real money? Confirmed in seconds, straight from the bank webhook." |
| 2:25–2:40 | Scale | IG DM same flow, daily summary "₦ saved from fakes" | "Same brain on Instagram and Messenger." |
| 2:40–2:50 | Close | Architecture slide + Meta logos, plus one benchmark headline that was actually measured | "Built on Muse and Meta's platforms. Sell-Safe: sell more, get scammed less." |
Recording tips: screen-record phone via scrcpy or WhatsApp Web; pre-seed data; script read aloud; captions; 1080p; no real phone numbers/accounts visible.

## Write-up outline
1. Inspiration (scam story) 2. What it does 3. How we built it (Muse Spark / Muse vision / Muse Image / SAM 3.1 on the Meta Model API, Intron Sahara for speech, WhatsApp/IG/Messenger, Jev, Paystack, Supabase) 4. Challenges (card restriction → provider abstraction; Yoruba and Pidgin; tamper detection) 5. Accomplishments: only numbers copied from the benchmark report. The target is zero false CONFIRMED on fakes; do not write that sentence until `docs/benchmark.md` has a measured numerator and denominator 6. What we learned 7. What's next (bank partnerships, Android alert forwarder, Hausa and Igbo) 8. Built with.

## Pre-submit tests (Nov 4 morning)
- [ ] Fresh WhatsApp number: full order → pay (test) → CONFIRMED
- [ ] Fake screenshot → SUSPICIOUS, release blocked (409)
- [ ] Duplicate webhook → processed once
- [ ] Bad signature → 401
- [ ] Yoruba + Pidgin replies checked by a native speaker
- [ ] `pytest`, eval script, gitleaks all green
- [ ] Video link opens in incognito
