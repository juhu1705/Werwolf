evils = ['Werwolf']


class User:

    def __init__(self, username, sid):
        self.username = username
        self.sid = sid
        self.room = None
        self.role = ""
        self.dead = False
        self.alive = False
        self.is_mayor = False
        self.sounds_active = False

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

    def kill(self):
        self.dead = True

    def is_evil(self):
        if self.dead:
            return False
        if evils.__contains__(self.role):
            return True
        return False
