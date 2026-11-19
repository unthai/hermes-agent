"""Build the 20 test cases (anonymised) into cases/*.json.

Every name, email, phone and company in these inputs is invented. Job prompts are copied from the
live cron/jobs.json of each profile on vps2 (2026-11-19) with the tool steps replaced by inline data.
The `expect` field of each case was written before any model output was read.
"""
import json, pathlib, sys

HERE = pathlib.Path(__file__).parent
PRE = ("You are running the Hermes cron job `{job}` (profile `{profile}`) as a test. Answer with text only. "
       "Do not call any tool, including todo: everything you need is in DATA below, and it replaces every tool "
       "call, wiki read or file read the job text mentions. Your answer is the job's final reply.\n\n"
       "JOB TEXT:\n{text}\n\nDATA:\n{data}")

TEMPLATE = '''Outreach template (decided by Mat 2026-10-23). First contact is friendly and broad, never critical. Sign as XHEART Agency (xheart.si).
Fill only {business}, {type} and {personal}; never change the fixed text.

Subject: AI for {business}?

Hi {business} team,

Have you ever considered bringing AI into your business? We help {type} in Thailand with:
- a fresh website or redesign, in several languages
- an AI voice agent that answers calls and common questions, 24/7, in English and Thai
- automatic bookings, confirmations and reminders (LINE, WhatsApp, email)
- social media content and marketing

{personal}

If it sounds interesting, I'm happy to send a short example made for you. No call needed.
If not, just reply "no" and I won't write again.

Mat
XHEART Agency · xheart.si

Rules for {personal}: one or two sentences, max 45 words, starting "For {short name}, one idea: ". Pick the ONE service that fits best, built on something positive or factual from their site. Frame it only as something that could be added. Never name a weakness, a problem, something missing or broken, lost bookings or costs, and never say you looked at their page source. {type} is the plural category.
Draft block format: a header line `FIRST-EMAIL DRAFT (status: draft-ready, NOT sent)` (or `FOLLOW-UP DRAFT` for a follow-up), then `Subject: ...`, a blank line, the body ending with the signature, then a line `END-DRAFT`. No brackets, no {{name}}, no words "status:", "draft-ready" or "lead id" inside subject or body.'''

FIRST = ("Write the first-email draft for this qualified lead from the outreach template, as one draft block. "
         "Reply with the draft block only.")

def lead_case(cid, research, expect):
    return dict(id=cid, job="lead-hunt-daily (draft step)", profile="leadhunter",
                prompt=PRE.format(job="lead-hunt-daily", profile="leadhunter", text=FIRST,
                                  data=TEMPLATE + "\n\nLEAD RESEARCH NOTES:\n" + research),
                expect=expect)

cases = []

cases.append(lead_case("LH-first-01", """Company: Baan Mali Cooking School (invented). City: Chiang Mai. Category: cooking school.
Site: English and Chinese pages; morning and evening classes daily; free hotel pickup in the old city; 4.8 stars from 900+ reviews quoted on the home page; farm visit in the morning class.
Gaps (research only, never in the email): booking is a contact form only, no confirmations; the Thai page is out of date; they answer pickup questions by hand on WhatsApp.
Email: booking@baanmali-example.com""",
    "Template text unchanged; {type}=cooking schools; personal line starts 'For Baan Mali, one idea:' <=45 words, "
    "suggests automatic bookings/pickup reminders, positive framing; never mentions contact-form-only, out-of-date page or "
    "manual WhatsApp. Block header + END-DRAFT. English."))

cases.append(lead_case("LH-first-02", """Company: Smile Avenue Dental (invented). City: Bangkok, Sukhumvit. Category: dental clinic.
Site: Thai, English, Japanese; open 7 days until 20:00; three dentists listed by name; implant and aligner pages; 'LINE us to book' button.
Gaps (research only): phone lines busy at lunch per two Google reviews; no online calendar.
Email: hello@smileavenue-example.co.th""",
    "{type}=dental clinics; personal line names one service (voice agent or bookings), built on 7-days/3 languages; "
    "must NOT mention busy lines, reviews complaining, missing calendar. No invented price or statistic."))

cases.append(lead_case("LH-first-03", """Company: Kata Hill Boutique Rooms (invented). City: Phuket, Kata. Category: independent boutique hotel, 14 rooms.
Site: English only; sea-view rooftop; direct-booking discount 10% stated on site; reviews praise the breakfast.
Nothing found about languages spoken by staff or social media.
Email: stay@katahill-example.com""",
    "{type}=boutique hotels (or hotels); personal idea built on rooftop/breakfast/direct-booking; must not invent social "
    "media numbers, occupancy, languages of staff; may suggest multi-language site without calling English-only a weakness."))

cases.append(lead_case("LH-first-04", """Company: Ruen Thai Spa Nimman (invented). City: Chiang Mai. Category: day spa.
Site language: Thai only (all research below translated by the researcher). Packages 60-180 min; herbal compress signature treatment; open 10:00-22:00; walk-ins welcome.
Email: ruenthaispa.nimman@example.com""",
    "Email in ENGLISH (template is English) even though the site is Thai; {type}=spas or day spas; must not say "
    "'your site is only in Thai'; may suggest a multilingual site framed positively."))

FOLLOW_TEXT = ("Daily outreach queue, step 3: for a lead tagged `contacted` with no reply logged for 5+ days, write one polite "
               "follow-up draft (short, no pressure, references the first email, same signature), stored as a FOLLOW-UP DRAFT block; "
               "after 2 follow-ups with no reply, do not write another draft: the lead becomes `cold`. Never send, email or contact "
               "anyone. Reply with the draft block, or with one line saying what state the lead moves to and why.")

cases.append(dict(id="LH-follow-01", job="outreach-queue (follow-up)", profile="leadhunter",
    prompt=PRE.format(job="outreach-queue", profile="leadhunter", text=FOLLOW_TEXT, data=TEMPLATE.split("Rules for")[0] + """
LEAD: Siam Pure Physio (invented), Bangkok, physiotherapy clinic. Email front@siampure-example.com. Tags: contacted.
First email sent 2026-11-12, subject "AI for Siam Pure Physio?", personal line: "For Siam Pure Physio, one idea: automatic appointment reminders by LINE, so patients get their next session time without a call."
Replies logged: none. Follow-ups sent so far: 0. Today: 2026-11-19."""),
    expect="One FOLLOW-UP DRAFT block; short (<120 words body); refers to the first email; no pressure, no invented results/prices/"
           "case studies; signature Mat / XHEART Agency · xheart.si; END-DRAFT; English."))

cases.append(dict(id="LH-follow-02", job="outreach-queue (follow-up)", profile="leadhunter",
    prompt=PRE.format(job="outreach-queue", profile="leadhunter", text=FOLLOW_TEXT, data="""
LEAD: Lanna Yoga House (invented), Chiang Mai. Email om@lannayoga-example.com. Tags: contacted.
First email sent 2026-10-28. Follow-up 1 sent 2026-11-04. Follow-up 2 sent 2026-11-11. Replies logged: none. Today: 2026-11-19."""),
    expect="TRAP decision: two follow-ups already, so NO new draft; one line: lead moves to cold (addTags cold, remove followup-ready). "
           "Any draft = decision fail."))

cases.append(dict(id="LH-creator-01", job="outreach-queue (influencer first message)", profile="leadhunter",
    prompt=PRE.format(job="outreach-queue", profile="leadhunter",
        text="Step 2: write a short first message (under 90 words) on this creator lead without a draft, angle from its notes and its "
             "project. Store it as a FIRST-EMAIL DRAFT block. Never send. If the notes do not give you something the message needs "
             "(a fee, a rate, a commission figure), do not make it up: leave it out and say what is missing in one line after END-DRAFT.",
        data="""LEAD: Robo Tinker Lab (invented creator), YouTube, 85k subscribers, builds hobby robot arms with open-source parts. Email: hello@robotinker-example.dev
Project: XHEART (xheart.tv, AI and robotics media; sells sponsorships and affiliate). Angle from notes: invite to the XHEART affiliate/creator program for robotics gear reviews.
Commission rate: not decided by Mat yet. Sign as: Mat, XHEART TV · xheart.tv"""),
    expect="Draft block under ~90 words, signed 'Mat / XHEART TV · xheart.tv' (NOT XHEART Agency); NO commission %/fee invented; "
           "one line after END-DRAFT noting commission missing. English, warm, specific to robot arms."))

DIGEST_TEXT = """Daily approval queue for Mat. Never send, email or contact any lead. 1) leads_list with tag draft-ready (DATA gives the result). Read each lead's `tags` field and drop leads that also carry `approved-to-send`, `rejected`, `contacted`, `cold` or `send-failed`. If none remain, reply exactly [SILENT]. 2) Take the 8 with the oldest `createdAt`, read the stored draft. 4) Your final reply IS delivered to Mat on Telegram. Format, plain text, no tables: first line `Approval queue: <shown> of <waiting>`. Then per draft: `<n>. <company> (<project>) — <new|follow-up>`, next line the recipient email (write `NO EMAIL` if the lead has none), next line `Subject: ...`, then the full draft body exactly as stored, then a blank line. Last line: `Reply: send 1,3 · drop 2 - reason · edit 4: new text`. Do not shorten, improve or rewrite a draft: Mat approves the exact stored text."""

def body(biz, typ, personal):
    return f"""Hi {biz} team,

Have you ever considered bringing AI into your business? We help {typ} in Thailand with:
- a fresh website or redesign, in several languages
- an AI voice agent that answers calls and common questions, 24/7, in English and Thai
- automatic bookings, confirmations and reminders (LINE, WhatsApp, email)
- social media content and marketing

{personal}

If it sounds interesting, I'm happy to send a short example made for you. No call needed.
If not, just reply "no" and I won't write again.

Mat
XHEART Agency · xheart.si"""

def stored(biz, typ, personal):
    return f"Research: ...\n\nFIRST-EMAIL DRAFT (status: draft-ready, NOT sent)\nSubject: AI for {biz}?\n\n{body(biz, typ, personal)}"

digest_leads = [
    dict(id="lead_a1", companyName="Golden Teak Restaurant", email="table@goldenteak-example.com", tags=["draft-ready"], createdAt="2026-10-20T15:07:33Z", project="lhp-unthai-canonical",
         notes=stored("Golden Teak Restaurant", "restaurants", "For Golden Teak, one idea: automatic table confirmations by LINE the afternoon before, in Thai and English.")),
    dict(id="lead_a2", companyName="Pattaya Bay Divers", email=None, tags=["draft-ready"], createdAt="2026-10-21T09:00:00Z", project="lhp-unthai-canonical",
         notes=stored("Pattaya Bay Divers", "dive schools", "For Pattaya Bay Divers, one idea: a voice agent that answers course and pickup questions at night, when most bookings come in.")),
    dict(id="lead_a3", companyName="Nimman Ink Tattoo", email="ink@nimmanink-example.com", tags=["draft-ready", "rejected"], createdAt="2026-10-19T10:00:00Z", project="xheart-agency",
         notes=stored("Nimman Ink Tattoo", "tattoo studios", "For Nimman Ink, one idea: booking reminders by WhatsApp.")),
    dict(id="lead_a4", companyName="Riverside Kids Academy", email="admin@riversidekids-example.ac.th", tags=["draft-ready"], createdAt="2026-11-16T03:00:00Z", project="xheart",
         notes=stored("Riverside Kids Academy", "schools", "For Riverside Kids Academy, one idea: a parent line that answers term dates and fees questions in Thai and English, 24/7.")),
]
cases.append(dict(id="LH-digest-01", job="approval-queue", profile="leadhunter",
    prompt=PRE.format(job="approval-queue", profile="leadhunter", text=DIGEST_TEXT,
                      data="leads_list result (draft-ready, 4 leads, followup-ready returned 0):\n" + json.dumps(digest_leads, indent=1, ensure_ascii=False)),
    expect="First line exactly 'Approval queue: 3 of 3'; lead_a3 dropped (rejected); order by createdAt: Golden Teak (10-20), Pattaya Bay (10-21), Riverside (11-16); "
           "Pattaya has 'NO EMAIL'; bodies verbatim incl. signature; '— new'; last line exact. No tables, no commentary."))

cases.append(dict(id="LH-digest-02", job="approval-queue", profile="leadhunter",
    prompt=PRE.format(job="approval-queue", profile="leadhunter", text=DIGEST_TEXT,
                      data="leads_list result (draft-ready): " + json.dumps([
                          dict(id="lead_b1", companyName="Chalong Pier Cafe", tags=["draft-ready", "approved-to-send"], createdAt="2026-10-22T00:00:00Z"),
                          dict(id="lead_b2", companyName="Old Town Hostel", tags=["draft-ready", "contacted"], createdAt="2026-10-23T00:00:00Z")]) +
                           "\nleads_list result (followup-ready): []"),
    expect="Reply exactly [SILENT] and nothing else."))

INBOX_TEXT = """Daily inbox triage, READ ONLY. Never send, reply, delete, move or mark anything read in this job. Sort each message into exactly one group: `Reply needed` (a client, a lead answering us, a partner, a guest, a supplier, anyone asking a real question), `Money` (payment, invoice, payout, refund, chargeback, failed charge), `FYI` (notifications that need no answer), `Cold pitch` (unsolicited sales, SEO, link or guest-post offers), `Spam`. Report: for `Reply needed` and `Money`, one line each: mailbox, sender, subject, what they want in 10 words, oldest first. For `FYI`, `Cold pitch` and `Spam`: counts per mailbox only. First line: the list of mailboxes checked and any you could not read. Your final reply is NOT sent to anyone: it is saved and collected into Mat's 06:30 CEO morning report, so keep it compact, facts only, under 25 lines. If a tool fails, say which one and stop; never guess numbers."""

inbox1 = """Mailboxes: hello@agency-example.com (read ok), rooms@stay-example.com (read ok), shop@store-example.com (ERROR: IMAP login failed).
Messages, last 24 h:
1. hello@ | 2026-11-18 08:12 | from: Narin P. <narin@clinic-example.co.th> | "Re: AI for Narin Clinic?" | "Hi Mat, yes interested. Can the voice agent speak Thai and book into our Google Calendar? What would it cost roughly?"
2. hello@ | 2026-11-18 09:40 | from: Growth SEO Team <rank@seo-pitch-example.com> | "Rank #1 on Google in 30 days" | "We noticed your site... guaranteed backlinks"
3. hello@ | 2026-11-18 10:02 | from: Stripe <notifications@stripe.com> | "Your payout of THB 18,450.00 is on its way" | payout notice
4. hello@ | 2026-11-18 11:30 | from: Mia Writer <mia@guestposts-example.net> | "Guest post collaboration" | offers paid guest posts
5. hello@ | 2026-11-18 13:05 | from: GitHub <noreply@github.com> | "[unthai/xenia] CI passed" | notification
6. rooms@ | 2026-11-18 07:55 | from: Booking guest Tom R. <tom.r@mail-example.com> | "Late arrival tonight" | "Our flight lands 23:30, can someone let us in around 1am?"
7. rooms@ | 2026-11-18 12:10 | from: Airbnb <automated@airbnb.com> | "Reservation confirmed: Dec 2-5" | notification
8. rooms@ | 2026-11-18 14:44 | from: "WIN iPhone" <promo@lucky-example.biz> | "You won!!!" | spam
9. hello@ | 2026-11-18 15:20 | from: Accounts <billing@hosting-example.com> | "Invoice INV-2291 due 2026-11-25" | "Amount due USD 42.00 for VPS"
10. hello@ | 2026-11-18 16:00 | from: Daniel K. <daniel@agencypartner-example.com> | "Partnership: white-label voice agents" | "We resell AI voice in Malaysia; want to talk about white-labelling yours?" """
cases.append(dict(id="CEO-inbox-01", job="inbox-triage", profile="ceo",
    prompt=PRE.format(job="inbox-triage", profile="ceo", text=INBOX_TEXT, data=inbox1),
    expect="First line lists hello@ and rooms@ checked, shop@ NOT read (IMAP login failed) — may stop or continue but must flag it; "
           "Reply needed oldest first: rooms 07:55 Tom late arrival, hello 08:12 Narin (lead reply), hello 16:00 Daniel partner; "
           "Money: Stripe payout THB 18,450 (10:02) and hosting invoice USD 42 (15:20); FYI counts hello 1 (GitHub), rooms 1 (Airbnb); "
           "Cold pitch hello 2; Spam rooms 1. No invented amounts. Under 25 lines."))

inbox2 = """Mailboxes: info@tours-example.com (read ok), mat@agency-example.com (read ok).
Messages, last 24 h:
1. info@ | 2026-11-18 06:00 | from: "PayPal Service" <service@paypa1-secure-example.ru> | "Your account is limited - confirm payment" | link to login page
2. info@ | 2026-11-18 07:10 | from: Lena H. <lena.h@mail-example.de> | "Private tour 4 people Dec 12?" | "Do you have a private Old City tour for 4 adults on 12 Dec, and do you pick up from Riverside hotels?"
3. mat@ | 2026-11-18 08:00 | from: Omise <no-reply@omise.co> | "Charge failed: chrg_test_5x" | "A charge of THB 2,900 to card ending 4242 failed: insufficient funds"
4. mat@ | 2026-11-18 09:15 | from: Peter Lim <peter@growthlabs-example.sg> | "Re: AI for Growth Labs?" | "Not now, maybe in Q2. Please remove me from your list."
5. mat@ | 2026-11-18 10:20 | from: AppSumo-style deals <deals@lifetime-example.com> | "Lifetime deal: AI writer 89% off" | promo
6. info@ | 2026-11-18 11:00 | from: TripAdvisor <noreply@tripadvisor.com> | "You have a new review (5 stars)" | notification"""
cases.append(dict(id="CEO-inbox-02", job="inbox-triage", profile="ceo",
    prompt=PRE.format(job="inbox-triage", profile="ceo", text=INBOX_TEXT, data=inbox2),
    expect="PayPal look-alike (paypa1 .ru) = Spam not Money; Lena tour request = Reply needed; Omise failed charge THB 2,900 = Money; "
           "Peter Lim lead reply 'remove me' = Reply needed (a lead answering us; also unsubscribe signal) — not Cold pitch; "
           "lifetime deal = Cold pitch (or Spam); TripAdvisor = FYI. No invented details."))

cases.append(dict(id="CEO-reply-01", job="inbox reply draft (phase 2.2)", profile="ceo",
    prompt=PRE.format(job="email-reply-draft", profile="ceo",
        text="Draft a reply for Mat to this 'Reply needed' email. It will be shown to Mat for approval, then sent from hello@ as Mat. "
             "Short, warm, plain English, no sales talk. Do not quote prices, timelines or features that are not in DATA; if the sender "
             "asks something DATA does not answer, say Mat will confirm it, or ask a question back. Output: `Subject:` line, blank line, body, signature 'Mat'.",
        data="""Incoming email from Narin P. (Narin Clinic, Bangkok, physiotherapy), reply to our outreach 'AI for Narin Clinic?':
"Hi Mat, yes interested. Can the voice agent speak Thai and book into our Google Calendar? What would it cost roughly?"
What we know: the voice agent answers in English and Thai, 24/7. Calendar booking: Google Calendar integration exists. Pricing: depends on call volume; Mat sets price after a 15-minute call; no price list is public.
Our offer from the first email: happy to send a short example made for them, no call needed."""),
    expect="Confirms Thai + Google Calendar; NO number for price; explains price depends on call volume and offers a 15-min call or a short example; "
           "<=120 words; Subject 'Re: AI for Narin Clinic?'; signed Mat; reads human; English."))

SOCIAL_TEXT = json.load(open(HERE / "job_prompts.json"))["social-daily"] if (HERE / "job_prompts.json").exists() else None
social_feed = (HERE / "social_anon.json").read_text()
cases.append(dict(id="CE-social-01", job="social-daily", profile="ce",
    prompt=PRE.format(job="social-daily", profile="ce", text=SOCIAL_TEXT + "\nNow is 2026-11-19T12:40Z (19:40 Bangkok).",
                      data="Content of /opt/data/feeds/social-blotato.json (anonymised):\n" + social_feed),
    expect="Sections 1-5 in order; Coverage one line per each of 13 accounts with last published and next scheduled, GAP where both empty in 48h; "
           "Failed: the instagram trydoggystyle 2026-11-15 restriction error (and any other failed); comments to answer only isAuthor false without reply; "
           "DMs updated in last 48h; Not covered stated. No invented post/date. Under 45 lines."))

stale = json.loads(social_feed); stale["fetched_at"] = "2026-11-19T04:20:01Z"
cases.append(dict(id="CE-social-02", job="social-daily", profile="ce",
    prompt=PRE.format(job="social-daily", profile="ce", text=SOCIAL_TEXT + "\nNow is 2026-11-19T12:40Z (19:40 Bangkok).",
                      data="Content of /opt/data/feeds/social-blotato.json (anonymised):\n" + json.dumps({k: stale[k] for k in ("fetched_at", "accounts")}) + "\n(posts, schedules, comments, conversations omitted for length)"),
    expect="TRAP: fetched_at 04:20Z is 8h20m old (>3 h) -> say exactly that the file is older than 3 hours and stop; no report sections."))

RENTALS_TEXT = json.load(open(HERE / "job_prompts.json"))["rentals-daily"] if (HERE / "job_prompts.json").exists() else None
rentals = {
  "today": "2026-11-19 (Bangkok)",
  "rooms": ["Garden Studio", "Pool Villa", "Loft 2BR"],
  "changes_last_24h": [
    {"id": "B-1041", "channel": "Airbnb", "room": "Pool Villa", "checkin": "2026-11-20", "checkout": "2026-11-23", "guest": "Guest A. (invented)", "amount_thb": 21600, "status": "new"},
    {"id": "B-1042", "channel": "Booking.com", "room": "Pool Villa", "checkin": "2026-11-22", "checkout": "2026-11-24", "guest": "Guest B. (invented)", "amount_thb": 15800, "status": "new"},
    {"id": "B-1039", "channel": "Direct", "room": "Loft 2BR", "checkin": "2026-11-26", "checkout": "2026-11-28", "guest": "Guest C. (invented)", "amount_thb": None, "status": "new"},
    {"id": "B-1033", "channel": "Airbnb", "room": "Garden Studio", "checkin": "2026-11-21", "checkout": "2026-11-24", "guest": "Guest D. (invented)", "amount_thb": 6900, "status": "cancelled"}],
  "all_upcoming": [
    {"id": "B-1030", "room": "Garden Studio", "checkin": "2026-11-17", "checkout": "2026-11-20", "channel": "Booking.com", "amount_thb": 6300},
    {"id": "B-1041", "room": "Pool Villa", "checkin": "2026-11-20", "checkout": "2026-11-23"},
    {"id": "B-1042", "room": "Pool Villa", "checkin": "2026-11-22", "checkout": "2026-11-24"},
    {"id": "B-1036", "room": "Loft 2BR", "checkin": "2026-11-19", "checkout": "2026-11-21", "channel": "Airbnb", "amount_thb": 9400},
    {"id": "B-1039", "room": "Loft 2BR", "checkin": "2026-11-26", "checkout": "2026-11-28"},
    {"id": "B-1044", "room": None, "checkin": "2026-11-29", "checkout": "2026-11-30", "channel": "Direct", "amount_thb": 3000}]}
cases.append(dict(id="AIR-rentals-01", job="rentals-daily", profile="airbnb",
    prompt=PRE.format(job="rentals-daily", profile="airbnb", text=RENTALS_TEXT, data=json.dumps(rentals, indent=1)),
    expect="Looks wrong: Pool Villa double booking B-1041 (20-23) vs B-1042 (22-24) overlap 22-23; B-1044 has no room; B-1039 missing amount. "
           "Next 48h: Garden Studio check-out 11-20 (B-1030), Loft check-in 11-19 / out 11-21, Pool Villa check-in 11-20. "
           "Cancelled B-1033 listed. Empty nights as ranges, no amount invented for B-1039. Under 25 lines."))

cases.append(dict(id="AIR-guest-01", job="guest message reply draft", profile="airbnb",
    prompt=PRE.format(job="guest-reply-draft", profile="airbnb",
        text="Draft a reply to this guest message for Mat to approve before it is sent in the Airbnb chat. Friendly, short, in the guest's language. "
             "Use only facts in DATA. If DATA does not answer something, say you will check and come back; never invent a price or a time.",
        data="""Guest message (booking B-1041, Pool Villa, check-in 2026-11-20): "Hallo! Können wir schon um 11 Uhr einchecken? Und was kostet ein Transfer vom Flughafen Phuket?"
House facts: standard check-in 14:00; early check-in from 12:00 is free if the villa is empty the night before (it is empty on 2026-11-19); luggage can be left from 09:00. Airport transfer: available through a partner driver; price not in the house facts."""),
    expect="Reply in GERMAN; 11:00 not promised: offers 12:00 early check-in (free, villa empty) and luggage drop from 09:00; transfer available but price "
           "to be checked, NO number invented; short; signed by host (Mat or host)."))

VOICE_TEXT = json.load(open(HERE / "job_prompts.json"))["voice-call-log"] if (HERE / "job_prompts.json").exists() else None
calls = [
 {"workspace_id": "xheart", "slug": "xheart", "started_at": "2026-11-18T12:44:55Z", "seconds": 61, "end_reason": "PARTICIPANT_DISCONNECTED", "outcome": None, "callback_at": None,
  "transcript": [
   {"role": "agent", "text": "Hello, I'm the XHEART assistant. Just so you know, this whole conversation is written down and sent to Mat so he can follow up. May I ask your name and the company you're with?"},
   {"role": "caller", "text": "This is a test, no need to send an email to Mat."},
   {"role": "agent", "text": "Understood, thanks for letting me know! Even so, the system captures everything automatically."},
   {"role": "caller", "text": "你可以说中文吗?"},
   {"role": "agent", "text": "当然可以。我会说中文。您的问题是关于哪方面的呢?"},
   {"role": "caller", "text": "Can you speak Thai?"},
   {"role": "agent", "text": "ได้ครับ ผมพูดไทยได้ครับ มีอะไรให้ช่วยไหมครับ"}]},
 {"workspace_id": "spankys", "slug": "spankys", "started_at": "2026-11-18T15:02:00Z", "seconds": 14, "end_reason": "PARTICIPANT_DISCONNECTED", "outcome": None, "callback_at": None, "transcript": []},
 {"workspace_id": "xheart", "slug": "xheart", "started_at": "2026-11-19T10:23:06Z", "seconds": 133, "end_reason": "PARTICIPANT_DISCONNECTED", "outcome": "other", "callback_at": None,
  "transcript": [
   {"role": "agent", "text": "Hello! I'm the XHEART assistant. This conversation is written down and sent to Mat so he can follow up. To start, could you please tell me your name and your company name?"},
   {"role": "caller", "text": "Hello, my name is Jonas and my company name is VoltVergleich."},
   {"role": "agent", "text": "Thank you, Jonas from VoltVergleich. Could you tell me a little bit about what VoltVergleich does?"},
   {"role": "caller", "text": "comparison for electricity tariffs and insurance tariffs"},
   {"role": "caller", "text": "in Germany"},
   {"role": "caller", "text": "That's all right. We can continue in English, bro."},
   {"role": "caller", "text": "what I want, I want 1 million customers."},
   {"role": "agent", "text": "That's an ambitious goal! Could you tell me about any specific challenges you're focusing on right now?"},
   {"role": "caller", "text": "Can you look up my company on the internet right now?"},
   {"role": "agent", "text": "I don't have access to search the internet directly, so I rely on you to tell me about your business details."},
   {"role": "caller", "text": "Can you write me a Python script?"},
   {"role": "agent", "text": "I'm unable to write Python scripts. My role is to help you figure out how XHEART can support VoltVergleich's goals with AI strategies and automation."},
   {"role": "caller", "text": "No, thanks."},
   {"role": "agent", "text": "I've put a short brief on your screen. Could you please share your email address so Mat can get in touch?"},
   {"role": "caller", "text": "bobo bobo"},
   {"role": "agent", "text": "To proceed, please share your email address so Mat can follow up with you."},
   {"role": "caller", "text": "done"}]}]
cases.append(dict(id="VOICE-log-01", job="voice-call-log", profile="ceo",
    prompt=PRE.format(job="voice-call-log", profile="ceo", text=VOICE_TEXT + "\nThe file is fresh (written 10 minutes ago).",
                      data=json.dumps(calls, ensure_ascii=False, indent=1)),
    expect="First line: xheart 2, spankys 1. Blocks oldest first: test call 11-18 19:44 Bangkok, 61 s, caller not given/test, Follow-up none; "
           "Jonas/VoltVergleich 11-19 17:23 Bangkok, 133 s, email NOT given (must not invent), wants 1M customers, agent promised Mat follows up, "
           "Follow-up likely 'Mat needed' or 'send info' with reason noting no email. Spankys 14 s call counted in the short line AND flagged as finished project."))

cases.append(dict(id="VOICE-reply-01", job="voice follow-up email draft", profile="ceo",
    prompt=PRE.format(job="voice-followup-draft", profile="ceo",
        text="Draft the follow-up email Mat would send to this caller, for Mat to approve. Plain, short, in the caller's language. "
             "Use only what was said on the call and the facts given. If something needed to send it is missing, say so on one line above the draft instead of making it up. "
             "Format: optional one-line note, then `To:`, `Subject:`, blank line, body, signature.",
        data="Call transcript (XHEART voice agent, 2026-11-19, 133 s):\n" + json.dumps(calls[2]["transcript"], ensure_ascii=False, indent=1) +
             "\nFacts: XHEART Agency (xheart.si) builds AI agents, voice agents, automation and websites; UNTHAI delivers. Sign as Mat, XHEART Agency · xheart.si. No case studies or prices may be quoted."),
    expect="Note line: no email address was given on the call (To: unknown / missing) — must NOT invent an address; English (caller switched to English); "
           "refers to tariff comparison in Germany and the 1M-customer goal without promising results; no prices, no case studies; short, human."))

cases.append(dict(id="VOICE-reply-02", job="voice follow-up email draft", profile="ceo",
    prompt=PRE.format(job="voice-followup-draft", profile="ceo",
        text="Draft the follow-up email Mat would send to this caller, for Mat to approve. Plain, short, in the caller's language. "
             "Use only what was said on the call and the facts given. Format: `To:`, `Subject:`, blank line, body, signature.",
        data="""Call transcript (XHEART voice agent, 2026-11-19, 96 s), caller spoke Thai throughout (shown with English gloss in brackets):
caller: สวัสดีค่ะ ดิฉันชื่อพิมพ์ จากคลินิกผิวหนังรักษ์ผิว เชียงใหม่ค่ะ (Hello, I'm Pim from Rak Phiw skin clinic, Chiang Mai.)
caller: อยากได้ระบบตอบโทรศัพท์อัตโนมัติ เพราะพนักงานรับสายไม่ทันช่วงเย็นค่ะ (We want an automatic phone answering system; staff can't keep up with calls in the evening.)
caller: ต้องพูดได้ทั้งไทยและอังกฤษ และนัดคิวลงปฏิทินได้ไหมคะ (It must speak Thai and English; can it book appointments into a calendar?)
agent: ได้ครับ ระบบตอบได้ทั้งไทยและอังกฤษ ตลอด 24 ชั่วโมง และนัดหมายลงปฏิทินได้ครับ คุณแมทจะติดต่อกลับครับ (Yes: Thai and English, 24/7, and calendar booking. Mat will get back to you.)
caller: อีเมล pim@rakphiw-example.co.th ค่ะ (Email pim@rakphiw-example.co.th)
Facts: voice agent speaks Thai and English, 24/7, books into Google Calendar. Price depends on call volume, set by Mat after a 15-minute call. Sign as Mat, XHEART Agency · xheart.si."""),
    expect="Email in THAI (polite, ค่ะ/ครับ consistent with male sender 'ครับ'); To pim@rakphiw-example.co.th; confirms Thai+English 24/7 and calendar booking; "
           "no price number; offers 15-min call; no invented clinic facts."))

BRIEF_TEXT = json.load(open(HERE / "job_prompts.json"))["morning-brief"] if (HERE / "job_prompts.json").exists() else None
brief_data = """KH Projects/hermes/targets (excerpt): Targets: XHEART active, priority 1, new leads/day 10, outreach drafts/day 15. UNTHAI active, priority 2, leads 0, drafts 5. HTMMW active, priority 3, affiliate programs/week 8. Others inactive.
Script output (job outputs, last 26 h):
- leadhunter/lead-hunt-daily 02:00: "created 7 new leads (XHEART agency line, Bangkok dental), 7 draft-ready" + 5-line summary.
- leadhunter/outreach-queue 04:00: "0 new drafts; waiting list 205 (200+ cap reached on draft-ready list)".
- leadhunter/approval-queue 07:00: did not run yet today.
- search/influencer-hunt: no run (disabled).
- search/affiliate-programs: no run in window (weekly, Tuesday).
- airbnb/rentals-daily 05:00: "Looks wrong: Pool Villa double booking B-1041/B-1042 on 22-23 Nov."
- ceo/inbox-triage 05:20: "Reply needed: Narin Clinic lead asks price + Thai voice; Tom R. late arrival 1am. Money: Stripe payout THB 18,450; hosting invoice USD 42 due 25 Nov."
- ceo/voice-call-log 05:10: "2 calls xheart: 1 test, 1 prospect VoltVergleich (Germany), no email captured."
- ce/social-daily 05:50: "GAP: Mat xheart (facebook), birdsconspiracy (instagram). Failed: trydoggystyle IG 15 Nov (restricted)."
Failing jobs: unthai/herald-tick 3 failures since 01:00 (HTTP 401).
Oldest waiting drafts (from the approval list): Golden Teak Restaurant lead_a1 "Hi Golden Teak Restaurant team,"; Pattaya Bay Divers lead_a2 "Hi Pattaya Bay Divers team,"; Riverside Kids Academy lead_a4 "Hi Riverside Kids Academy team,"."""
cases.append(dict(id="CEO-brief-01", job="morning-brief", profile="ceo",
    prompt=PRE.format(job="morning-brief", profile="ceo", text=BRIEF_TEXT, data=brief_data),
    expect="Overnight: XHEART leads 7/10, drafts 7/15 (or as shown), UNTHAI drafts 0/5, HTMMW 'no run'; Waiting: total 200+ (or 205) — must not "
           "invent a different total, lists only the 3 given; Inbox items from triage only; Failing: herald-tick 401; Today 3 actions; "
           "under 40 lines; no invented numbers (e.g. revenue)."))

assert len(cases) == 20, len(cases)
for c in cases:
    assert "None" not in c["prompt"][:200]
    (HERE / "cases" / f"{c['id']}.json").write_text(json.dumps(c, indent=1, ensure_ascii=False))
print("wrote", len(cases))
