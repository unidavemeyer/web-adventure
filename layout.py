# room layout support and machinery

import yaml

class Room:
    """A single room in the game area"""

    def __init__(self):
        self.m_name = None
        self.m_desc = None
        self.m_lExit = []
        self.m_lChange = []

    def Load(self, doc):
        """Serialize in a room from a yaml source doc"""
        self.m_name = doc.get('name')
        self.m_desc = doc.get('desc')
        self.m_lExit = doc.get('exits')
        self.m_lChange = doc.get('changes', [])

        # HINT: expect something like the lines above for the room to know its type

        # HINT: if we have a grid type room, we may also want to load in the template
        #  html page data from its file here, and store it for future use in a Desc()
        #  function/def on the Room class

        # HINT: for grid rooms, the desc field may be another dictionary instead of a
        #  string, so that we could have the layout and the image references

    def StrErrors(self):
        lStrErr = []

        if self.m_name is None:
            lStrErr.append("Room is missing a name")

        if self.m_desc is None:
            lStrErr.append("Room {r} is missing desc".format(r=self.m_name))

        # HINT: if this is a grid room, we should verify that self.m_desc has the
        #  fields we expect, with appropriate contents, etc.

        if self.m_lExit is None:
            lStrErr.append("Room {r} is missing exits".format(r=self.m_name))
        elif not isinstance(self.m_lExit, list):
            lStrErr.append("Room {r} exits is not a list".format(r=self.m_name))

        if self.m_lChange is None:
            pass    # OK to not have changes
        elif not isinstance(self.m_lChange, list):
            lStrErr.append("Room {r} changes is not a list".format(r=self.m_name))

        # TODO: check exits, changes, if present, for validity as well

        return '\n'.join(lStrErr)

    def LExit(self):
        return self.m_lExit

    def LChange(self):
        return self.m_lChange

    # HINT: this is where we could add a Desc() function/def, which:
    #  for non-grid rooms would return self.m_desc
    #  for grid rooms would:
    #    create divs with content from self.m_desc
    #    put those divs into the template
    #    return the combined template/divs as the page content

class Rooms:
    """Stores information about the whole room layout"""

    def __init__(self):
        self.m_mpNameRoom = {}
        self.m_roomStart = None

    def Load(self, path):
        with open(path, 'r') as fileIn:
            for doc in yaml.safe_load_all(fileIn):
                if doc is None:
                    continue

                room = Room()
                room.Load(doc)
                strErr = room.StrErrors()

                if strErr:
                    print(strErr)
                elif room.m_name in self.m_mpNameRoom:
                    print("Room {r} defined more than once!".format(r=room.m_name))
                else:
                    self.m_mpNameRoom[room.m_name] = room
                    if self.m_roomStart is None:
                        # TODO: come up with a better plan here
                        self.m_roomStart = room

    def Room(self, name):
        """Return the room by the given name, or None if there is no such room"""

        return self.m_mpNameRoom.get(name, None)

if __name__ == '__main__':
    # testing code if we run layout directly
    rooms = Rooms()
    rooms.Load('example_layout.yml')
    print("Finished loading example layout (errors, if any, are above)")
