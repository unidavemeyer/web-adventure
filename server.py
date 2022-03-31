# http server driver and associated machinery

import http.server as Hs
import os
import secrets



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
                <head><title>Oops!</title></head>
                <body>
                <h1>Oops!</h1>
                <p>Not sure how you ended up here, but good job! (Maybe your session timed out?)</p>
                <p></p>
                <p>Try <a href="/login">logging in</a> to continue.</p>
                </body>
                </html>'''.encode())



class Server:
    """High level wrapper for the http server, tracking various important bits"""

    s_strPathImage = '/image'

    def __init__(self):
        self.m_rooms = None
        self.m_group = None
        self.m_mpSidSession = {}
        global g_server
        g_server = self

        # Set up function tables for handling various POST and GET URLs

        self.m_mpPathPost = {
                "/create" : self.OnPostCreate,
                "/login" : self.OnPostLogin,
                "/room" : self.OnPostRoom,
                }

        # TODO could also add handling for /img subtree and thus allow graphics links to work (!!)

        self.m_mpPathGet = {
                "/" : self.OnGetLogin,
                "/create" : self.OnGetCreate,
                "/favicon.ico" : self.OnGetFavicon,
                "/login" : self.OnGetLogin,
                self.s_strPathImage : self.OnGetImage,
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
        if self.m_mpSidSession.get(sid) is None:
            return False

        # TODO: some notion of sid timeout?

        return True

    def SidGenerate(self):
        """Generate a new unused SID"""

        # Seems like the loop should be completely unnecessary, but also shouldn't
        #  really hurt anything to have it

        while True:
            sid = secrets.token_hex(nbytes=16)
            if sid not in self.m_mpSidSession:
                return sid

    def HandlePost(self, handler):
        """Dispatch an HTTP POST request to the appropriate place"""

        # Expectation:
        #  - post data will be URL encoded (i.e., key=value&key=value&...)
        #  - above should be true since default for form is "enctype=application/x-www-form-urlencoded"
        #  - NOTE spaces are switched to + and special characters are converted to ASCII HEX

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
            return

        # For images, we want to allow effectively doing direct file mapping, which means the path
        #  won't actually match the entirety in the dictionary

        if handler.path.startswith(self.s_strPathImage + '/'):
            fn = self.m_mpPathGet.get(self.s_strPathImage)
            fn(handler)
            return

        # If nothing else handled this request, redirect to login

        self.OnRedirectLogin(handler)

    def OnRedirectLogin(self, handler):
        # generate 303 return sending people to GET the /login endpoint

        lStr = [
                '<html>',
                '<body>',
                '<h1>Oops!</h1>',
                '<p>Something went wrong. You should be redirected, but if not, try to <a href="/login">log in</a>.</p>',
                '</body>',
                '</html>',
            ]
        strOut = '\n'.join(lStr)
        abOut = strOut.encode()

        handler.send_response(303)
        handler.send_header('Location', '/login')
        handler.send_header('Content-Length', len(abOut))
        handler.end_headers()

        handler.wfile.write(abOut)

    def OnCreateError(self, handler, strErr):
        """Provide error page to the user in response to bad user create attempts"""

        lStr = [
                '<html>',
                '<head><title>Create User Error</title></head>',
                '<body>',
                '<h1>Oops!</h1>',
                '<p>The user could not be created: {err}</p>'.format(err=strErr),
                '<p>You could <a href="/create">try again</a> if you wish.</p>',
                '<p>You could <a href="/login">log in</a> if you remember your username and password.</p>',
                '</body>',
                '</html>',
            ]
        strOut = '\n'.join(lStr)
        abOut = strOut.encode()

        handler.send_response(200)
        handler.send_header('Content-Length', len(abOut))
        handler.end_headers()

        handler.wfile.write(abOut)

    def OnPostCreate(self, handler, dPost):
        """Handles attempts to create a new account"""

        # filter out invalid usernames

        uid = dPost.get('login')
        if uid is None or uid == '':
            self.OnCreateError(handler, "Invalid username")
            return

        setCh = set(list(uid))
        setChValid = set(list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'))

        if setCh & setChValid != setCh:
            self.OnCreateError(handler, "Invalid characters in username")
            return

        # filter out duplicated usernames

        sessionPrev = self.m_group.SessionFromUid(uid)
        if sessionPrev is not None:
            self.OnCreateError(handler, "User already exists")
            return

        pwd1 = dPost.get('pass')
        pwd2 = dPost.get('pass2')

        # reject illegal passwords

        if pwd1 is None or pwd1 == '':
            self.OnCreateError(handler, "Invalid password")
            return

        if len(pwd1) < 4:
            self.OnCreateError(handler, "Password is too short")
            return

        # reject non-matching passwords

        if pwd1 != pwd2:
            self.OnCreateError(handler, "Passwords do not match")
            return

        # create a session with the given user/password

        session = self.m_group.SessionCreate()
        session.SetCreds(uid, pwd1)
        session.SetPath(os.path.join(self.m_group.m_pathDir, "{u}.session".format(u=uid)))
        session.SetRoomCur(self.m_rooms.m_roomStart)

        strErr = session.StrErrors()
        if strErr:
            self.OnCreateError(handler, "Error creating user: " + strErr)
            return

        # stamp the session to disk and add to the group

        session.Save()
        self.m_group.AddSession(session)

        # pretend that the user just logged in

        dPost = {
                'login' : uid,
                'pass' : pwd1,
            }

        self.OnPostLogin(handler, dPost)

    def OnGetCreate(self, handler):
        """Page to allow a new player to create a new account"""

        lStr = [
                '<html>',
                '<head><title>New Player</title></head>',
                '<body>',
                '<h1>Create New Player</h1>',
                '<p>If you would like to play web-adventure you will need to create an account. Please fill in the following fields.</p>',
                '<form action="/create" method="post">',
                    '<label for="login">Username:</label>',
                    '<input type="text" id="login" name="login" autocomplete="off" autofocus maxlength=20 required size=20/>',
                    '<br/>',
                    '<label for="pass">Password:</label>',
                    '<input type="password" id="pass" name="pass" autocomplete="off" autofocus maxlength=20 required size=20/>',
                    '<br/>',
                    '<label for="pass2">Password (re entry):</label>',
                    '<input type="password" id="pass2" name="pass2" autocomplete="off" autofocus maxlength=20 required size=20/>',
                    '<br/>',
                    '<input type="submit" value="Go"/>',
                '</form>',
                '</body>',
                '</html>',
            ]
        strOut = '\n'.join(lStr)
        abOut = strOut.encode()

        handler.send_response(200)
        handler.send_header('Content-Length', len(abOut))
        handler.end_headers()
        handler.wfile.write(abOut)

    def OnPostLogin(self, handler, dPost):
        """Handle the submit end of attempting to log in"""

        handler.send_response(200)
        handler.end_headers()
        
        lStr = []
        lStr.append('<html>')
        lStr.append('<body>')

        # Check if we have a user and password that match. To avoid timing attacks we check
        #  a session, even if we don't have one with a matching UID.

        sessionCheck = self.m_group.SessionFromUid(dPost.get('login'))
        if sessionCheck is None:
            sessionCheck = self.m_group.SessionCreate()

        if not sessionCheck.FMatchesCreds(dPost.get('pass')):
            lStr.append('<h1>Invalid Login</h1>')
            lStr.append('<p>The user or password you supplied do not match our records.</p>')
            lStr.append('<p>You could try to <a href="/login">login again</a> if you would like.</p>')
            lStr.append('<p>You could also try to <a href="/create">create a new account</a> instead.</p>')
        else:
            # for safety, wipe any other sids that are pointing to this session

            lSidRemove = []
            for sidOther, session in self.m_mpSidSession.items():
                if session == sessionCheck:
                    lSidRemove.append(sidOther)

            for sidOther in lSidRemove:
                del self.m_mpSidSession[sidOther]

            # generate sid and map it to this session

            sid = self.SidGenerate()
            self.m_mpSidSession[sid] = sessionCheck

            # send back welcome page

            lStr.append('<h1>Login Successful!</h1>')
            lStr.append('<p>You logged in! You win!</p>')
            lStr.append('<p>Clearly this does not actually make sense to display.</p>')
            lStr.append('<p>It is possible the correct flow here is to do OnRoom...?</p>')
            lStr.append('<p>At any rate...</p>')
            lStr.append('<form action="/room" method="post">')
            # This hidden input will need to be in basically all room posts...do we need to formalize/remember/whatever?
            lStr.append('<input type="hidden" name="sid" id="sid" value="{sid}"/>'.format(sid=sid))
            lStr.append('<input type="submit" value="Continue Your Adventure"/>')
            lStr.append('</form>')

        lStr.append('</body>')
        lStr.append('</html>')

        for str0 in lStr:
            handler.wfile.write(str0.encode())
            handler.wfile.write('\n'.encode())

    def OnPostRoom(self, handler, dPost):
        """Handle the submit end of attempting to access a room"""

        # deal with missing/incorrect sessions (has to handle in room logic...sigh...)

        # TODO redirect to login here is fairly unfriendly, should consider producing an
        #  error page of some kind that has maybe helpful data instead

        if 'sid' not in dPost:
            handler.log_error('No sid in post data')
            self.OnRedirectLogin(handler)
            return

        sid = dPost['sid']
        if not self.FIsValidSid(sid):
            handler.log_error('Invalid sid "{sid}" given'.format(sid=sid))
            self.OnRedirectLogin(handler)
            return

        session = self.m_mpSidSession.get(sid, None)
        if session is None:
            handler.log_error('Sid "{sid}" valid but no session?'.format(sid=sid))
            self.OnRedirectLogin(handler)
            return

        # do the actual work, on the session, to possibly adjust and then display the current room

        session.TryAdjustRoom(dPost, handler)
        room = session.RoomCur()
        if room is None:
            handler.log_error('Sid "{sid}" session "{uid}" had no current room'.format(sid=sid, uid=session.m_uid))
            self.OnRedirectLogin(handler)
            return

        session.RenderRoomCur(sid, handler)

        if session.m_fIsDirty:
            session.Save()

    def OnGetLogin(self, handler):
        """Provide the initial login page"""

        lStr = [
                '<html>',
                '<head><title>Login</title></head>',
                '<body>',
                '<h1>Welcome</h1>',
                '<p>You have found your way to web-adventure, and in order to continue, you need to...</p>',
                '<h1>Login</h1>',
                '<p>Log in to an existing account if you have one. Please do not resue passwords!</p>',
                '<form action="/login" method="post">',
                    '<label for="login">Username:</label>',
                    '<input type="text" id="login" name="login" autocomplete="off" autofocus maxlength=20 required size=20/>',
                    '<br/>',
                    '<label for="pass">Password:</label>',
                    '<input type="password" id="pass" name="pass" autocomplete="off" autofocus maxlength=20 required size=20/>',
                    '<br/>',
                    '<input type="submit" value="Go"/>',
                '</form>',
                '<h1>Create</h1>',
                '<p><a href="/create">Create a new account</a> if you do not already have one!</p>',
                # TODO maybe also have a little about page?
                '</body>',
                '</html>',
            ]
        strOut = '\n'.join(lStr)
        abOut = strOut.encode()

        handler.send_response(200)
        handler.send_header('Content-Length', len(abOut))
        handler.end_headers()
        handler.wfile.write(abOut)

    def OnGetFavicon(self, handler):
        """Favicon handling"""

        handler.send_response(404)
        handler.end_headers()

    def OnGetImage(self, handler):
        """Support providing images"""

        # Get the relative path to the image (will be relative to the data directory)

        strPathImage = handler.path[len(self.s_strPathImage) + 1:]

        # See if the image exists -- if not, that's a 404

        if not os.path.exists(strPathImage):
            handler.send_response(404)
            handler.end_headers()
            return

        # Determine particular image type -- we support png, jpeg, and gif for now

        s_mpStrExtStrContent = {
                '.gif' : 'image/gif',
                '.jpeg' : 'image/jpeg',
                '.jpg' : 'image/jpeg',
                '.png' : 'image/png',
            }

        strExt = os.path.splitext(strPathImage)[-1]
        strContent = s_mpStrExtStrContent.get(strExt.lower(), None)

        if strContent is None:
            handler.send_response(404)
            handler.end_headers()
            return

        # Load up the image data

        # BB (davidm) any kind of error handling we want here?

        with open(strPathImage, 'rb') as fileIn:
            aBImage = fileIn.read()

        # Send a successful response with the image content

        handler.send_response(200)
        handler.send_header('Content-type', strContent)
        handler.send_header('Content-Length', len(aBImage))
        handler.end_headers()
        handler.wfile.write(aBImage)

    def FormExample(self, handler, lPart):
        """Example of doing form stuff, useful while experimenting with things"""

        # show login form
        handler.send_response(200)
        handler.end_headers()
        handler.wfile.write('''<html>
                <head><title>Login</title></head>
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
