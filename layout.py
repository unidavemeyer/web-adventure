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
        self.m_lChange = doc.get('changes')

    def StrErrors(self):
        lStrErr = []

        if self.m_name is None:
            lStrErr.append("Room is missing a name")

        if self.m_desc is None:
            lStrErr.append("Room {r} is missing desc".format(r=self.m_name))

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



class Rooms:
    """Stores information about the whole room layout"""

    def __init__(self):
        self.m_mpNameRoom = {}
        self.m_roomStart = None
        pass

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

if __name__ == '__main__':
    # testing code if we run layout directly
    rooms = Rooms()
    rooms.Load('example_layout.yml')
    print("Finished loading example layout (errors, if any, are above)")
