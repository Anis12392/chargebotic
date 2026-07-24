"""
Creates a Google Doc with the full pitch deck text, slide by slide,
each slide paired with the Slidebean rule it applies.
Uses Drive API upload + conversion (works with drive scope, no Docs API needed).

Run: python3 execution/create_pitch_text_doc.py
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
]
ROOT = os.path.expanduser("~/claude-code-official-memory")
TOKEN_PATH = os.path.join(ROOT, "token.json")
HTML_PATH = os.path.join(os.path.dirname(__file__), ".pitch_text.html")

HTML = """
<h1>Chargebotic Pitch Deck, Full Text</h1>
<p><i>Structure: Slidebean method. A deck answers four questions.
1. What opportunity have you discovered? 2. What are you building?
3. How much will you grow? 4. Why are you the team to win?
Deck must be consumable in 4 minutes. No embedded video.</i></p>

<h2>Slide 1. Cover</h2>
<p><b>Slidebean rule:</b> the cover carries a 5 to 7 word explainer of what you do. Not a slogan. Practice it on strangers.</p>
<p><b>Title:</b> CHARGEBOTIC</p>
<p><b>Headline:</b> Energy from the line. Delivered.</p>
<p><b>Blurb:</b> Drones that harvest energy from power lines to run ground systems.</p>

<h2>Slide 2. Traction teaser</h2>
<p><b>Slidebean rule:</b> optional hook slide. If something exciting is happening, show it early to frame the whole read.</p>
<p><b>Headline:</b> Defense is already paying for this.</p>
<ul>
<li>Paid pilot signed with Chariot Defense (a16z backed, $41M raised): 2 units, $80K</li>
<li>Demonstration on a military base in August 2026 (JIFX, Camp Roberts CA)</li>
<li>Selected by Founders Inc and Nvidia Inception</li>
</ul>

<h2>Slide 3. Problem</h2>
<p><b>Slidebean rule:</b> short undisputable lines, facts not opinions, backed by sources. Money or time wasted. This slide sets your credibility (his references: Airbnb, Uber, Dropbox problem slides).</p>
<p><b>Headline:</b> Power at the edge still travels by truck.</p>
<ul>
<li>Forward positions run on generators, and generators run on fuel convoys</li>
<li>In Iraq and Afghanistan, roughly 1 casualty for every 24 fuel resupply convoys (Army Environmental Policy Institute, 2009)</li>
<li>Generators broadcast heat and noise. Batteries last hours. Missions last weeks.</li>
</ul>

<h2>Slide 4. Solution</h2>
<p><b>Slidebean rule:</b> the solution slide answers the problem slide line by line (his Airbnb redesign example). It is about the approach, not yet the product.</p>
<p><b>Headline:</b> The power is already there. Overhead.</p>
<ul>
<li>Power lines cross almost every environment we operate in</li>
<li>Our drone perches on the line and harvests energy directly from it</li>
<li>Power flows down a tether to systems on the ground</li>
<li>No convoys. No generator signature. Power for as long as the line is live.</li>
</ul>

<h2>Slide 5. Product (2 slides, visual)</h2>
<p><b>Slidebean rule:</b> maximize space for showing the product. Two or three slides is fine. No video demos, investor attention is about 4 minutes.</p>
<p><b>Slide 5a headline:</b> The system.</p>
<ul>
<li>Kestrel: the drone, carries the Magline energy harvesting payload</li>
<li>Magline: harvests energy from live lines by magnetic induction</li>
<li>Tether: delivers power and communications to the ground</li>
<li>Ground station: plugs into standard battery systems (integrated today with Chariot Amphora)</li>
</ul>
<p><b>Slide 5b headline:</b> How it works.</p>
<p>Deploy. Launch. Reach. Perch. Deliver energy. Power the mission.
The system finds the line, flies to it, attaches, and harvests. Autonomous operation is the product; our August 2026 field demo flies piloted while the autonomy stack completes.</p>

<h2>Slide 6. Target audience and case study</h2>
<p><b>Slidebean rule:</b> a key and often forgotten slide. The answer is never everyone. A case study can answer who the customer is and prove value at the same time.</p>
<p><b>Headline:</b> Silent watch, powered for weeks.</p>
<p>A robotic combat vehicle drives deep into contested territory carrying comms and sensors. It shuts its engine off to kill its heat and acoustic signature. Our drone launches to a nearby power line and feeds the vehicle for days or weeks. The sensor hears an incoming threat, the alert reaches base, the engine never restarts.</p>
<p><b>Customer:</b> defense integrators building unmanned ground systems and edge infrastructure. Their end user: military units operating beyond the grid.</p>

<h2>Slide 7. Business model</h2>
<p><b>Slidebean rule:</b> just tell us how you make money. No forecasts, no scenarios. Keep it simple and clean.</p>
<p><b>Headline:</b> Every unit sold carries recurring revenue.</p>
<ul>
<li>Hardware: drone with harvesting payload, sold per unit</li>
<li>Software: find the line, fly, attach, harvest. Licensed per unit per year</li>
<li>Training: operator certification per deployment</li>
<li>Insurance: replacement plan when a unit fails, per unit per year</li>
</ul>

<h2>Slide 8. Roadmap</h2>
<p><b>Slidebean rule:</b> place the roadmap after the business model, it bridges the product section to the growth section.</p>
<p><b>Headline:</b> From field demo to fleet.</p>
<ul>
<li>Now: TRL 4, harvesting validated on the bench, pilot contract signed</li>
<li>Aug 2026: JIFX field demo at Camp Roberts with Chariot, piloted flight, target TRL 6</li>
<li>Q4 2026: real power line pilot, success threshold agreed with the customer</li>
<li>2027: autonomy stack released, pilot converts to fleet orders</li>
</ul>

<h2>Slide 9. Traction</h2>
<p><b>Slidebean rule:</b> stage honesty. Pre seed companies are not expected to show revenue, so a paid pilot puts you ahead of the bar. Show the ladder, not a claim.</p>
<p><b>Headline:</b> One account, a clear ladder.</p>
<ul>
<li>Signed: paid pilot, 2 units, $80K, Chariot Defense</li>
<li>Next: military base demonstration Aug 2026 (JIFX, Camp Roberts), then a real line test with agreed success criteria</li>
<li>Then: expansion order. This single account is worth about $6.5M per year at 100 units.</li>
<li>Also in motion: Letter of Interest from the largest US utility inspection company, inbound interest from Terna, Italy's national grid operator</li>
<li>All of this built by a team of 4</li>
</ul>

<h2>Slide 10. Go to market</h2>
<p><b>Slidebean rule:</b> the slide 9 out of 10 companies get wrong. Not a list of tactics. Walk the conversion journey: who the decision maker is, how you reach them, how the sales cycle works.</p>
<p><b>Headline:</b> We do not sell to the military. Our partners do.</p>
<ul>
<li>Channel: defense integrators who already hold customer relationships. Chariot embeds our system into their power hub and co markets it.</li>
<li>Proof engine: each field demo produces footage and data that becomes the partner's sales collateral</li>
<li>Sales cycle: pilot, joint customer discovery, expansion order. Price point validated with the partner's customers, not guessed.</li>
<li>Second market, later: power line inspection for utilities. Same drone, same perch, different payload economics. Two grid operators are already talking to us.</li>
</ul>

<h2>Slide 11. Market size</h2>
<p><b>Slidebean rule:</b> TAM is how big your business gets, not the size of an industry. Customers times revenue per customer, with a validated price.</p>
<p><b>Headline:</b> Customers times revenue, not a market report.</p>
<ul>
<li>US military operates about 250,000 ground vehicles moving toward unmanned and sensor heavy configurations</li>
<li>Validated price: $40K per unit hardware, plus recurring software and insurance</li>
<li>One integrator account alone reaches $6.5M per year at 100 units</li>
<li>Expansion market: power line inspection, a $30B+ global problem, reachable with the same aircraft</li>
</ul>

<h2>Slide 12. Team, secret sauce, competition</h2>
<p><b>Slidebean rule:</b> competition slide shows what you understand that others do not. Secret sauce is the unfair advantage. The team slide proves the core skills for THIS business are in the room.</p>
<p><b>Headline:</b> Energy people who build aircraft, not the reverse.</p>
<ul>
<li>Anis Cheriet, CEO: EV charging background, power delivery is his domain</li>
<li>Bo Christopher Redfearn, CTO: formerly Apple, hardware at consumer grade reliability</li>
<li>Armin, AI and ML: the autonomy stack</li>
</ul>
<p><b>What we understand that others do not:</b> everyone else brings energy to the field (fuel, solar, batteries). The energy is already there, strung overhead. Nobody else harvests it.</p>
<p><b>Secret sauce:</b> Magline, our induction harvesting payload, validated and integrated with a fielded military power hub.</p>

<h2>Slide 13. The ask</h2>
<p><b>Slidebean rule:</b> transactional, but must show the raise reaches the next fundable milestone. Companies die between rounds when it does not.</p>
<p><b>Headline:</b> $4M to turn a pilot into a fleet.</p>
<ul>
<li>Raising $4M for 24 months of runway</li>
<li>Use of funds: hardware builds and field testing, autonomy stack, core team, operations</li>
<li>Milestones this buys: JIFX demo, real line pilot success, expansion order at our first account, 2 to 3 additional paying customers</li>
<li>Outcome: a Series A raised on signed defense revenue</li>
</ul>
"""


def main():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    with open(HTML_PATH, "w") as f:
        f.write(HTML)

    drive = build("drive", "v3", credentials=creds)
    media = MediaFileUpload(HTML_PATH, mimetype="text/html", resumable=False)
    file = drive.files().create(
        body={
            "name": "Chargebotic Pitch Deck Text (Slidebean method)",
            "mimeType": "application/vnd.google-apps.document",
        },
        media_body=media,
        fields="id,webViewLink",
    ).execute()

    os.remove(HTML_PATH)
    print(f"Doc created: {file['webViewLink']}")


if __name__ == "__main__":
    main()
