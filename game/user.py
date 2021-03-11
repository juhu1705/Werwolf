evils = ['Werwolf']


class User:

    def __init__(self, username, sid):
        self.username = username
        self.sid = sid
        self.room = None
        self.role = ""
        self.dead = False
        self.alive = False
        self.loved_user = None
        self.is_mayor = False

    def join_room(self, room):
        if self.room is not None:
            self.room.del_user(self)
        self.room = room

    def leave(self):
        if self.room is not None:
            self.room.del_user(self)

    def reset(self):
        self.role = ""
        self.dead = False
        self.alive = True
        self.loved_user = None

    def kill(self):
        self.dead = True

        if self.loved() and not self.loved_user.dead:
            self.loved_user.kill()

    def is_evil(self):
        if self.dead:
            return False
        if evils.__contains__(self.role):
            return True
        elif self.loved() and evils.__contains__(self.loved_user.role):
            return True
        return False

    def loved(self):
        return self.loved_user is not None
