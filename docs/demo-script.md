# Demo script (3–4 minutes)

**Setup (before judging):** `make seed && make api` (terminal 1), `make web`
(terminal 2). Open `http://localhost:3000`. Language toggle top-right.

---

### 0:00 — The problem (30s)
> "Digital-arrest scams stole hundreds of crores from Indians. Scammers impersonate
> the CBI, isolate victims on video calls for hours, and extract 'safe account'
> transfers. Keyword filters miss this because no single sentence is the scam —
> **the sequence is the scam**. ScamShield AI detects the psychological coercion
> sequence and interrupts fraud *before payment*."

### 0:30 — Live simulation (90s)
Open **Live Demo** → click **▶ Play scripted scam call** repeatedly.

Narrate the risk climb as each stage lands:
- "TRAI… illegal parcel" → *authority impersonation + Aadhaar hook — 12%*
- "CBI officer… money laundering case" → *accusation + sequence bonus — 27%*
- "Do not tell your family… confidential" → *isolation + secrecy — 54%, High*
- "Do not disconnect… digital arrest" → *continuous-call control + threat — 75%*
- **Safety Mode fires automatically**: full-screen STOP with the exact guidance a
  panicking victim needs, in English or Hindi (toggle it live —
  "रुकिए। यह डिजिटल अरेस्ट धोखाधड़ी…").
- Dismiss, play the final line: "₹50,000 to the safe RBI account" → *100%,
  and the UPI ID is flagged — already reported in 8 other complaints.*

Point at the assessment panel: every point traces to a named rule; sequence
bonuses are listed explicitly; confidence and engine version shown.

### 2:00 — Evidence report (30s)
Click **Full report view** → **Generate evidence report**. Open the PDF:
case ID, timestamps, consent, coercion sequence, masked entities, SHA-256
hashes, audit trail, human-review disclaimer. "Court-ready structure, one click."

### 2:30 — Command Centre (45s)
**Command Centre** → login with the demo token.
- Cards: complaints, critical cases, **% detected before payment request**.
- **Fraud network**: the ring is obvious — one UPI ID connected to 8 complaints
  across cities; suspected-mule ranking below. "Every complaint makes the next
  detection stronger."
- Hotspot map (synthetic data, labelled as such).

### 3:15 — Close (30s)
> "Explainable rules, not a black box: our evaluation script shows the
> sequence-aware engine beats a keyword baseline — with zero false positives on
> the legitimate set, including a genuine bank-awareness SMS that keyword tools
> flag. Privacy is built in: consent, masking, hashing, append-only audit.
> Everything you saw runs offline — no paid APIs. ScamShield AI: detect coercion,
> interrupt fraud, protect before payment."

---

**Fallbacks:** if the network dies, everything is local; if the browser dies,
`python scripts/generate_demo_report.py` produces the PDF from the terminal.
Reset between runs: `make reset`.
