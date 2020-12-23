# http server driver and associated machinery

import http.server as Hs



class Handler(Hs.BaseHTTPRequestHandler):
    """Handler object invoked on each attempt to get/post/whatever via http server"""

    # docs say not to override/extend __init__ method, so we do not

    def do_GET(self):
        """Called to respond to an HTTP GET"""

        # self.requestline is current request line...?
        # self.path is current path...?
        # self.headers is header container...?
        # self.rfile is where we'd read post data from, probably?
        # self.wfile is output sream to send data back to

        # flow:
        # self.send_response(code)
        # self.send_header(key, value)
        # self.end_headers()
        # write data (page) to self.wfile

        self.send_response(200)
        self.send_header('myheader', 'myvalue')
        self.end_headers()
        self.write('''<html><body>
                requestline = '{rl}'<br>
                path = '{path}'<br>
                got some stuff, yay!<br>
                </body></html>'''.format(rl=self.requestline, path=self.path))

        # use link to set player session room?
        # use player session to find current room?
        # get room, ask it to "render" based on session
        pass



class Server:
    """High level wrapper for the http server, tracking various important bits"""

    def __init__(self):
        self.m_rooms = None
        self.m_group = None

    def SetRooms(self, rooms):
        self.m_rooms = rooms

    def SetGroup(self, group):
        self.m_group = group

    def Run(self):
        addr = ('', 8000)   # all interfaces, port 8000
        server = Hs.ThreadingHTTPServer(addr, Handler)
        server.serve_forever()
