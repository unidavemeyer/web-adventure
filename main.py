# front end driver for web-adventure

import server
import layout
import session

if __name__ == '__main__':
    rooms = layout.Rooms()
    rooms.Load("game.yml")    # TODO: command line arg to select?

    group = session.Group()
    group.Load("sessions")    # TODO: command line arg to select?
    group.InitRooms(rooms)

    server = server.Server()
    server.SetRooms(rooms)
    server.SetGroup(group)
    server.Run()
