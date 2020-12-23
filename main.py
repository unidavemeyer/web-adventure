# front end driver for web-adventure

import server
import layout
import session

if __name__ == '__main__':
    rooms = layout.Rooms()
    rooms.Load("example_layout.yml")    # TODO: correct this to be the real deal

    group = session.Group()
    group.Load()

    server = server.Server()
    server.SetRooms(rooms)
    server.SetGroup(group)
    server.Run()
