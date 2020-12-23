# room layout support and machinery

class Room:
    """A single room in the game area"""

    def __init__(self):
        self.m_name = None
        self.m_desc = None
        self.m_lExit = []
        self.m_lChange = []



class Rooms:
    """Stores information about the whole room layout"""

    def __init__(self):
        self.m_mpNameRoom = {}
        # TODO
        pass

    def Load(self):
        # TODO
        pass

