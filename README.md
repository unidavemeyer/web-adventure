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
(possibly simultaneously) we thus have one or more sessions on the server side. A session remembers state for the particular player
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
 * Description (required): Every room must have a description to display to the player.
 * Exits (required): Every room must have one or more possible exits. Exits may be conditional (hidden if player doesn't match).
 * Session (optional): Rooms may define changes to apply to the player's session on entry into the room.

