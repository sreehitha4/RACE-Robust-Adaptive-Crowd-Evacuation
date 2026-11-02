"""Generates a plain-English, deeply understandable explanation of the entire project
and all its components as a Microsoft Word .doc file.
"""

import os

def generate_doc() -> str:
    return """<html xmlns:o='urn:schemas-microsoft-com:office:office'
xmlns:w='urn:schemas-microsoft-com:office:word'
xmlns='http://www.w3.org/TR/REC-html40'>
<head>
<meta charset='utf-8'>
<title>Complete Project Explanation in Simple Terms</title>
<!--[if gte mso 9]>
<xml>
<w:WordDocument>
  <w:View>Print</w:View>
  <w:Zoom>100</w:Zoom>
</w:WordDocument>
</xml>
<![endif]-->
<style>
  @page {
    size: 8.5in 11.0in;
    margin: 1.0in 1.0in 1.0in 1.0in;
  }
  body {
    font-family: 'Calibri', 'Segoe UI', Arial, sans-serif;
    font-size: 11.5pt;
    line-height: 1.6;
    color: #222222;
  }
  h1 {
    color: #1a365d;
    font-size: 24pt;
    border-bottom: 2pt solid #2b6cb0;
    padding-bottom: 6pt;
    margin-top: 10pt;
    margin-bottom: 12pt;
  }
  h2 {
    color: #2b6cb0;
    font-size: 16pt;
    margin-top: 22pt;
    margin-bottom: 8pt;
    border-bottom: 1pt solid #e2e8f0;
    padding-bottom: 3pt;
  }
  h3 {
    color: #2d3748;
    font-size: 13pt;
    margin-top: 14pt;
    margin-bottom: 6pt;
  }
  p {
    margin-top: 0;
    margin-bottom: 10pt;
    text-align: justify;
  }
  ul, ol {
    margin-top: 0;
    margin-bottom: 12pt;
    padding-left: 20pt;
  }
  li {
    margin-bottom: 6pt;
  }
  .highlight-box {
    background-color: #ebf8ff;
    border-left: 5pt solid #3182ce;
    padding: 12pt 16pt;
    margin: 14pt 0;
    border-radius: 0 6pt 6pt 0;
  }
  .highlight-box strong {
    color: #2b6cb0;
  }
  .example-box {
    background-color: #f7fafc;
    border: 1pt solid #cbd5e0;
    border-left: 5pt solid #48bb78;
    padding: 12pt 16pt;
    margin: 14pt 0;
    border-radius: 0 6pt 6pt 0;
  }
  .example-box strong {
    color: #276749;
  }
  .term-badge {
    background-color: #edf2f7;
    color: #2d3748;
    padding: 2pt 6pt;
    border-radius: 4pt;
    font-family: Consolas, monospace;
    font-size: 10.5pt;
    font-weight: bold;
    border: 1pt solid #cbd5e0;
  }
  table {
    border-collapse: collapse;
    width: 100%;
    margin: 14pt 0;
    font-size: 10.5pt;
  }
  th {
    background-color: #2b6cb0;
    color: white;
    padding: 8pt 10pt;
    text-align: left;
    border: 1pt solid #2b6cb0;
  }
  td {
    border: 1pt solid #e2e8f0;
    padding: 7pt 10pt;
    vertical-align: top;
  }
  tr:nth-child(even) {
    background-color: #f7fafc;
  }
  hr {
    border: none;
    border-top: 1pt solid #e2e8f0;
    margin: 20pt 0;
  }
</style>
</head>
<body>

<h1>How Everything in This Project Works (Explained in Simple Terms)</h1>

<p>
This document explains our entire <strong>Crowd Evacuation Simulation System</strong> in straightforward, plain English. 
There is no unnecessary math jargon here. By reading this, you will completely understand what the project does, how every piece of code works, why we built it this way, and what is happening on your screen.
</p>

<hr/>

<h2>1. The Big Picture: What Did We Actually Build?</h2>

<p>
Imagine you are inside a large university campus center or an airport terminal with hundreds of people. Suddenly, a fire alarm rings! 
What happens?
</p>
<ul>
  <li>People don't teleport or jump across squares like chess pieces. They walk, run, push, steer around pillars, and try to find the nearest exit door.</li>
  <li>If 50 people all try to squeeze through the same small door at once, a dangerous bottleneck forms. People get crushed and trapped, even if another exit door 10 meters away is completely empty!</li>
  <li>Smart people who are still walking in the back notice the giant crowd jam ahead, turn around, and run toward the empty exit instead.</li>
</ul>

<div class='highlight-box'>
  <strong>Our Project in 1 Sentence:</strong><br/>
  We built a real-time computer simulation using Python and Pygame that models how realistic crowds move through a building, find exits using pathfinding, steer around obstacles, and automatically balance themselves across multiple exits so people don't get crushed in door jams.
</div>

<hr/>

<h2>2. How the People Move: The Movement Physics Engine</h2>

<p>
To make people walk realistically on screen, we had to choose how their movement is calculated.
</p>

<h3>Why didn't we just use a discrete grid?</h3>
<p>
In basic student projects, people are represented as dots locked inside grid squares. Each second, a dot jumps 1 tile up or 1 tile left. 
This looks completely fake because real humans have momentum, smooth turns, and personal space.
</p>

<h3>How our Continuous Physics works: The "Social Force Model"</h3>
<p>
Instead of a simple grid, our people exist in continuous 2D space. That means a person's position is a real number like <span class='term-badge'>(14.37, 8.92)</span>, not just an integer square.
</p>
<p>
We used an algorithm created by a famous physicist named Dirk Helbing called the <strong>Social Force Model</strong>. You can think of it as <strong>invisible magnetic forces</strong> acting on every person:
</p>

<ol>
  <li><strong>The Goal Force (Drive to Exit):</strong>
    Every person has a desired walking speed (e.g., 1.2 m/s when calm, 1.8 m/s during evacuation, 2.6 m/s when panicked). A force constantly pulls them toward their next navigation step.
  </li>
  <li><strong>The Personal Space Force (Pushing other people away):</strong>
    Humans naturally hate bumping into strangers. If two people walk too close to each other, an invisible repulsive force pushes them gently apart. If they actually touch, an elastic body force pushes back harder so they don't overlap.
  </li>
  <li><strong>The Wall &amp; Obstacle Repulsion:</strong>
    When a person gets close to a wall, pillar, bench, or desk, an invisible buffer pushes them away. This ensures people naturally steer parallel along walls instead of hitting their faces against them.
  </li>
  <li><strong>Companion Cohesion (Friends &amp; Pairs):</strong>
    People in real life often walk with a friend or colleague. We pair up certain agents with an invisible &ldquo;elastic band&rdquo;. If one person gets pushed ahead by the crowd, they slow down or feel an attractive pull to stay near their companion.
  </li>
  <li><strong>Fire Thermal Repulsion &amp; Safety Buffer:</strong>
    Real people instinctively keep a wide berth around active fire due to intense heat, smoke, and danger. In our simulation, fire hazards emit a strong thermal barrier force (over 600 Newtons within 1.5&ndash;2.4 meters) and the pathfinder calculates safe detour waypoints around a protective safety zone, ensuring pedestrians naturally arc around flames rather than walking perilously close.
  </li>
</ol>

<div class='example-box'>
  <strong>How the computer calculates this every frame:</strong><br/>
  60 times every second, our physics engine adds up all 5 forces (Goal pull + People push + Wall push + Friend pull + Hazard repulsion). It uses simple Newtonian physics (<code>Force = Mass &times; Acceleration</code>) to update each person's exact speed and position.
  <br/><br/>
  <strong>Zero-Overlap &amp; Realistic Body Dimensions:</strong><br/>
  &bull; <strong>Human Body Radius (0.25m):</strong> Each person has a physical body radius of 0.25 meters (50 cm shoulder width), matching official crowd architectural standards. This gives people natural personal space without appearing oversized.<br/>
  &bull; <strong>Non-Overlap Hard Separation:</strong> In addition to social forces, our movement engine runs a hard non-overlap resolution pass every tick. Even in dense doorway queues, people form orderly physical lines and never clip or overlap through each other.
</div>

<hr/>

<h2>3. How People Find the Exits: Pathfinding &amp; BFS</h2>

<p>
A person might know how to walk, but <em>how do they know where the doors are?</em> 
They cannot see through solid concrete walls!
</p>

<h3>The Algorithm: Breadth-First Search (BFS)</h3>
<p>
Our building floor plan is made of walkable floor tiles and solid wall tiles. To find the shortest path from any room to an exit, we use an algorithm called <strong>Breadth-First Search (BFS)</strong>.
</p>

<div class='highlight-box'>
  <strong>How to visualize BFS:</strong><br/>
  Imagine you drop water on a tile. The water spreads outward evenly in all 4 directions (North, South, East, West). 
  It fills 1 tile away, then 2 tiles away, then 3 tiles away. 
  Because it spreads evenly, the first time the water touches your target, it is guaranteed to be the <strong>absolute shortest possible route</strong>.
</div>

<h3>Our Special Upgrade: Multi-Source Distance Field</h3>
<p>
If a building has 50 people and 4 emergency exits, calculating BFS 50 separate times would make the computer slow.
So we did something much smarter called a <strong>Multi-Source Distance Field</strong>:
</p>
<ol>
  <li>Instead of starting from a person, we start from <strong>all 4 exit doors at the same time</strong>.</li>
  <li>We flood water backwards into the building from all the exits simultaneously.</li>
  <li>Every single floor tile in the building records a number: its exact distance to the nearest exit door.</li>
  <li>Now, no matter where any person is standing, they just look at their neighboring tiles and step onto whichever tile has a lower number!</li>
</ol>
<p>
This takes only <strong>one single pass</strong> and instantly gives every person in the building their optimal route to safety.
</p>

<hr/>

<h2>4. What Mam Asked For: Congestion-Aware Dynamic Exit Balancing</h2>

<p>
This was one of the most important features requested for the project. Here is exactly what it is and how it works:
</p>

<h3>The Problem in Real Life (Exit Herding)</h3>
<p>
Suppose a room has 20 students. Exit 1 is right outside their door (5 meters away). Exit 2 is down the hall (12 meters away).<br/>
Naturally, all 20 students rush toward Exit 1. 
Because the door is narrow, only 1 person can squeeze through every second. 
The 18 people stuck in line are waiting 15 to 20 seconds, while Exit 2 is sitting completely empty!
</p>

<h3>How Our Balancing Algorithm Fixes This</h3>
<p>
Our simulation doesn't let agents act like blind robots. Every few ticks, trailing people evaluate a simple formula:
</p>

<div class='example-box'>
  <strong>The Balancing Formula:</strong><br/>
  <code>Total Time = (Distance to walk) + (2.2 seconds &times; Number of people in line)</code>
  <br/><br/>
  Suppose Student #15 is looking at Exit 1:<br/>
  &bull; Distance = 5 meters.<br/>
  &bull; People in line ahead = 15 people.<br/>
  &bull; Time to wait = 5 + (2.2 &times; 15) = <strong>38 seconds</strong>!
  <br/><br/>
  Now Student #15 looks at Exit 2 across the hall:<br/>
  &bull; Distance = 12 meters.<br/>
  &bull; People in line ahead = 0 people.<br/>
  &bull; Time to wait = 12 + (2.2 &times; 0) = <strong>12 seconds</strong>!
  <br/><br/>
  <strong>Decision:</strong> 12 seconds is way faster than 38 seconds! 
  Student #15 turns around, gets a glowing golden halo and a <strong>&ldquo;&#9889; DIVERTER&rdquo;</strong> badge, and sprints to Exit 2!
</div>

<h3>How we prevent people from &ldquo;Ping-Ponging&rdquo; back and forth:</h3>
<ul>
  <li><strong>Door Commitment:</strong> If you are already within 2.5 meters of the door, you are committed. You don't turn back.</li>
  <li><strong>Hysteresis Threshold:</strong> The other exit must be at least 1.2 seconds faster before you switch. This stops people from getting confused and wobbling back and forth.</li>
</ul>

<h3>How People Choose Exits Distant From Fire (Fire Hazard Aversion)</h3>
<p>
In an emergency, people do not just look at distance&mdash;they look at <strong>danger</strong>! 
If Exit 1 is 5 meters away but has active flames roaring right next to it, running toward Exit 1 is suicidal. 
Exit 2 may be 15 meters away, but it is on the opposite, smoke-free side of the building.
</p>

<div class='example-box'>
  <strong>How Our Fire-Averse Exit Selection Works:</strong><br/>
  Whenever active fire hazards exist, our pathfinding algorithm calculates the exact physical clearance between each emergency exit and the fire:
  <br/><br/>
  &bull; <strong>Immediate Threat (&lt; 4 meters from fire):</strong> An exit in the immediate flame zone receives an enormous safety penalty (+500 points). Unless it is literally the only exit in a sealed room, evacuees will completely refuse to target it.<br/>
  &bull; <strong>Moderate Proximity (&lt; 20 meters from fire):</strong> Exits receive a proportional hazard penalty based on how close they are to the flames.<br/>
  &bull; <strong>Safe Exits (&ge; 20 meters from fire):</strong> Exits on the far, safe side of the facility have 0 penalty.<br/>
  <br/>
  <strong>Result:</strong> Occupants naturally and intelligently evacuate toward doors <strong>distant from the fire</strong>. Even if a fire suddenly breaks out near an exit while people are walking towards it, they immediately re-evaluate, turn away from the smoke, and route to a safe, distant exit!
</div>

<hr/>

<h2>5. What Mam Asked For: The 4 Unseen Floor Plans &amp; Obstacles</h2>

<p>
Your evaluator wanted to ensure that the code works on <strong>any building layout</strong>, not just one pre-made room. We built 4 distinct floor plans that you can switch between by pressing <span class='term-badge'>L</span>:
</p>

<ol>
  <li><strong>Campus Complex (Default):</strong> 
    A university student center with 3 wings (Lecture Hall, Central Concourse, Library), structural pillars, and 4 exits (North, South, East, West).
  </li>
  <li><strong>Corporate Office Complex:</strong> 
    A long central horizontal hallway with 6 private research labs and 3 dedicated fire exit stairwells.
  </li>
  <li><strong>Airport Transit Terminal:</strong> 
    A ticketing hall that leads through a <strong>narrow security screening choke point</strong> (simulating an extreme bottleneck) into a duty-free departures lounge.
  </li>
  <li><strong>Procedural Unseen Floor Plan:</strong> 
    A layout created algorithmically by random code. This proves mathematically that no matter how weird the rooms are, our BFS flood-fill algorithm guarantees everyone can reach an exit.
  </li>
</ol>

<h3>The 4 Real Architectural Obstacles</h3>
<p>
Buildings have real furniture that people must walk around. We added 4 obstacle types with real collision boxes:
</p>
<ul>
  <li><strong>Information Kiosks (Wood reception desk with &ldquo;INFO&rdquo;):</strong> Placed in central halls to see how crowd streams split in two.</li>
  <li><strong>Cedar Seating Benches:</strong> Placed in corridors to block straight-line walking and force people to use the sides.</li>
  <li><strong>Botanical Planters (Green foliage pots):</strong> Flank doorways to create natural entry funnels.</li>
  <li><strong>Lecture Desks:</strong> Clustered in classrooms to test how people squeeze through aisle seating.</li>
</ul>

<hr/>

<h2>6. What Are All Those Things on the Screen?</h2>

<table>
  <tr>
    <th>Visual Element</th>
    <th>What It Means in Plain English</th>
  </tr>
  <tr>
    <td><strong>Exit Queue Badges<br/><code>[Q:0 CLEAR]</code> vs <code>[Q:15+ JAMMED!]</code></strong></td>
    <td>Pill labels above each exit door. Green means no line. Red means a crowd bottleneck has formed.</td>
  </tr>
  <tr>
    <td><strong>Golden Halo &amp; <code>&#9889; DIVERTER</code></strong></td>
    <td>Appears over any person who was smart enough to turn away from a crowded exit and head for an open one.</td>
  </tr>
  <tr>
    <td><strong>Egress Curve (S-Curve Graph)</strong></td>
    <td>
      The live graph on the right panel. It plots how many people have escaped over time. 
      It naturally forms an &ldquo;S&rdquo; shape (slow start while walking, steep middle when doors flow at full speed, flat end as stragglers finish).
    </td>
  </tr>
  <tr>
    <td><strong>Density Heatmap (Key H)</strong></td>
    <td>
      A glowing colored overlay over the floor. Blue means plenty of open space; yellow means crowded; red means severe crushing danger at doorways.
    </td>
  </tr>
  <tr>
    <td><strong>Occupant Inspector Card</strong></td>
    <td>
      Clicking any person with the mouse opens their profile card showing their name, current speed, stress meter, companion friend, and their planned path line.
    </td>
  </tr>
</table>

<hr/>

<h2>7. How the Code Files Are Organized</h2>

<p>
If someone asks: <em>&ldquo;Where is the code for X?&rdquo;</em>, here is the clean breakdown:
</p>

<ul>
  <li><code>main.py</code>: The master entry point. It creates the Pygame window, handles mouse clicks, keyboard shortcuts, and button clicks.</li>
  <li><code>Review 2/environment/</code>:
    <ul>
      <li><code>grid.py</code>: The 2D grid of tiles (0 = floor, 1 = wall, 2 = exit).</li>
      <li><code>building.py</code>: Creates the 4 floor plans, rooms, doorways, pillars, and 4 furniture obstacles.</li>
    </ul>
  </li>
  <li><code>Review 2/algorithms/</code>:
    <ul>
      <li><code>pathfinding.py</code>: The Breadth-First Search (BFS) and Multi-Source Distance Field logic.</li>
    </ul>
  </li>
  <li><code>Review 2/agents/</code>:
    <ul>
      <li><code>agent.py</code>: The Person class (stores position, speed, panic state, companion ID).</li>
      <li><code>manager.py</code>: Spawns people, pairs up friends, and tracks who has evacuated.</li>
    </ul>
  </li>
  <li><code>Review 2/simulation/</code>:
    <ul>
      <li><code>physics.py</code>: Helbing's Social Force Model (calculates pushing forces between people and walls).</li>
      <li><code>engine.py</code>: The brain of the simulation. Runs the clock, checks the congestion exit balancing, and moves people.</li>
    </ul>
  </li>
  <li><code>Review 2/visualization/</code>:
    <ul>
      <li><code>renderer.py</code>: Draws the floor plan, furniture, people, queue badges, and heatmap.</li>
      <li><code>dashboard.py</code>: The right-hand control panel with buttons, metrics, and occupant dossier.</li>
      <li><code>graph.py</code>: Draws the live real-time S-curve evacuation chart.</li>
    </ul>
  </li>
  <li><code>Review 2/tests/</code>:
    45 automated unit tests written in Pytest that prove every formula, path, and collision works with 100% success.</li>
</ul>

<hr/>

<h2>8. Summary: What to Remember Above All Else</h2>
<ol>
  <li>We use <strong>Continuous Physics (Social Force Model)</strong>, not a primitive square-jumping grid.</li>
  <li>We use <strong>Multi-Source BFS</strong> to find the shortest path to all exits in a single, fast calculation.</li>
  <li>We built <strong>Congestion-Aware Exit Balancing</strong> so trailing people calculate delays and divert to open exits with golden badges.</li>
  <li>We have <strong>4 distinct floor plans</strong> and <strong>4 real furniture obstacles</strong> to prove generalization.</li>
  <li>Everything is verified by <strong>45 automated unit tests</strong> with a 100% pass rate.</li>
</ol>

</body>
</html>
"""

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    html_content = generate_doc()

    doc_path = os.path.join(base_dir, "Project_Explanation_In_Simple_Terms.doc")
    root_doc_path = os.path.join(base_dir, "..", "Project_Explanation_In_Simple_Terms.doc")

    print(f"Writing {doc_path}...")
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Writing {root_doc_path}...")
    with open(root_doc_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print("Done! Both .doc files created successfully.")

if __name__ == "__main__":
    main()
