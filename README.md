web-adventure
=============

Purpose
-------

In December 2020 I decided it would be potentially fun and interesting to write a little web-based choose your own adventure
game that might be fun for my kids to try out (both as players and potentially as authors). Since I know some stuff about writing
http servers with python, I figured it would be fun to try setting things up that way, since it would allow some potentially
interesting options on the adventure authoring side (remembering state, etc.). Hence, web-adventure.

Architecture
------------

The main idea here is to use python3's http.server module (yes, not marked for production use, this is a toy!) to implement a
http server, and to thus create one or more request handlers that implement the actual behavior. In order to have multiple players
(possibly simultaneously) we also have one or more sessions on the server side. A session remembers state for the particular player
so that we can do interesting things like have a "current" URL that always returns where the player is, even if that is a different
logical location over the course of the game, or a different logical location than another player.

The system therefore needs to read in two different pieces of information:

 * The room layouts
 * The stored sessions

Sessions
--------

Sessions need to be stored periodically to avoid players losing progress. Otherwise, sessions are effectively dictionaries storing
information about the player's progress. At the very least, a session will need to track the player's current location. The session
may also track other information about the player, perhaps values noted in room definitions based on player actions.

Room Layouts
------------

The logical rooms that a player may be in are authored in a room layout. This should be a series of YAML documents, possibly stored
in multiple files, where each document defines a single room. Rooms can define several pieces of information that are relevant to
the system as shown below.

 * Name (required): Every room must have a unique name within the scope of the overall room layout the room belongs to.
 * Description (required): Every room must have a description to display to the player. Descriptions can contain
   variables in them for expansion, as used by python's "format" function, e.g., {var}. Variables will be expanded by pulling
   them from the player's session.
 * Exits (required): Every room must have one or more possible exits. Exits may be conditional (hidden if player doesn't match).
   Conditions on an exit may compare session variables to other session variables or to constant values. As with descriptions,
   exit text will be formatted with session variable expansions applied.
 * Change (optional): Rooms may define one or more changes to apply to the player's session on entry into the room. Changes
   provide simple expressions that can set the value of a session variable, add or subtract something from one, put a ranged
   randomized integer in one, or set to the current time value in seconds. Changes are applied in order of definition prior
   to generating the description and exits for the room.

Examples for how rooms in a room layout can be put together can be found in example\_layout.yml

Big Picture Internship - Spring Semester 2022
=============================================

Initial Work
------------

In no particular order, there are several things that need to happen at the beginning of the internship process so that
we can make progress:

 * Python3 needs to be installed on your computer so that you can run the project.
 * A git client (compatible with github) needs to be installed on your computer so you can clone the project and
   make contributions.
 * A basic understanding of python will be required in order to follow what is going on. Specific topics of interest:
   * Variables (including lists and dictionaries)
   * Functions
   * Classes
   * Methods (vs. functions)
   * Modules (aka imports)
 * A basic understanding of YAML will be quite helpful in order to author content (see www.yaml.org)
 * Basic project code understanding:
   * What does main.py do?
   * How are areas in the game organized (what classes)? In which file(s) do you find that code?
   * What does the Session class do?
     * With the basic overview of the Session class in mind, what do the rest of the session methods do?
   * What does the Handler class do?
   * Where is most of the "interesting" functionality handled (class and file)?
   * Where do you find an example set of game data?
   * Explain the general flow of function calls, etc., when a player clicks on a link

Project Notes
-------------

Intern expects programming primarily. Moving a character around, picking up items, secret areas,
possibly an enemy. Graphics side: maybe small animations and like pixellated game.

From discussion, moving on a 2d grid seems like a possibly reasonable thing as a long term goal.
In order to make that happen, we'd need general image support for the project so that it could
show images in addition to text content. We probably also need support for something like a table
so that we could form an image grid, although it's possible that there's a different HTML thing
that we'd want instead of a table. Presumably, each image tile would also be a link so that the
player would have freedom to choose where to interact (move, etc.) with every tile. Another thought
is that maybe we want image maps here...but I'm not sure.

For this to work, I think we'd want to allow the Room to be organized with arbitrary positioning
for links, along with the image and table bits. The session could keep track of the hero position
as part of its dictionary entries (x,y coords). Effectively links could adjust the hero position
or whatever as they were followed. Could still switch between rooms (say at boundary or border
grid locations) to have different layouts available in different areas. Could pretty easily thus
do a simple "collecting" model where some room cells had contents. Player entry into the cell
causes the contents to enter player inventory.

Question: can we generate links appropriately connected to the images that still do POST
operations instead of GET operations? We want to have the post contents go along so we can track
session IDs and the like, so we don't really want a plain old GET. If we absolutely cannot do
POST this way, it would be *possible* to convert to a model where information for the link is
encoded (say to some base64 hash or some type of general data identifier like the session one)
such that we could use GET operations instead of POST ones, but that feels a bit on the gross
side to me. That would be a lot of additional plumbing that we don't currently have, I think.

If we added a notion of "type" to the Room, and possibly created subclasses thereof, we could
even combine some map-based movement (grid rooms) with story/corridor (text adventure rooms)
by simply linking the two of them together. This may not actually be a crazy idea, as it would
allow simple transitions with explanatory text before entering a dungeon, for example.

We may wish to consider the possibility of also displaying some "always on" or "nearly always on"
bits of content in addition to the room itself. For example, player inventory or perhaps player
stats of some kind. Those could be as a header or a footer to the room content. Perhaps rooms
would opt in/out of displaying this as part of their configuration?

NPCs would be some work, but we could imagine that their notion of "time" only advances when the
player makes moves. Fast enemies move every player move (and possibly multiple cells) while slow
enemies may stay in place for several player moves. Not clear if/how combat would work in this
type of a scenario, although possibly something akin to a turn-based JRPG could be made to work
relatively simply - player selects their action, then NPC gets a turn, etc.

Project Plan
------------

This is a roughly ordered collection of ideas about how I think we would want to approach the
items discussed in Project Notes above. There is definitely room for interpretation on how this
should be done, but I've at least made some attempt to order things based on dependencies.

 1. ~~Add support for images to Room contents. Make a couple of examples to demonstrate.~~
    * ~~Mentor will add image support -- seems like it would have nuance that may be tricky.~~
 2. Add support for Room objects in YAML to have types, unlocking subtypes for rooms.
    * Initially just have this as a property on the Room class, serialized in from YAML
    * Decide if this is a required property or not (both have advantages)
 3. Make a mock-up (in plain HTML) of a gridded image series.
    * Ideally, can test image support by doing this as the contents of a Room in YAML as well
    * Will involve making some additional image contents (at least placeholder quality)
 4. Add a GridRoom subclass and link it to the grid type. These are image grids. Make an example.
    * Note that this will definitely be a subclass, so it will inherit much behavior from Room
    * May need to adjust the load method to support pre-pulling room properties and then determining proper class to instantiate
    * Will want to carefully consider authoring model here - perhaps "text bitmap" with lookup table (like an indexed image?)
    * Can/should we support more than just rectangular grids?
 5. Adjust HTML generation to support interstitial links (preferably POST!) to support clickable image grids.
    * Some reading on the subject suggests we may need to incorporate JavaScript to make this work, which is fine
 6. Incorporate the concept of the hero position for the GridRoom class. Associate with an image. Make an example.
    * May also consider if/how exits would manipulate this for entry to other GridRooms
 7. Add an Item class. These can have position in a GridRoom and an associated image.
 8. Allow defining Items in a GridRoom in YAML. Make an example.

Daily Plans
-----------
 1. 2022-03-31: (unlikely all of these will be accomplished, but listing out thoughts)
    * Contact Mentor once setup and ready to proceed in the morning for start-of-day discussion
    * Discuss possibility of getting git client installed on school laptop
    * Continue to answer questions from the Initial Work section, starting with further detail on the additional
      Session class methods and continuing from there
    * Download copies of relevant code (ideally git, but can just download directly if git is not present)
    * Make adjustments (quite possibly with Mentor help!) to get local copy of the project running
    * Adjust or make own version of game content YAML and run it to gain familiarity with the authoring model
    * Look at a set of changes in github - try the one for image support, report on image formats that are supported
    * Run program (main.py) and use browser to go to http://localhost:8000
    * Start developing a plan for how to do Project Plan item (2)
