# session-related machinery (tracks player state)

import glob
import hashlib
import secrets
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
        self.m_mpVarVal = {}
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
        self.m_mpVarVal = doc.get('vars')
        self.m_fIsDirty = False

    def Save(self):
        """Serialize out this session as a yaml document to its source path"""

        # TODO: is there a better way here? can we fake that we're a dict instead somehow?

        dSelf = {}
        dSelf['uid'] = self.m_uid
        dSelf['pwd'] = self.m_pwd
        dSelf['room'] = self.m_room.m_name
        dSelf['vars'] = self.m_mpVarVal

        tmp = self.m_path + ".new"
        with open(tmp, 'w') as fileOut:
            yaml.serialize(dSelf, fileOut)

        old = self.m_path + '.old'
        if os.path.exists(old):
            os.remove(old)

        os.rename(self.m_path, old)
        os.rename(tmp, self.m_path)

        self.m_fIsDirty = False

    def StrErrors(self):
        """Validate this session, and if it has problems, return a string explaining the issues"""

        lStrErr = []

        if self.m_uid is None:
            lStrErr.append("UID is missing")

        if self.m_path is None:
            lStrErr.append("UID {u} missing its path".format(u=self.m_uid))

        if self.m_roomSaved is None:
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
        dk = hashlib.pbkdf2_hmac(self.s_algoHash, pwd, salt, self.s_cIterHash)
        hashCheck = dk.hex()

        return hashSelf == hashCheck

    def SetCreds(self, uid, pwd):
        """Sets the creds for this session object directly (assumes it is valid to do so)"""

        self.m_uid = uid
        salt = secrets.token_hex(nbytes=32)
        dk = hashlib.pbkdf2_hmac(self.s_algoHash, pwd, salt, self.s_cIterHash)
        self.m_pwd = ','.join([dk.hex(), salt])
        self.m_fIsDirty = True

    def SetPath(self, path):
        """Sets up the path for where this session should be saved"""

        self.m_path = path
        self.m_fIsDirty = True


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
