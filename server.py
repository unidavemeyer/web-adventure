# http server driver and associated machinery

import http.server as Hs



class Handler(Hs.BaseHTTPRequestHandler):
    """Handler object invoked on each attempt to get/post/whatever via http server"""

    # docs say not to override/extend __init__ method, so we do not

    def do_POST(self):
        """Called to respond to an HTTP POST"""

        g_server.HandlePost(self)

    def do_GET(self):
        """Called to respond to an HTTP GET"""

        g_server.HandleGet(self)

    def ExamplePostPageNotCalled(self):
        self.send_response(200)
        self.send_header('myheader', 'myvalue')
        self.end_headers()

        self.wfile.write('<html><body>'.encode())
        self.wfile.write('<h1>POST!</h1>'.encode())
        self.wfile.write("requestline = '{rl}'<br>".format(rl=self.requestline).encode())
        self.wfile.write("path = '{path}'<br>".format(path=self.path).encode())
        for field, value in self.headers.items():
            self.wfile.write("header '{h}' = '{v}'<br>".format(h=field, v=value).encode())
        if 'Content-Length' in self.headers:
            # NOTE can only read as many bytes as listed in content length -- for HTTP/1.1 clients, the
            #  connection might be left alive, so can't just read to the end. Not sure what/how we should
            #  deal with HTTP/1.0 clients -- that might require the other behavior, although with a content
            #  length they should act the same way I believe
            strIn = self.rfile.read(int(self.headers['Content-Length']))
            self.wfile.write("POST data '{s}'<br>".format(s=strIn).encode())
        self.wfile.write('</body></html>'.encode())

    def ExamplePageNotCalled(self):
        # self.requestline is current request line: 'GET /abc/def HTTP/1.1'
        # self.path is current path: '/abc/def'
        # self.headers is header container...?
        # self.rfile is where we'd read post data from, probably?
        # self.wfile is output sream to send data back to

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
                </html>'''.encode())



class Server:
    """High level wrapper for the http server, tracking various important bits"""

    def __init__(self):
        self.m_rooms = None
        self.m_group = None
        self.m_mpSidSession = {}
        global g_server
        g_server = self

        # Set up function tables for handling various POST and GET URLs

        self.m_mpPathPost = {
                "/login" : self.OnPostLogin,
                "/room" : self.OnPostRoom,
                }

        self.m_mpPathGet = {
                "/" : self.OnGetLogin,
                "/favicon.ico" : self.OnGetFavicon,
                "/login" : self.OnGetLogin,
                }

    def SetRooms(self, rooms):
        self.m_rooms = rooms

    def SetGroup(self, group):
        self.m_group = group

    def Run(self):
        addr = ('', 8000)   # all interfaces, port 8000
        ths = Hs.ThreadingHTTPServer(addr, Handler)
        ths.serve_forever()

    def FIsValidSid(self, sid):
        if self.m_mpSidSession.get('sid') is None:
            return False

        # TODO: some notion of sid timeout?

        return True

    def HandlePost(self, handler):
        """Dispatch an HTTP POST request to the appropriate place"""

        # Expectation:
        #  - post data will be URL encoded (i.e., key=value&key=value&...)
        #  - TODO: can we make this be the case somehow?

        # redirect if we don't understand where the post is

        fn = self.m_mpPathPost.get(handler.path)
        if fn is None:
            self.OnRedirectLogin(handler)

        # extract and convert post data if possible

        strCl = 'Content-Length'
        dPost = {}
        if strCl in handler.headers:
            cB = int(handler.headers[strCl])
            strPost = handler.rfile.read(cB).decode()
            for strKvp in strPost.split('&'):
                k,v = strKvp.split('=')
                dPost[k] = v

        # TODO think about wrapping in try/except to make more armored maybe?

        fn(handler, dPost)

    def HandleGet(self, handler):
        """Dispatch an HTTP GET request to the appropriate place"""

        fn = self.m_mpPathGet.get(handler.path)
        if fn is not None:
            fn(handler)
        else:
            self.OnRedirectLogin(handler)

    def OnRedirectLogin(self, handler):
        # generate 303 return sending people to GET the /login endpoint

        # TODO: include Content-Length

        handler.send_response(303)
        handler.send_header('Location', '/login')
        handler.end_headers()

        lStr = [
                '<html>',
                '<body>',
                '<h1>Oops!</h1>',
                '<p>Something went wrong. You should be redirected, but if not, try to <a href="/login">log in</a>.</p>',
                '</body>',
                '</html>',
            ]

        for str0 in lStr:
            handler.wfile.write(str0.encode())
            handler.wfile.write('\n'.encode())

    def OnPostLogin(self, handler, dPost):
        """Handle the submit end of attempting to log in"""

        # TODO actually validate, make welcome page, links to go to room, etc.?

        handler.send_response(200)
        handler.end_headers()
        
        lStr = [
                '<html>',
                '<body>',
                '<p>user: "{u}"</p>'.format(u=dPost.get('login', 'MISSING')),
                '<p>pass: "{p}"</p>'.format(p=dPost.get('pass', 'MISSING')),
                '</body>',
                '</html>',
                ]

        for str0 in lStr:
            handler.wfile.write(str0.encode())
            handler.wfile.write('\n'.encode())

    def OnPostRoom(self, handler, dPost):
        """Handle the submit end of attempting to access a room"""

        # TODO actually run room logic here
        #
        # flow:
        #  - post should indicate desired exit index
        #  - if post wants to set room, adjust session
        #  - get room from session
        #  - ask session to "render" current room
        #    - session should cache room contents to avoid redo on reload, etc.

        # deal with missing/incorrect sessions (has to handle in room logic...sigh...)

        if 'sid' not in dPost:
            self.OnRedirectLogin(handler)
            return

        if 'sid' not in self.m_mpSidSession:
            self.OnRedirectLogin(handler)
            return

        # TODO: expired sessions?

        handler.send_response(200)
        handler.end_headers()
        
        lStr = [
                '<html>',
                '<body>',
                ]

        for key, value in dPost:
            lStr.append('<p>{k}: "{v}"</p>'.format(k=key, v=value))

        lStr.append([
                '</body>',
                '</html>',
                ])

        for str0 in lStr:
            handler.wfile.write(str0.encode())
            handler.wfile.write('\n'.encode())

    def OnGetLogin(self, handler):
        """Provide the initial login page"""

        handler.send_response(200)
        handler.end_headers()

        lStr = [
                '<html>',
                '<head>Login</head>',
                '<body>',
                '<h1>Welcome</h1>',
                '<p>You have found your way to web-adventure, and in order to continue, you need to...</p>',
                '<h1>Login</h1>',
                '<form action="/login" method="post">',
                    '<label for="login">Username:</label>',
                    '<input type="text" id="login" name="login" autocomplete="off" autofocus maxlength=20 required size=20/>',
                    '<label for="pass">Spec:</label>',
                    '<input type="password" id="pass" name="pass" autocomplete="off" autofocus maxlength=20 required size=20/>',
                    '<input type="submit" value="Go"/>',
                '</form>',
                # TODO add new user link here - OnGetNewUser, different form, different post?
                '</body>',
                '</html>',
            ]

        for str0 in lStr:
            handler.wfile.write(str0.encode())
            handler.wfile.write('\n'.encode())

    def OnGetFavicon(self, handler):
        """Favicon handling"""

        handler.send_response(404)
        handler.end_headers()

    def FormExample(self, handler, lPart):
        """Example of doing form stuff, useful while experimenting with things"""

        # show login form
        handler.send_response(200)
        handler.end_headers()
        handler.wfile.write('''<html>
                <head>Login</head>
                <body>
                <h1>Welcome</h1>
                <p>You have found your way to web-adventure, and in order to continue, you need to...</p>
                <h1>Login</h1>
                <form action="/login&user=1" method="post">
                    <label for="login">Username:</label>
                    <input type="text" id="login" name="login" autocomplete="off" autofocus maxlength=20 required size=20/>
                    <label for="spec">Spec:</label>
                    <input type="text" id="spec" name="spec" autocomplete="off" autofocus maxlength=20 required size=20/>
                    <input type="hidden" name="hid" id="hid" value="also_here"/>
                    <input type="submit" value="Submit"/>
                </form>
                </body>
                </html>'''.encode())

# TODO: probably need better/smarter tracking of this across imports and such
g_server = None
