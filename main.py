# front end driver for web-adventure

import argparse
import layout
import os
import server
import session

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run the web-adventure server")
    parser.add_argument('--datadir', default='.', help="Select the data directory")
    args = parser.parse_args()

    # change to the appropriate directory

    os.chdir(args.datadir)

    rooms = layout.Rooms()
    rooms.Load("game.yml")

    group = session.Group()
    group.Load("sessions")
    group.InitRooms(rooms)

    server = server.Server()
    server.SetRooms(rooms)
    server.SetGroup(group)
    server.Run()
