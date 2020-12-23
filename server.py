# http server driver and associated machinery

import http.server as Hs



class Handler(Hs.BaseHTTPRequestHandler):
    """Handler object invoked on each attempt to get/post/whatever via http server"""

    # docs say not to override/extend __init__ method, so we do not

    def do_GET(self):
        """Called to respond to an HTTP GET"""

        # self.requestline is current request line: 'GET /abc/def HTTP/1.1'
        # self.path is current path: '/abc/def'
        # self.headers is header container...?
        # self.rfile is where we'd read post data from, probably?
        # self.wfile is output sream to send data back to

        # expected path: /room&sid=xxx&choice=n
        #  - room = literally "room"
        #  - xxx = session ID if session is established
        #  - n = exit selected; if not present, just do room directly not switch rooms
        # new session?
        #  - take to login page if no sid is present in data or if sid has expired
        # how to *actually* track a session? is that a cookie? hmm...could also do in URL
        #  - from reading RFC 6265, cookies are pretty insecure and/or unreliable, although using a session nonce is maybe ok
        #  - alternative, from my perspective: encode the session ID (not the user, though!) as part of the URI
        #  - could do /path&sid=xxx, for example, with & split and then have KVP's in the list...not crazy, maybe
        # use link to set player session room?
        #  - could use "cur" as path to indicate no change
        #  - do we want some kind of caching/reloading mechanism to only stamp entry on first room change?
        #  - exits do different links, maybe, which set player room in session
        # use player session to find current room?
        # get room, ask it to "render" based on session

        # flow:
        # self.send_response(code)
        # self.send_header(key, value)
        # self.end_headers()
        # write data (page) to self.wfile

        # This is an example of how to do basic stuff

        self.send_response(200)
        self.send_header('myheader', 'myvalue')
        self.end_headers()
        self.wfile.write('''<html><body>
                requestline = '{rl}'<br>
                path = '{path}'<br>
                got some stuff, yay!<br>
                </body></html>'''.format(rl=self.requestline, path=self.path).encode())

        # check for a sid

        lPart = self.path.split('&')
        sid = None
        for part in lPart:
            if part.startswith('sid='):
                sid = part[4:]
                break

        if lPart[0] == '/login' or lPart[0] == '/':
            g_server.RunLogin(self, lPart)
        if g_server.FIsValidSid(sid):
            g_server.RunRequest(self, sid, lPart)
        else:
            self.SendErrorPage()

    def SendErrorPage(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write('''<html>
                <head>Oops!</head>
                <body>
                <p>Not sure how you ended up here, but good job! (Maybe your session timed out?)</p>
                <p></p>
                <p>Try <a href="/login">logging in</a> to continue.</p>
                </body>
                </html>''')



class Server:
    """High level wrapper for the http server, tracking various important bits"""

    def __init__(self):
        self.m_rooms = None
        self.m_group = None
        self.m_mpSidSession = {}
        global g_server
        g_server = self

    def SetRooms(self, rooms):
        self.m_rooms = rooms

    def SetGroup(self, group):
        self.m_group = group

    def Run(self):
        addr = ('', 8000)   # all interfaces, port 8000
        ths = Hs.ThreadingHTTPServer(addr, Handler)
        ths.serve_forever()

    def FIsValidSid(self, sid):
        if not self.m_mpSidSession.get('sid'):
            return False

        # TODO: some notion of sid timeout?

        return True

    def RunLogin(self, handler, lPart):
        """Fill out an appropriate login page via the handler"""
        # TODO: with no args, show a login form
        # TODO: with args, add a new session/player maybe?
        # TODO: if login is valid, set up session sid and go from there
        pass

    def RunRequest(self, handler, sid, lPart):
        """Handle a request for a particular room for a particular session"""

        # TODO

        # if we have a choice part, use that & current room to update the session's room

        # render the session's current room

        # expected path: /room&sid=xxx&choice=n
        #  - room = literally "room"
        #  - xxx = session ID if session is established
        #  - n = exit selected; if not present, just do room directly not switch rooms
        # new session?
        #  - take to login page if no sid is present in data or if sid has expired
        # how to *actually* track a session? is that a cookie? hmm...could also do in URL
        #  - from reading RFC 6265, cookies are pretty insecure and/or unreliable, although using a session nonce is maybe ok
        #  - alternative, from my perspective: encode the session ID (not the user, though!) as part of the URI
        #  - could do /path&sid=xxx, for example, with & split and then have KVP's in the list...not crazy, maybe
        # use link to set player session room?
        #  - could use "cur" as path to indicate no change
        #  - do we want some kind of caching/reloading mechanism to only stamp entry on first room change?
        #  - exits do different links, maybe, which set player room in session
        # use player session to find current room?
        # get room, ask it to "render" based on session

        pass

# TODO: probably need better/smarter tracking of this across imports and such
g_server = None
