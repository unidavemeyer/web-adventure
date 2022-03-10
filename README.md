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
   * Variables
   * Functions
   * Classes
   * Methods (vs. functions)
   * Modules (aka imports)
 * A basic understanding of YAML will be quite helpful in order to author content (see www.yaml.org)
 * Basic project code understanding:
   * What does main.py do?
   * How are areas in the game organized (what classes)? In which file(s) do you find that code?
   * What does the Session class do?
   * What does the Handler class do?
   * Where is most of the "interesting" functionality handled (class and file)?
   * Where do you find an example set of game data?

