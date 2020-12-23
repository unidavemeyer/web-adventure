# session-related machinery (tracks player state)

class Session:
    """Information about the state for a single player"""

    def __init__(self):
        self.m_uid = None
        self.m_room = None



class Group:
    """All of the sessions known by the system"""

    def __init__(self):
        self.m_mpUidSession = {}

    def Load(self):
        # TODO
        pass
