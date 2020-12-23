# front end driver for web-adventure

import http
import layout
import session

if __name__ == '__main__':
    rooms = layout.Rooms()
    rooms.Load()

    group = session.Group()
    group.Load()

    server = http.Server()
    server.SetRooms(rooms)
    server.SetGroup(group)
    server.Run()
