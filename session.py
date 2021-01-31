# session-related machinery (tracks player state)

import collections
import glob
import hashlib
import os
import random
import secrets
import server
import yaml

class Session:
    """Information about the state for a single player"""

    s_cIterHash = 100000
    s_algoHash = 'sha256'

    def __init__(self):
        self.m_uid = None
        self.m_pwd = 'abcdefg,0123456789ABCDEF'
        self.m_path = None
        self.m_room = None
        self.m_roomSaved = None
        self.m_mpVarVal = collections.defaultdict(int)  # auto-create keys with 0 value
        self.m_fIsDirty = False

    def Load(self, path):
        """Serialize in this session from a file containing a yaml document"""

        self.m_path = path

        with open(path, 'r') as fileIn:
            doc = yaml.safe_load(fileIn)

        if doc is None:
            return

        self.m_uid = doc.get('uid')
        self.m_pwd = doc.get('pwd')
        self.m_roomSaved = doc.get('room')  # NOTE string, not room
        self.m_mpVarVal = collections.defaultdict(int)
        self.m_mpVarVal.update(doc.get('vars'))
        self.m_fIsDirty = False

    def Save(self):
        """Serialize out this session as a yaml document to its source path"""

        # TODO: is there a better way here? can we fake that we're a dict instead somehow?

        dSelf = {}
        dSelf['uid'] = self.m_uid
        dSelf['pwd'] = self.m_pwd
        dSelf['room'] = self.m_room.m_name
        dSelf['vars'] = dict(self.m_mpVarVal)

        tmp = self.m_path + ".new"
        with open(tmp, 'w') as fileOut:
            yaml.dump(dSelf, fileOut)

        old = self.m_path + '.old'
        if os.path.exists(old):
            os.remove(old)

        if os.path.exists(self.m_path):
            os.rename(self.m_path, old)

        os.rename(tmp, self.m_path)

        if os.path.exists(old):
            os.remove(old)

        self.m_fIsDirty = False

    def StrErrors(self):
        """Validate this session, and if it has problems, return a string explaining the issues"""

        lStrErr = []

        if self.m_uid is None:
            lStrErr.append("UID is missing")

        if self.m_path is None:
            lStrErr.append("UID {u} missing its path".format(u=self.m_uid))

        if self.m_roomSaved is None and self.m_room is None:
            lStrErr.append("UID {u} missing its room".format(u=self.m_uid))

        if not isinstance(self.m_mpVarVal, dict):
            lStrErr.append("UID {u} has non-dictionary vars".format(u=self.m_uid))

        # TODO: other things to check?

        return '\n'.join(lStrErr)

    def RoomCur(self):
        return self.m_room

    def SetRoomCur(self, room):
        self.m_room = room
        self.m_fIsDirty = True

    def Var(self, var):
        return self.m_mpVarVal.get(var, None)

    def SetVar(self, var, value):
        self.m_mpVarVal[var] = value
        self.m_fIsDirty = True

    def FMatchesCreds(self, pwd):
        """Returns True if the given user/password combo matches this session"""

        hashSelf, salt = self.m_pwd.split(',')
        dk = hashlib.pbkdf2_hmac(self.s_algoHash, pwd.encode(), salt.encode(), self.s_cIterHash)
        hashCheck = dk.hex()

        return hashSelf == hashCheck

    def SetCreds(self, uid, pwd):
        """Sets the creds for this session object directly (assumes it is valid to do so)"""

        self.m_uid = uid
        salt = secrets.token_hex(nbytes=32)
        dk = hashlib.pbkdf2_hmac(self.s_algoHash, pwd.encode(), salt.encode(), self.s_cIterHash)
        self.m_pwd = ','.join([dk.hex(), salt])
        self.m_fIsDirty = True

    def SetPath(self, path):
        """Sets up the path for where this session should be saved"""

        self.m_path = path
        self.m_fIsDirty = True

    def StrFormatSmart(self, strIn):
        """Do "smart" formatting of strIn (expected to be a format string) vs. the contents of
        mp_mpVarValue. In particular, deal with cases where the format string talks about items
        that don't have keys in the var map."""

        # NOTE: I attempted to deal with this by using defaultdict, but unfortunately, the ** expansion
        #  that is used to convert dictionaries into keyword expansions of course doesn't default expand
        #  every possible keyword out, so defaultdict didn't actually help with that case at all. Since
        #  there isn't a way to pass a "smart" dictionary like that into str.format(), we deal with that
        #  ourselves here.

        # TODO: be smarter/safer about dealing with this stuff -- doing the simple version where we detect
        #  problems and fix them, rather than attempting to "correctly" parse the format syntax up front

        cIter = 100
        while cIter > 0:
            cIter -= 1
            try:
                return strIn.format(**self.m_mpVarVal)
            except KeyError as ke:
                # TODO: Is this safe/guaranteed?
                self.m_mpVarVal[ke.args[0]] = 0

        return "<could not format>"

    def RunChanges(self, room):
        """Apply any changes for the given room to this session"""

        for change in room.LChange():
            op = change[0]
            self.m_fIsDirty = True

            if op == 'set':
                # set a session variable to a fixed value
                var = change[1]
                value = change[2]
                self.m_mpVarVal[var] = value

            elif op == 'add':
                # add a fixed value to a session variable
                var = change[1]
                value = change[2]
                # TODO: cleaner/more useful handling of invalid/missing/non-numeric values?
                try:
                    self.m_mpVarVal[var] = self.m_mpVarVal.get(var, 0) + int(value)
                except:
                    pass

            elif op == 'addrand':
                # add a random ranged value to a session variable
                var = change[1]
                low = change[2]
                high = change[3]
                # TODO: cleaner/more useful handling of invalid/missing/non-numeric values?
                try:
                    self.m_mpVarVal[var] = self.m_mpVarVal.get(var, 0) + random.randint(low, high)
                except:
                    pass

            elif op == 'setrand':
                # set a session variable to a ranged randomized value
                var = change[1]
                low = change[2]
                high = change[3]
                self.m_mpVarVal[var] = random.randint(low, high)

    def TryAdjustRoom(self, dPost, handler):
        """Handles any commands in dPost that could adjust the current room, etc."""

        # No adjustment if we're not asked to go anywhere

        if 'dest' not in dPost:
            return

        dest = dPost['dest']

        # NOTE it appears that spaces get turned into plus signs on form submit, so undo that here

        dest = dest.replace('+', ' ')

        # bad coupling here

        rooms = server.g_server.m_rooms
        roomNext = rooms.Room(dest)

        if roomNext:
            self.RunChanges(roomNext)
            self.SetRoomCur(roomNext)

        # TODO do we need handling for the case where the room doesn't exist? just leaving the player there is weird, I guess?

    def FEvaluateCond(self, cond):
        """Returns True if the given condition evaluates to True, and False if not"""
        
        if isinstance(cond, dict):
            if len(cond) != 1:
                return false

            if 'and' in cond:
                lCond = cond['and']
            elif 'or' in cond:
                lCond = cond['or']
            else:
                # TODO: logging?
                return False

            if not isinstance(lCond, list):
                # TODO: logging?
                return False

            lF = [self.FEvaluateCond(x) for x in lCond]
            setF = set(lF)

            if 'and' in cond:
                return True in setF and False not in setF
            elif 'or' in cond:
                return True in setF
            else:
                # TODO: logging?
                return False

        elif isinstance(cond, list):
            # should be a three part list: op, var, value

            if len(cond) != 3:
                # TODO: logging?
                return False

            op = cond[0]
            var = cond[1]
            value = cond[2]

            if 'var' in op:
                # expand value by looking it up
                value = self.m_mpVarVal.get(value, 0)

            if op == 'eq' or op == 'eqvar':
                return self.m_mpVarVal.get(var, 0) == int(value)
            elif op == 'gt' or op == 'gtvar':
                return self.m_mpVarVal.get(var, 0) > int(value)
            elif op == 'lt' or op == 'ltvar':
                return self.m_mpVarVal.get(var, 0) < int(value)
            elif op == 'ne' or op == 'nevar':
                return self.m_mpVarVal.get(var, 0) != int(value)
            else:
                # TODO: logging?
                return False

        # TODO: logging?
        return False

    def FShouldProvideExit(self, exit):
        """Returns True if the exit should be provided, False if the exit should not be provided"""

        # exits that do not have a condition should always be provided

        if 'cond' not in exit:
            return True

        return self.FEvaluateCond(exit['cond'])

    def LStrTryAddExit(self, exit, sid):
        """Returns the list of form strings for the exit if it is legal, and empty list otherwise"""

        # skip invalid exits (no name or verb)

        if 'name' not in exit:
            return []

        if 'verb' not in exit:
            return []

        if not self.FShouldProvideExit(exit):
            return []

        # NOTE that by using a separate form for each exit, we can thus include the index as a different
        #  value so that we can distinguish which exit was selected

        lStr = []
        lStr.append('<form action="/room" method="post">')
        lStr.append('<input type="hidden" name="sid" id="sid" value="{sid}"/>'.format(sid=sid))
        lStr.append('<input type="hidden" name="cur" id="cur" value="{cur}"/>'.format(cur=self.RoomCur().m_name))
        lStr.append('<input type="hidden" name="dest" id="dest" value="{dest}"/>'.format(dest=exit['name']))
        lStr.append('<input type="submit" value="{verb}"/>'.format(verb=self.StrFormatSmart(exit['verb'])))
        lStr.append('</form>')

        return lStr

    def RenderRoomCur(self, sid, handler):
        """Renders the current room, with appropriate settings, etc., to the given handler"""
        
        # TODO should cache contents for reload scenarios...maybe? maybe skip adjust if we find a reload?

        room = self.RoomCur()

        lStr = []
        lStr.append('<html>')
        lStr.append('<head>')
        lStr.append('<title>{name}</title>'.format(name=room.m_name))
        lStr.append('</head>')
        lStr.append('<body>')
        lStr.append('<h1>{name}</h1>'.format(name=room.m_name))

        # Note that we pass the var/val dictionary here for formatting purposes in case the
        #  description wants to include things about current session state

        lStr.append('<p>{desc}</p>'.format(desc=self.StrFormatSmart(room.m_desc)))

        for exit in room.LExit():
            lStr.extend(self.LStrTryAddExit(exit, sid))

        # TODO add generic links for logout, about, any others here

        lStr.append('</body>')
        lStr.append('</html>')

        abOut = '\n'.join(lStr).encode()

        handler.send_response(200)
        handler.send_header('Content-Length', len(abOut))
        handler.end_headers()

        handler.wfile.write(abOut)

class Group:
    """All of the sessions known by the system"""

    def __init__(self):
        self.m_mpUidSession = {}
        self.m_pathDir = None

    def Load(self, pathDir):
        """load all files from the directory, assuming they're sessions"""

        self.m_pathDir = pathDir

        for path in glob.glob("{p}/*".format(p=pathDir)):
            session = Session()
            session.Load(path)
            strErrors = session.StrErrors()
            if strErrors:
                print("Session from {p} had errors:\n{e}".format(p=path, e=strErrors))
            elif session.m_uid in self.m_mpUidSession:
                print("Session {u} defined multiply (new {pNew}, prev {pOld})".format(
                        u=session.m_uid,
                        pNew=path,
                        pOld=self.m_mpUidSession[session.m_uid].m_path))
            else:
                self.m_mpUidSession[session.m_uid] = session

    def InitRooms(self, rooms):
        """initialize actual room references for each session (typically after loading)"""

        for session in self.m_mpUidSession.values():
            room = rooms.Room(session.m_roomSaved)
            session.SetRoomCur(room)

    def SessionFromUid(self, uid):
        return self.m_mpUidSession.get(uid, None)

    def SessionCreate(self):
        """Generate untracked "blank" session"""
        return Session()

    def LSession(self):
        """Return list (or generator) of sessions in the group"""

        return self.m_mpUidSession.values()

    def AddSession(self, session):
        """Adds the given session to the group"""

        self.m_mpUidSession[session.m_uid] = session

if __name__ == '__main__':
    # test driver for session stuff
    group = Group()
    group.Load('sampleSessions')
    print("Finished loading sample sessions; errors will be listed above if any")
