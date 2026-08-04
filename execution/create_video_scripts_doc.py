"""
Creates a Google Doc: Anduril's product launch machine, reverse engineered from
their full video catalog, plus the three story films for our own products.

Evidence base (pulled August 4, 2026):
  - Full channel catalog, 61 videos with dates, durations, view counts
  - Frame by frame storyboard extraction on 4 films:
      Thunder: The New Era of Attack Aviation   2:57  F4LOf_eleAM
      Thunder: Autonomous Attack Rotorcraft     0:56  kmPaiqfywd8
      Menace-I: Deployable Data Center          0:48  bSVonflfE0A
      EagleEye: Superpowers For Superheroes     3:06  x9B02pFKpJo
  - Publish timestamps and description copy for 26 launch videos

Uses Drive API upload + conversion (works with drive scope, no Docs API needed).
Run: python3 execution/create_video_scripts_doc.py
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
HTML_PATH = os.path.join(os.path.dirname(__file__), ".video_scripts.html")

HTML = """
<h1>Product Launch Playbook</h1>
<p><i>Anduril's launch machine, reverse engineered from their full catalog of 61 videos and a
frame by frame breakdown of four films. Then applied to Kestrel, Spark E, and the software layer.
Evidence pulled August 4, 2026.</i></p>

<h1>Part 1. How they actually launch a product</h1>

<h2>1.1 The cadence</h2>
<p>Roughly 10 videos a year, one every 5 to 6 weeks. Only about half are products. The other half
keeps the channel warm so a launch never lands on a cold audience.</p>
<p>The channel has 215K subscribers and 112 videos. The first three years of it are employee profile
videos at 5K to 25K views. The cinematic era starts November 2023 with Roadrunner, which did 4M.
Nothing about the product changed. The format did.</p>

<h2>1.2 The catalog, sorted by what it earned</h2>
<table border="1" cellpadding="6">
<tr><th>Video</th><th>Date</th><th>Length</th><th>Views</th><th>Type</th></tr>
<tr><td>YFQ-44A: The Road to First Flight</td><td>2026-02-23</td><td>3:12</td><td>16M</td><td>Milestone documentary</td></tr>
<tr><td>Anduril UK: A New Testbed for Sovereign Defence</td><td>2025-11-18</td><td>0:54</td><td>6.5M</td><td>Country and policy</td></tr>
<tr><td>For The Warfighter</td><td>2025-05-26</td><td>3:22</td><td>5.3M</td><td>Brand, Memorial Day</td></tr>
<tr><td>Thunder: The New Era of Attack Aviation</td><td>2026-07-20</td><td>2:57</td><td>4.0M</td><td>Launch, narrative</td></tr>
<tr><td>Don't Work At Anduril</td><td>2025-02-19</td><td>2:14</td><td>4.0M</td><td>Recruiting</td></tr>
<tr><td>Anduril Unveils Roadrunner and Roadrunner-M</td><td>2023-11-30</td><td>1:54</td><td>4.0M</td><td>Launch</td></tr>
<tr><td>Introducing: Bolt and Bolt-M</td><td>2024-10-09</td><td>2:13</td><td>3.8M</td><td>Launch</td></tr>
<tr><td>Anduril: Fight Unfair</td><td>2026-06-12</td><td>0:31</td><td>3.2M</td><td>Brand</td></tr>
<tr><td>Introducing: Dive-XL</td><td>2024-12-09</td><td>1:06</td><td>3.1M</td><td>Launch</td></tr>
<tr><td>Introducing: Pulsar-L</td><td>2025-04-29</td><td>1:55</td><td>2.3M</td><td>Launch, variant</td></tr>
<tr><td>EagleEye: Superpowers For Superheroes</td><td>2025-10-16</td><td>3:06</td><td>2.2M</td><td>Launch, chaptered</td></tr>
<tr><td>Menace-I: Deployable Data Center</td><td>2026-06-30</td><td>0:48</td><td>2.0M</td><td>Launch, field</td></tr>
<tr><td>Menace: Own the Edge</td><td>2025-05-05</td><td>2:16</td><td>1.9M</td><td>Launch</td></tr>
<tr><td>Command the Sea. Command the World.</td><td>2025-04-08</td><td>1:54</td><td>1.7M</td><td>Launch, category</td></tr>
<tr><td>Win This Cup Car. Literally This Car.</td><td>2026-06-08</td><td>0:30</td><td>1.6M</td><td>NASCAR activation</td></tr>
<tr><td>ArsenalOS: The Digital Backbone of Modern Defense Manufacturing</td><td>2026-06-29</td><td>1:14</td><td>1.3M</td><td>Launch, software</td></tr>
<tr><td>ALTIUS-700M Loitering Munition</td><td>2024-03-14</td><td>1:21</td><td>1.0M</td><td>Launch, variant</td></tr>
<tr><td>Race The Base: The Anduril 250</td><td>2025-08-14</td><td>0:58</td><td>946K</td><td>NASCAR announcement</td></tr>
<tr><td>Introducing: Barracuda-M Family of Cruise Missiles</td><td>2024-09-11</td><td>1:10</td><td>933K</td><td>Launch</td></tr>
<tr><td>Introducing Pulsar: Family of EW Systems</td><td>2024-05-05</td><td>1:42</td><td>923K</td><td>Launch, family</td></tr>
<tr><td>Thunder: Autonomous Attack Rotorcraft for the Deep Fight</td><td>2026-07-20</td><td>0:56</td><td>498K</td><td>Launch, spec</td></tr>
<tr><td>Menace-I Sling Load</td><td>2025-09-09</td><td>1:01</td><td>314K</td><td>Capability proof</td></tr>
<tr><td>Ghost-X: Modular, Multi-Mission sUAS</td><td>2024-09-25</td><td>2:59</td><td>221K</td><td>Launch, spec heavy</td></tr>
<tr><td>The Evolution of Omen</td><td>2025-12-15</td><td>0:42</td><td>152K</td><td>Credibility, history</td></tr>
</table>

<h3>What the numbers say</h3>
<ol>
<li><b>The best performing video they have ever made is not a product reveal.</b> It is a documentary
about getting one aircraft off the ground for the first time. 16M views. The story was the risk of
the attempt, not the specs of the object.</li>
<li><b>Brand and recruiting films outperform most launches.</b> 5.3M, 4.0M, 3.2M. That audience is
already warm when the next product drops.</li>
<li><b>Length does not predict performance.</b> 0:31 did 3.2M. 2:59 did 221K.</li>
<li><b>The spec film always underperforms the hero film by 5 to 8 times</b> and they ship it anyway,
because it is aimed at engineers and program officers, not at reach.</li>
</ol>

<h2>1.3 Launch day mechanics, from the timestamps</h2>
<p>Thunder, July 20, 2026. Two videos, same day, deliberate order:</p>
<ol>
<li>07:32 Pacific, the 56 second spec film. Object only. No story.</li>
<li>10:31 Pacific, the 2:57 narrative film. Doctrine, humans, the fight.</li>
</ol>
<p>Three hours apart. The object is established first, so the story film is never the first thing
a skeptical engineer sees. July 20 was day one of the Farnborough International Airshow.</p>
<p>EagleEye, October 16, 2025, sits in the same week as AUSA. Menace-I and ArsenalOS went out on
consecutive days, June 29 and 30, 2026, paired with a partner announcement.</p>
<p><b>The rule: launch on day one of the show where the buyer already is, and never ship one video alone.</b></p>

<h2>1.4 The four film formats</h2>
<p>They do not have a house style. They have four, and they pick by product type.</p>
<table border="1" cellpadding="6">
<tr><th></th><th>A. Narrative</th><th>B. Spec</th><th>C. Field</th><th>D. Chaptered demo</th></tr>
<tr><td>Example</td><td>Thunder 2:57</td><td>Thunder 0:56</td><td>Menace-I 0:48</td><td>EagleEye 3:06</td></tr>
<tr><td>Look</td><td>Hand drawn animation</td><td>Black room, one green light</td><td>Live action, real dirt</td><td>White cards, in headset POV</td></tr>
<tr><td>Humans</td><td>Faces, name tapes, a family photo</td><td>None</td><td>Hands and backs, no heroes</td><td>The operator is the camera</td></tr>
<tr><td>Type on screen</td><td>Almost none until the end</td><td>Four spec claims</td><td>Five capability cards with numbers</td><td>One chapter title per capability</td></tr>
<tr><td>Use it when</td><td>The product needs a doctrine to exist</td><td>The product must look engineered</td><td>The product works today</td><td>The product is software or worn</td></tr>
<tr><td>Cost</td><td>Very high</td><td>Very low</td><td>Low</td><td>Medium, needs real capture</td></tr>
</table>

<h3>A. Narrative, verified beats (Thunder, 2:57)</h3>
<table border="1" cellpadding="6">
<tr><th>Time</th><th>On screen</th><th>Function</th></tr>
<tr><td>0:00 to 0:14</td><td>Coastline, smoke trails on the horizon, an enemy drone crossing jungle. No product.</td><td>The threat exists before you do.</td></tr>
<tr><td>0:16</td><td>Cut to black</td><td>Act break one</td></tr>
<tr><td>0:20 to 0:26</td><td>Two Apaches, the new aircraft flying beneath them</td><td>Legacy asset first. The new thing enters as escort.</td></tr>
<tr><td>0:28 to 0:36</td><td>Cockpit, green displays, pilot face close up</td><td>The human who pays the price</td></tr>
<tr><td>0:40 to 0:48</td><td>Macro on launch rails, macro on the sensor turret, then a sensor view naming the munition</td><td>Capability as hardware, never as bullets</td></tr>
<tr><td>1:04</td><td>A family photo taped inside the cockpit</td><td>One frame that carries the stakes</td></tr>
<tr><td>1:08 to 1:20</td><td>Planning interface, then the product hero shot</td><td>Software before hardware</td></tr>
<tr><td>1:24 to 1:36</td><td>Launch, fireball, strike card</td><td>The kill, 12 seconds total</td></tr>
<tr><td>1:40 to 1:52</td><td>Mixed formation, battle chaos</td><td>Scale. Never one aircraft.</td></tr>
<tr><td>1:54</td><td>Cut to black</td><td>Act break two</td></tr>
<tr><td>2:00 to 2:20</td><td>Sunset flight line, crew walking, a crew chief with a legible name tape</td><td>Home. Real ranks, no officers.</td></tr>
<tr><td>2:24</td><td>A thumb presses one button on a tablet</td><td>The autonomy claim, made physical</td></tr>
<tr><td>2:32</td><td>Fleet management screen</td><td>One operator to a fleet in two cuts. The business model shot.</td></tr>
<tr><td>2:48</td><td>Wordmark, at 94 percent of runtime</td><td>Name it only once earned</td></tr>
<tr><td>2:52</td><td>Black, logo</td><td>Endcard</td></tr>
</table>
<p><b>No voice over anywhere.</b> There is no caption track on the film. Image and score carry it,
and the written argument lives in the description under the video.</p>

<h3>B. Spec, verified beats (Thunder, 0:56)</h3>
<p>0:00 object emerges from black in a pool of green light. 0:02 name plus one category line.
0:08 macro on the rotor hub with a claim about the powertrain. 0:18 macro on the nose sensor with a
claim about perception. 0:30 payload bay open, with a row of four payload words. 0:44 pull back to
the whole object, loaded. 0:52 black and logo.</p>
<p>Four claims, one per act, each held on screen 6 to 8 seconds so it can be screenshotted.
Macro to wide, never the reverse. The whole object only in the last six seconds.
One dark room, one light, one unit.</p>

<h3>C. Field, verified beats (Menace-I, 0:48)</h3>
<p>Opens and closes on the identical locked off wide, which makes it read as a record and not an ad.
Five capability cards, each a big word pair plus one line of small print carrying the number.
Two soldiers open the box, throw breakers, and walk out. Nobody speaks. Time to operational is
stated as a number, under ten minutes.</p>

<h3>D. Chaptered demo, verified beats (EagleEye, 3:06)</h3>
<p>Inverted aesthetic. White, clinical, calm. A white card names the capability in title case with the
sub features listed in small caps beneath it, then 40 to 50 seconds of uncut real in headset POV
footage proving it. Four chapters: mission planning, lethal connectivity, heightened survivability,
enhanced perception.</p>
<p>Each chapter was then cut out and posted as a standalone Short. Three of those Shorts did 44K to
61K each. <b>One shoot, one long film, four short films.</b> Copy this.</p>

<h2>1.5 The copy formula</h2>
<p>Every launch description is the same five moves, 3 to 5 paragraphs, 1 to 2 sentences each,
ending in a link to a product page at their own domain.</p>
<ol>
<li><b>The world changed.</b> One flat declarative sentence about the new reality.</li>
<li><b>Who is losing because of it.</b> Named people or platforms, not markets.</li>
<li><b>The consequence, stated as a stall.</b> Ground forces cannot advance. Production is frozen in Cold War designs.</li>
<li><b>The need, written as a requirement, not a product.</b> They describe what has to exist before they name what they built.</li>
<li><b>The product in one sentence, then the pairing thesis.</b> Their Thunder line is that the Apache is exposed without it and it is leaderless without the Apache, and the deep fight needs both.</li>
</ol>
<p><b>Note:</b> move 5 is the same 1 plus 1 equals 3 argument Adam Warmoth made to us on June 19.
Steal the sentence shape exactly.</p>

<h3>Numbers appear in the problem, not in the product</h3>
<p>Their strongest openings are a single number that indicts the status quo. Nine days to burn through
the missile stockpile. Multiple days and multiple operators to set up comms, against five minutes and
one operator. Threat response in hours instead of months. The number is always about the pain,
never about the spec sheet.</p>

<h3>Title formula</h3>
<p>Two eras. Until early 2025 it was Introducing, colon, product name. Since then it is
product name, colon, positioning claim. The second form is better because the title carries the
argument even to someone who never clicks.</p>

<h2>1.6 The rest of the launch stack</h2>
<ol>
<li><b>A product page per product</b> at their own domain, linked from every video description.</li>
<li><b>A newsroom post</b> published the same day, linked when the story is a partnership or a contract.</li>
<li><b>Earned long form.</b> For Fury they pointed at an outside publication's feature story rather than writing their own. Third party narrative carries credibility their own blog cannot.</li>
<li><b>Founder and executive distribution</b> on X on the same morning.</li>
<li><b>Trade show timing</b> on day one, so press already in the building has something to film.</li>
<li><b>Credibility films between launches.</b> A 42 second film whose only job is to say the product is not a concept, that it first flew in 2020, and that there are 30 prototypes and hundreds of hours.</li>
</ol>

<h1>Part 2. Our launch, mapped onto that machine</h1>

<h2>2.1 What we can and cannot copy</h2>
<table border="1" cellpadding="6">
<tr><th>They have</th><th>We have</th><th>So we</th></tr>
<tr><td>A production line in Ohio</td><td>TRL 4 and a paid pilot</td><td>Lead with the field film, not the animation</td></tr>
<tr><td>16M views on a first flight documentary</td><td>A first harvest on a real line, still unfilmed</td><td>Film the attempt, including what fails</td></tr>
<tr><td>Farnborough and AUSA</td><td>JIFX 26-4, August 10 to 14</td><td>Treat JIFX as the shoot, not the launch</td></tr>
<tr><td>A brand audience kept warm all year</td><td>A founder account with a real voice</td><td>Ship the credibility short first, months before the hero film</td></tr>
</table>
<p><b>The single most important adaptation:</b> their 16M view film is about the first time a thing flew.
Ours is the first time a drone perched on a live conductor and powered a ground system.
That footage does not exist yet, and it can only be captured once. Film JIFX like a documentary,
not like a demo.</p>

<h2>2.2 Launch sequence for Kestrel</h2>
<ol>
<li><b>Now to August 9.</b> Product page per product, live before any video ships.</li>
<li><b>August 10 to 14, JIFX.</b> Capture only. Nothing published. Full capture list in Part 4.</li>
<li><b>Roughly two weeks after.</b> Field film, 50 seconds, and the spec film, same day, spec film three hours earlier. This is the launch.</li>
<li><b>Same day.</b> Newsroom post, product page update, founder post, and the pilot partner co posting. Their sales team gets the footage, which is the co marketing we already agreed to.</li>
<li><b>Four to six weeks later.</b> The milestone documentary, 3 minutes, the story of the first harvest on a real line including the failures. This is the 16M view format, and it is the one that raises the round.</li>
<li><b>Only after a multi unit order.</b> The animated narrative film. Anduril earned that format with a factory. We earn it with a signed fleet order.</li>
</ol>

<h1>Part 3. The three stories</h1>

<h2>Story 1. Kestrel. Narrative film, 2:45. Working title: Silent Watch</h2>
<p><b>Format A. Audience:</b> defense primes, program offices, defense investors.
<b>Source:</b> the use case Adam Warmoth described to us on June 19.</p>

<h3>The written argument, five moves</h3>
<ol>
<li>Power at the edge still arrives by truck, and the truck is now the easiest target on the battlefield.</li>
<li>The crews on fuel resupply pay for it. Roughly one casualty for every 24 fuel convoys in Iraq and Afghanistan.</li>
<li>So a robotic vehicle 10 km forward has to keep its engine running to keep its sensors alive. A running engine is heat and noise. Heat and noise is a signature. A signature is a target.</li>
<li>We need power at the edge that arrives without a convoy and runs without a signature.</li>
<li>Kestrel perches on a power line, harvests, and sends energy down a tether to the machine. A ground system without Kestrel is waiting on fuel. Kestrel without a ground system has nowhere to put the power. The deep fight requires both.</li>
</ol>

<h3>Shot list</h3>
<table border="1" cellpadding="6">
<tr><th>Time</th><th>Shot</th><th>Sound and type</th></tr>
<tr><td>0:00 to 0:08</td><td>Dusk. A fuel convoy on a dirt road seen from high above. Dust plume, long and slow. No product.</td><td>Low tone. No type.</td></tr>
<tr><td>0:08 to 0:14</td><td>Top down on a small enemy quadcopter crossing above the same road. It holds over the convoy.</td><td>Rotor whine enters.</td></tr>
<tr><td>0:16</td><td>Black.</td><td>Silence. Act break one.</td></tr>
<tr><td>0:18 to 0:28</td><td>Another valley, first light. A robotic combat vehicle grinds forward, engine running, exhaust shimmer. Behind it a line of transmission towers runs down the valley. The towers stay in frame for the rest of the film.</td><td>Engine, heavy.</td></tr>
<tr><td>0:28 to 0:38</td><td>Company command post 10 km back. Green screens. A young operator watching the vehicle feed. Close up on their face.</td><td>Radio chatter, low.</td></tr>
<tr><td>0:40 to 0:46</td><td>The vehicle stops. Engine shuts down. Exhaust shimmer dies. Thermal view of the engine block going dark.</td><td>Engine dies into near silence. Best sound cue in the film.</td></tr>
<tr><td>0:48 to 0:54</td><td>Battery gauge dropping. Sensor feeds shutting down one at a time.</td><td>Small print: SENSORS ON BATTERY. 6 HOURS.</td></tr>
<tr><td>0:56 to 1:06</td><td>Kestrel lifts off the back deck of the vehicle. Low, quiet, deliberate. Climbs toward the conductor overhead.</td><td>Product appears at 33 percent. No type.</td></tr>
<tr><td>1:08 to 1:16</td><td>Macro: the harvester jaw opening. The conductor filling frame. Contact. Coil energising, one indicator going green.</td><td>Small print: MAGLINE INDUCTION HARVESTER.</td></tr>
<tr><td>1:18 to 1:26</td><td>The tether pays out downward. Follow it to the connector meeting the ground hub.</td><td>Small print: 24 VDC TO THE GROUND HUB.</td></tr>
<tr><td>1:28 to 1:36</td><td>Screens come back up in the same order they died. Thermal view: the vehicle is still dark.</td><td>Score lifts. Small print: ENGINE OFF. SENSORS UP.</td></tr>
<tr><td>1:38 to 1:48</td><td>Sun crosses. Rain. Night. The vehicle has not moved and has not warmed. Kestrel still on the line.</td><td>Small print: DAY 4.</td></tr>
<tr><td>1:50 to 2:00</td><td>Night. An acoustic sensor picks up an incoming drone. The alert travels: sensor, hub, satellite terminal, command post. The operator's face lights from the screen.</td><td>Small print: DETECTED.</td></tr>
<tr><td>2:02 to 2:06</td><td>Reverse angle. The enemy drone passes over the valley and sees nothing. The vehicle is cold and dark.</td><td>Rotor whine receding. This is the win, and nothing explodes.</td></tr>
<tr><td>2:08</td><td>Black.</td><td>Act break two.</td></tr>
<tr><td>2:10 to 2:24</td><td>Dawn at a forward base. Two soldiers lift a Kestrel out of a case. No crane, no crew. Close up on one of them, name tape legible. They set it on the deck of the next vehicle.</td><td>Ambient only.</td></tr>
<tr><td>2:26 to 2:30</td><td>Tablet in gloved hands. One button pressed: ATTACH. Cut to the aircraft lifting.</td><td>One tone.</td></tr>
<tr><td>2:32 to 2:36</td><td>Fleet screen. Units on lines across a region, each with power delivered and hours on station.</td><td>Small print: 34 UNITS ON STATION.</td></tr>
<tr><td>2:38 to 2:42</td><td>Widest frame in the film, held. Transmission towers to the horizon at sunrise, a Kestrel perched on one, tether down to a vehicle you can barely see.</td><td>Score resolves.</td></tr>
<tr><td>2:43</td><td>KESTREL wordmark.</td><td></td></tr>
<tr><td>2:45</td><td>Black. Company logo.</td><td></td></tr>
</table>
<p><b>Claim discipline.</b> The ATTACH button at 2:26 is the only autonomy claim in the film and it is
a roadmap claim. Kestrel 1 is piloted. If this film ships after Kestrel 2 semi autonomous find and
attach is real, it is honest. Do not add an autonomy caption anywhere else.</p>

<h2>Story 2. Spark E. Field film, 0:50. Working title: 17,000 Kilometers</h2>
<p><b>Format C. Audience:</b> utilities, grid operators, inspection providers. Terna and Cupertino
specifically. No defense framing in this film at all.</p>

<h3>The written argument, five moves</h3>
<ol>
<li>Grids got longer and older, and inspection demand outran the fleet that can fly it.</li>
<li>The operator with 17,000 km of network to cover pays for it, with a drone that lands every 30 minutes.</li>
<li>Range, not sensors, sets the cost per kilometre. The crew spends the day driving to the next launch point.</li>
<li>What is needed is not a bigger battery. It is a place to charge that is already there, every span, for the entire length of the line.</li>
<li>Spark E lands on the conductor it is inspecting and charges from it. The line is the runway and the fuel.</li>
</ol>

<h3>Shot list</h3>
<table border="1" cellpadding="6">
<tr><th>Time</th><th>Shot</th><th>On screen type</th></tr>
<tr><td>0:00 to 0:03</td><td>Locked off wide. Real terrain, a transmission line running out of frame. One pickup, one operator, one case on the tailgate. The film will close on this exact frame.</td><td>SPARK E, SELF CHARGING INSPECTION DRONE</td></tr>
<tr><td>0:04 to 0:07</td><td>Low angle, drone lifting off the tailgate.</td><td>ONE OPERATOR, small print: NO CREW, NO GENERATOR, NO LAUNCH SITE</td></tr>
<tr><td>0:08 to 0:13</td><td>Flying the line. Tower, conductor, insulator sliding past. Payload camera view cut in once.</td><td>INSPECT THE LINE, small print: THERMAL, VISUAL, LIDAR</td></tr>
<tr><td>0:14 to 0:20</td><td>Battery at 20 percent. Then the move that sells the product: the drone slows, rises, and settles onto the conductor. Hold the contact in macro.</td><td>LAND ON THE LINE, small print: BATTERY AT 20 PERCENT</td></tr>
<tr><td>0:21 to 0:27</td><td>Macro: harvester closed on the conductor, indicator going green, charge percentage climbing on a real screen.</td><td>CHARGE FROM THE LINE, small print: 20 TO 90 PERCENT IN X MINUTES</td></tr>
<tr><td>0:28 to 0:33</td><td>The operator sitting on the tailgate watching a tablet. Not working. Waiting. Real face, no acting.</td><td>small print: THE OPERATOR DOES NOT DRIVE TO THE NEXT LAUNCH POINT</td></tr>
<tr><td>0:34 to 0:39</td><td>Drone releases and continues down the line. Follow it until it is small.</td><td>KEEP GOING, small print: X KM PER DAY INSTEAD OF Y</td></tr>
<tr><td>0:40 to 0:45</td><td>Aerial pull up and back. The line runs to the horizon with the drone a dot on it.</td><td>THE LINE IS THE RUNWAY, small print: 17,000 KM OF NETWORK, ONE OPERATOR</td></tr>
<tr><td>0:46 to 0:48</td><td>Return to the exact opening wide. Operator closes the tailgate and drives out.</td><td>none</td></tr>
<tr><td>0:49</td><td>Black. Company logo.</td><td></td></tr>
</table>
<p><b>Numbers to fill before this is cut:</b> charge time from 20 to 90 percent, kilometres per day with
and without line charging, and whose 17,000 km it is. That figure came from Cupertino, so either clear
it with Santiago Bua or write it as network scale rather than as a customer number.</p>

<h2>Story 3. Software layer. Spec film, 0:52. Working title: What The Line Tells Us</h2>
<p><b>Format B, with format D structure for the screen sections. Audience:</b> utilities, grid CVCs,
and anyone who thinks we are a drone company. This film exists to prove we are not.</p>

<h3>The written argument, five moves</h3>
<ol>
<li>Every time we harvest, we make contact with the conductor and we read it.</li>
<li>Nobody else gets that data, because nobody else touches a live line at scale.</li>
<li>So a fleet flying for range extension is also a continuous line health survey.</li>
<li>And every watt taken off the line is metered, which is how the utility gets paid instead of getting nervous.</li>
<li>The hardware earns the contract. The software is why the contract renews.</li>
</ol>

<h3>Shot list</h3>
<table border="1" cellpadding="6">
<tr><th>Time</th><th>Frame</th><th>On screen type</th></tr>
<tr><td>0:00 to 0:04</td><td>Black. The harvester rises into a single pool of cold light, closed on a short section of conductor. Static wide, held.</td><td>Product name, one line under it</td></tr>
<tr><td>0:05 to 0:12</td><td>Macro: contact surface, coil, conductor. Slow drift. Real hardware, dark room, one light.</td><td>CONTACT WITH THE LIVE CONDUCTOR</td></tr>
<tr><td>0:13 to 0:22</td><td>Screen capture on black: the stack finding a line and locking on. Keep the raw interface, do not beautify it.</td><td>FIND, FLY, ATTACH, HARVEST</td></tr>
<tr><td>0:23 to 0:32</td><td>Screen capture: line health output. Thermal signature per span, anomalies flagged along a route.</td><td>LINE HEALTH REPORTING, small print: EVERY HARVEST IS A MEASUREMENT</td></tr>
<tr><td>0:33 to 0:42</td><td>Screen capture: metering view. Watt hours drawn per unit, per line, per month, with a settlement total.</td><td>METERED ENERGY, small print: THE UTILITY GETS PAID FOR EVERY WATT HOUR</td></tr>
<tr><td>0:43 to 0:48</td><td>Back to the dark room. Pull out from macro to the full harvester, lit, still. A fleet count appears beside it.</td><td>ONE FLEET, ONE LEDGER</td></tr>
<tr><td>0:49 to 0:52</td><td>Black.</td><td>Company logo</td></tr>
</table>

<h1>Part 4. Production</h1>

<h2>4.1 JIFX is the only shoot window that matters</h2>
<p>Camp Roberts, August 10 to 14, is the one date on the calendar where real hardware, a line, and a
customer system are in the same field. Everything real in all three films is captured that week or
waits months.</p>

<h3>Capture list</h3>
<ol>
<li>Locked off wide of the site, identical frame at the start and end of every day. This is the field film opening and closing shot.</li>
<li>Macro on the harvester jaw opening and closing. Tripod, long lens, at least 10 takes.</li>
<li>Macro on contact with the conductor and the indicator going green. The single most valuable frame we will own.</li>
<li>The tether paying out, top down and bottom up.</li>
<li>Hands. Two people lifting the unit out of the case, throwing latches, setting it on a deck. Faces optional, hands are enough.</li>
<li>Screen capture of live telemetry during the harvest, with watts and elapsed time legible.</li>
<li>Delivery into the ground hub, wide enough that both boxes are in one frame. The 1 plus 1 equals 3 shot.</li>
<li>One face in real light at the end of a working day. Do not stage it.</li>
<li>Ten minutes of the unit on the line after dark, no crew in frame.</li>
<li>Dark room spec pass after hours. One light, black backdrop, unit on a stand, 20 minutes of slow macro drift. That is Story 3 and every future spec film, for the cost of 20 minutes.</li>
<li><b>The documentary layer.</b> The briefing, the arguments, the failed attempt, the repair, the retry. This is the 16M view format and it only exists if someone is filming when it is not going well.</li>
</ol>

<h2>4.2 Order of production</h2>
<ol>
<li><b>Field film first.</b> Cheapest, fastest, all live, and it is the one that closes utilities. Cut within two weeks of the shoot.</li>
<li><b>Spec film second.</b> Same week's footage, plus screen capture we already own.</li>
<li><b>Milestone documentary third.</b> Four to six weeks later. This is the fundraising asset.</li>
<li><b>Animated narrative last</b>, once a multi unit order is signed.</li>
</ol>

<h2>4.3 Rules we adopt</h2>
<ol>
<li>No voice over in any film. Type carries the message.</li>
<li>No em dashes, no exclamation marks, no adjectives in on screen type. Nouns and numbers.</li>
<li>Every capability card carries one number in small print.</li>
<li>The number in the opening is about the pain, never about the spec sheet.</li>
<li>The product name appears in the last 10 percent of runtime, never in the first frame.</li>
<li>The last frame before the logo is the widest frame in the film.</li>
<li>One real human face minimum per film. Not a model.</li>
<li>Never ship one video alone. Spec film first, hero film three hours later, same day.</li>
<li>Launch on day one of an event where the buyer is already standing.</li>
<li>Every claim in every frame has to survive a customer engineer watching it twice.</li>
</ol>

<h1>Part 5. Three launch scenarios</h1>
<p>Anchors are real: AUSA Annual Meeting, October 12 to 14, 2026, Washington DC, about 44,000
attendees. DistribuTECH International, March 2 to 4, 2027, Atlanta.</p>

<table border="1" cellpadding="6">
<tr><th></th><th>1. Proof Drop</th><th>2. The Pairing</th><th>3. Two Markets</th></tr>
<tr><td>Assets</td><td>2</td><td>6</td><td>9</td></tr>
<tr><td>Launch date</td><td>Aug 27, 2026</td><td>Oct 12, 2026 at AUSA</td><td>Oct 12, 2026 and Mar 2, 2027</td></tr>
<tr><td>Crew at JIFX</td><td>2, in house</td><td>3, hired DP</td><td>3, plus a second shoot on a real line</td></tr>
<tr><td>Budget</td><td>$3K to $6K</td><td>$25K to $40K</td><td>$55K to $85K, or $135K to $285K with animation</td></tr>
<tr><td>Expected views</td><td>2K to 8K</td><td>15K to 60K</td><td>100K to 400K over 7 months</td></tr>
<tr><td>Main risk</td><td>A weak harvest leaves no film at all</td><td>Holding footage 24 days invites a leak</td><td>Six figures of animation before an order justifies it</td></tr>
</table>
<p><b>Recommendation: Scenario 2.</b> Scenario 1 undersells a moment that happens once. Scenario 3
commits six figures to animation before there is an order behind it. Scenario 2 costs about $30K,
uses a room of 44,000 people we are already entitled to walk into, and produces the documentary that
raises the round.</p>
<p><b>Check before August 10:</b> aerial B roll at Camp Roberts. JIFX bars Chinese components, so a
DJI airframe for camera work is likely a problem. Plan a long lens from the ground or our own airframe.</p>

<h1>Part 6. Launch kit: Chargebotic Drone Supercharger</h1>
<p><i>Product 1, the line harvesting charger, previously called Kestrel internally.
Scenario 2 mechanics. Launch day October 12, 2026, day one of AUSA.</i></p>

<h2>6.1 Naming and title</h2>
<p>Full product name in copy and on the product page: <b>Chargebotic Drone Supercharger</b>.
On screen wordmark, because 30 characters cannot be read in a 2 second card:
<b>SUPERCHARGER</b>. Video titles follow their post-2025 formula, product name then positioning claim:</p>
<ol>
<li>Chargebotic Drone Supercharger: Power at the Edge Without a Convoy (hero, field film)</li>
<li>Chargebotic Drone Supercharger: Harvesting Energy From the Grid You Already Fly Over (spec film)</li>
<li>First Harvest (documentary)</li>
</ol>

<h2>6.2 The launch copy, five moves</h2>
<p>This is the video description, the newsroom post's opening, and the product page's top section.
Same text, three places.</p>
<ol>
<li>Power at the edge still arrives by truck, and the truck is now the easiest target on the battlefield.</li>
<li>The crews on fuel resupply pay for it. Roughly one casualty for every 24 fuel convoys in Iraq and Afghanistan.</li>
<li>So a forward system keeps its engine running to keep its sensors alive. A running engine is heat and noise. Heat and noise is a signature. A signature is a target.</li>
<li>What is needed is not a better generator or a bigger battery. It is a way to take power from the grid that already crosses every environment we operate in.</li>
<li>The Chargebotic Drone Supercharger perches on a power line, harvests energy, and sends it down a tether to a drone battery or straight into a ground system. A ground system without it is waiting on fuel. It without a ground system has nowhere to put the power. The deep fight requires both.</li>
</ol>

<h2>6.3 Assets and publish choreography</h2>
<table border="1" cellpadding="6">
<tr><th>Time</th><th>Asset</th><th>Length</th><th>Channel</th></tr>
<tr><td>Oct 12, 07:30 PT</td><td>Spec film</td><td>0:52</td><td>YouTube, product page</td></tr>
<tr><td>Oct 12, 07:30 PT</td><td>Newsroom post and product page go live</td><td></td><td>chargebotic.com</td></tr>
<tr><td>Oct 12, 10:30 PT</td><td>Field film, the hero</td><td>0:50</td><td>YouTube, LinkedIn, X</td></tr>
<tr><td>Oct 12, 10:35 PT</td><td>Founder post</td><td></td><td>X</td></tr>
<tr><td>Oct 12, 12:00 PT</td><td>Pilot partner co post</td><td></td><td>Their channels</td></tr>
<tr><td>Oct 14</td><td>Short 1, the contact frame</td><td>0:15</td><td>Shorts, Reels, TikTok</td></tr>
<tr><td>Oct 16</td><td>Short 2, engine off and sensors up</td><td>0:15</td><td>Same</td></tr>
<tr><td>Oct 19</td><td>Short 3, two people and a case</td><td>0:15</td><td>Same</td></tr>
<tr><td>Oct 29</td><td>First Harvest documentary</td><td>3:00</td><td>YouTube, sent directly to investors</td></tr>
</table>

<h2>6.4 Field film, the hero. 0:50, 23 shots</h2>
<table border="1" cellpadding="6">
<tr><th>Time</th><th>Shot</th><th>On screen type</th></tr>
<tr><td>0:00 to 0:03</td><td>Locked off wide. Real terrain, a line running out of frame, one vehicle, one case on the tailgate. The film closes on this exact frame.</td><td>CHARGEBOTIC DRONE SUPERCHARGER</td></tr>
<tr><td>0:04 to 0:08</td><td>Two people lift the unit out of the case and set it down. Hands, latches, effort. No crane.</td><td>TWO PEOPLE, ONE CASE, small print: NO CREW, NO GENERATOR, NO FUEL</td></tr>
<tr><td>0:09 to 0:14</td><td>Launch. Low, deliberate. The unit climbs toward the conductor overhead.</td><td>FLY TO THE LINE</td></tr>
<tr><td>0:15 to 0:22</td><td>The money sequence. Macro: the harvester jaw opening, the conductor filling frame, contact, one indicator going green.</td><td>ATTACH TO THE LINE, small print: 50 TO 150 W LINES</td></tr>
<tr><td>0:23 to 0:29</td><td>Tether paying out downward. Follow it to the connector meeting the ground hub. Wide enough that both boxes are in one frame.</td><td>HARVEST, small print: [WATTS MEASURED AT JIFX] CONTINUOUS</td></tr>
<tr><td>0:30 to 0:36</td><td>Real telemetry on a real screen. Watts and elapsed time legible, nobody pointing at it.</td><td>METERED, small print: [MINUTES MEASURED AT JIFX] ON STATION</td></tr>
<tr><td>0:37 to 0:43</td><td>The ground system running on harvested power. Then one face in real light at the end of a working day. Not staged.</td><td>POWER DELIVERED, small print: ENGINE OFF, SENSORS UP</td></tr>
<tr><td>0:44 to 0:48</td><td>Return to the exact opening wide, now with the unit on the line and the tether down. Widest frame in the film, held.</td><td>THE GRID IS THE FUEL DEPOT</td></tr>
<tr><td>0:49 to 0:50</td><td>Black.</td><td>SUPERCHARGER wordmark, then logo</td></tr>
</table>
<p><b>Every bracketed number is filled from the demo, not written in advance.</b> If the harvest lands
at 40 W, the card reads 40 W. Minimum pilot success is 40 W continuous for 10 minutes on a real line.
About 70 W powers a Starlink terminal, which is the comparison a program officer already understands,
so use it in the description rather than on the card.</p>

<h2>6.5 Spec film. 0:52, 10 shots</h2>
<table border="1" cellpadding="6">
<tr><th>Time</th><th>Frame</th><th>On screen type</th></tr>
<tr><td>0:00 to 0:04</td><td>The unit rises out of black into a single pool of cold light, closed on a short section of conductor. Static wide, held.</td><td>none</td></tr>
<tr><td>0:05 to 0:12</td><td>Same wide, held.</td><td>CHARGEBOTIC DRONE SUPERCHARGER, under it: AIRBORNE ENERGY HARVESTING SYSTEM</td></tr>
<tr><td>0:13 to 0:21</td><td>Macro: the harvester jaw, the coil, the contact surface. Slow drift.</td><td>INDUCTION HARVESTING PAYLOAD</td></tr>
<tr><td>0:22 to 0:30</td><td>Macro: the tether spool and the connector.</td><td>TETHERED POWER DELIVERY, small print: 24 VDC OR 110 TO 240 VAC</td></tr>
<tr><td>0:31 to 0:39</td><td>Macro: the airframe attach points and the payload mount.</td><td>RETROFITS TO MULTIPLE AIRFRAMES</td></tr>
<tr><td>0:40 to 0:46</td><td>Screen capture on black, raw interface, no beautifying: find the line, fly, attach, harvest.</td><td>FIND, FLY, ATTACH, HARVEST</td></tr>
<tr><td>0:47 to 0:50</td><td>Pull back to the whole unit, lit, still.</td><td>none</td></tr>
<tr><td>0:51 to 0:52</td><td>Black.</td><td>Logo</td></tr>
</table>
<p><b>Claim discipline.</b> The interface section shows the stack, not an autonomy claim. Nothing in
either film says autonomous. At JIFX the aircraft is piloted, and any card that implies otherwise dies
the first time a customer engineer asks who was flying.</p>

<h2>6.6 First Harvest. Documentary, 3:00</h2>
<p>Different rules on purpose: handheld, available light, lav audio, average shot 4 seconds.</p>
<ol>
<li>0:00 to 0:25. The problem, stated by a person on camera in one take. No graphics.</li>
<li>0:25 to 0:55. The build. Benches, parts, the payload coming together. Dates on screen.</li>
<li>0:55 to 1:20. Arrival at Camp Roberts. The line. The briefing. Weather.</li>
<li>1:20 to 1:50. <b>The failure.</b> The attempt that did not work, on camera, with the audio of the moment it went wrong. Only music cue enters here. This section is why the film exists.</li>
<li>1:50 to 2:20. The fix. Hands, tools, an argument, a decision.</li>
<li>2:20 to 2:45. The harvest that worked. Real telemetry, real reaction, no slow motion.</li>
<li>2:45 to 3:00. What it means, one sentence from the CEO, then the widest frame and the logo.</li>
</ol>
<p>Anduril's highest performing film ever, at 16M views, is exactly this structure applied to a first
flight. The unusual move is admitting the road was not straight.</p>

<h2>6.7 Style specification</h2>
<table border="1" cellpadding="6">
<tr><th></th><th>Field film</th><th>Spec film</th><th>Documentary</th></tr>
<tr><td>Ratio and rate</td><td>2.39:1, 24 fps</td><td>2.39:1, 24 fps</td><td>2.39:1, 24 fps</td></tr>
<tr><td>Capture</td><td>6K to 4K, one LUT</td><td>6K to 4K, full grade</td><td>4K, minimal grade</td></tr>
<tr><td>Light</td><td>Natural only</td><td>One LED panel, green gel, 45 degrees behind</td><td>Available</td></tr>
<tr><td>Lenses</td><td>24 to 70, 100 to 400, 90 macro</td><td>100 macro at f/4, slider at 2mm per second</td><td>24 to 70 handheld</td></tr>
<tr><td>Average shot</td><td>2.2s</td><td>5.0s</td><td>4.0s</td></tr>
<tr><td>Type</td><td>One grotesque, two weights, all caps cards held 4 to 6s, small print at 30 percent size, 3 percent margin</td><td>Same, four claims held 6 to 8s</td><td>Dates and names only</td></tr>
<tr><td>Sound</td><td>Design only, no music for the first 8s</td><td>Drone score at 60 bpm</td><td>One cue, entering at 1:20</td></tr>
</table>

<h2>6.8 Budget and calendar</h2>
<table border="1" cellpadding="6">
<tr><th>Line</th><th>Cost</th></tr>
<tr><td>DP, 5 days at $850</td><td>$4,250</td></tr>
<tr><td>Camera assistant, 5 days at $450</td><td>$2,250</td></tr>
<tr><td>Gear package, 5 days</td><td>$2,500</td></tr>
<tr><td>Editor, 8 days</td><td>$4,800</td></tr>
<tr><td>Sound design and original score</td><td>$3,500 to $6,000</td></tr>
<tr><td>Motion and type design</td><td>$3,000</td></tr>
<tr><td>Color</td><td>$1,200</td></tr>
<tr><td>Contingency, 15 percent</td><td>$3,200 to $3,600</td></tr>
<tr><td><b>Total</b></td><td><b>$25,000 to $28,000</b></td></tr>
</table>
<table border="1" cellpadding="6">
<tr><th>Date</th><th>Milestone</th></tr>
<tr><td>Aug 6</td><td>DP booked, shot list printed, aerial B roll question resolved</td></tr>
<tr><td>Aug 10 to 14</td><td>JIFX. Capture only. Nothing published, including on X.</td></tr>
<tr><td>Aug 24</td><td>Numbers confirmed from telemetry, cards written with real values</td></tr>
<tr><td>Sep 18</td><td>Field film and spec film locked</td></tr>
<tr><td>Sep 25</td><td>Product page and newsroom post ready, held</td></tr>
<tr><td>Oct 12</td><td>Launch, AUSA day one</td></tr>
<tr><td>Oct 29</td><td>Documentary published</td></tr>
</table>

<h2>6.9 Product page, top section</h2>
<p><b>Headline:</b> Power at the edge, without a convoy.<br>
<b>Subhead:</b> The Chargebotic Drone Supercharger perches on a power line, harvests energy, and delivers it down a tether to a drone battery or a ground system.<br>
<b>Four spec claims, matching the spec film:</b> induction harvesting payload. Tethered power delivery, 24 VDC or 110 to 240 VAC. Retrofits to multiple airframes. Find, fly, attach, harvest.<br>
<b>Proof line:</b> demonstrated at JIFX 26-4, Camp Roberts, August 2026, delivering [X] watts continuous for [Y] minutes into a fielded battlefield power hub.</p>

<h2>6.10 Founder post, launch morning</h2>
<p>Four lines, no thread, video attached, posted at 10:35 Pacific:</p>
<p><i>Power at the edge still arrives by truck.<br>
In August we perched a drone on a live power line at Camp Roberts and ran a ground system off it.<br>
[X] watts, [Y] minutes, engine off the whole time.<br>
Chargebotic Drone Supercharger. Here is the film.</i></p>
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
            "name": "Product Launch Playbook (Anduril reverse engineered) + 3 Story Films",
            "mimeType": "application/vnd.google-apps.document",
        },
        media_body=media,
        fields="id,webViewLink",
    ).execute()

    os.remove(HTML_PATH)
    print(f"Doc created: {file['webViewLink']}")


if __name__ == "__main__":
    main()
