# http server driver and associated machinery

class Server:
    def __init__(self):
        self.m_rooms = None
        self.m_group = None

    def SetRooms(self, rooms):
        self.m_rooms = rooms

    def SetGroup(self, group):
        self.m_group = group

    def Run(self):
        # TODO
        pass
