import random
import time

from flask_socketio import emit


role_descriptions = {'Werwolf': 'In der Nacht wachst du auf und wählst mit den anderen Werwölfen ein Opfer aus, '
                                'erst wenn ihr alle Dorfbewohner umgebracht habt habt ihr gewonnen!',
                     'Hexe': 'Du besitzt zwei Zaubertränke für das gesammte Spiel, der einen kann heilen der andere '
                             'kann töten. Am Ende der Nacht wirst du gefragt, ob du einen deiner Tränke benutzen '
                             'willst.',
                     'Seherin': 'Du hast die Gabe nachts in deiner Glaskugel die Identität deiner Mitspieler zu '
                                'erfahren, doch leider kannst du dich jede Nacht nur auf einen anderen Spieler '
                                'konzentrieren.',
                     'Armor': 'Du besitzt wahrlich die Macht der Liebe. Zu Beginn des Spiels wählst du ein '
                              'Liebespaar, das für den Rest des Spiels nicht mehr ohne den Partner existieren kann.',
                     'Jäger': 'Auf der Jagt hast du gelernt so schnell zu reagieren, das du selbst im Sterben noch '
                              'eine Person tödlich verletzen kannst.',
                     'Beschützer': 'Jede Nacht wählst du einen Mitspieler den du beschützen willst, dieser Spieler '
                                   'kann in der Nacht nicht sterben.'}


def send_userdata(user):
    emit('set_role', 'Rolle: ' + user.role, room=user.sid, broadcast=False)
    emit('set_description', 'Beschreibung: ' + role_descriptions.get(user.role), room=user.sid, broadcast=False)


class Room:

    def __init__(self, user, room_name):
        self.room_name = room_name
        self.admin = user

        self.game_users = []

        self.alive = []
        self.dead = []
        self.master = None

        self.wolves_count = 2
        self.witches_count = 1
        self.searchers_count = 1
        self.armor_count = 1
        self.hunter_count = 0
        self.protector_count = 0
        self.wolves_choose = None
        self.started = False
        self.deletable = False
        self.votes = {}
        self.wait_for_votes = 0
        self.actual_step = ""

        self.show_settings(user=user)
        self.add_user(new_user=user)

    def show_settings(self, user):
        print('Load settings ' + user.username + " " + user.sid)
        emit('show_settings', 'Einstellungen:', room=user.sid)
        emit('append_setting', '<div class="line"><div>Werwölfe:</div><input class="setting" type="number" '
                               'name="wolves_count" id="wolves_count" value="' +
             str(self.wolves_count) + '" '
                                      'readonly="readonly"></input></div>',
             room=user.sid)
        emit('append_setting',
             '<div class="line"><div>Hexen:</div><input class="setting" type="number" name="witches_count" '
             'id="witches_count" value="' + str(
                 self.witches_count) + '" readonly="readonly"></input></div>', room=user.sid)
        emit('append_setting',
             '<div class="line"><div>Seherin:</div><input class="setting" type="number" name="searchers_count" '
             'id="searchers_count" value="' + str(
                 self.searchers_count) + '" readonly="readonly"></input></div>', room=user.sid)
        emit('append_setting',
             '<div class="line"><div>Jäger:</div><input class="setting" type="number" name="hunter_count" '
             'id="hunter_count" value="' + str(
                 self.hunter_count) + '" readonly="readonly"></input></div>', room=user.sid)
        emit('append_setting',
             '<div class="line"><div>Beschützer:</div><input class="setting" type="number" name="protector_count" '
             'id="protector_count" value="' + str(
                 self.protector_count) + '" readonly="readonly"></input></div>', room=user.sid)
        emit('append_setting',
             '<div class="line"><div>Armor:</div><input class="setting" type="number" name="armor_count" '
             'id="armor_count" value="' + str(
                 self.armor_count) + '" readonly="readonly"></input></div>', room=user.sid)

        if self.admin is user:
            emit('show_admin_room', '', room=user.sid)

    def add_user(self, new_user):
        emit('display_text', "Spieler: ", room=new_user.sid)
        emit('display_header', "Raum: " + self.room_name, room=new_user.sid)

        for user in self.game_users:
            emit('append_text', new_user.username, room=user.sid)
            emit('append_text', user.username, room=new_user.sid)

        self.game_users.append(new_user)
        new_user.room = self
        emit('append_text', new_user.username, room=new_user.sid)
        emit('show_room', "", room=new_user.sid, broadcast=False)
        emit('set_room_name', "Raum: " + self.room_name, room=new_user.sid, broadcast=False)
        print('Load settings ' + new_user.username + " " + new_user.sid)

    def del_user(self, user):
        if self.alive.__contains__(user):
            self.alive.remove(user)
        if self.dead.__contains__(user):
            self.dead.remove(user)
        self.game_users.remove(user)

        if user is self.admin:
            if self.game_users.__len__() > 0:
                self.admin = self.game_users[0]
            else:
                self.deletable = True
        self.check_for_winner()

    def check_for_winner(self):
        wolves_count = 0
        villager_count = 0

        for user in self.alive:
            if user.is_evil():
                wolves_count += 1
            else:
                villager_count += 1

        if wolves_count == 0 and villager_count == 0:
            self.display_end(header='Kein Sieger', text='Alle Spieler sind tragisch gestorben!')
        elif wolves_count > 0 and villager_count == 0:
            self.display_end(header='Die Werwölfe haben gewonnen!',
                             text='Die Dorfbewohner haben die wahren Feinde ihres Dorfes wohl erst zu spät erkannt!')
        elif wolves_count == 0 and villager_count > 0:
            self.display_end(header='Die Dorfbewohner haben gewonnen!',
                             text='Siegreich stehen sie um den Kadawer des letzten Wolfes und sind froh endlich '
                                  'wieder in Ruhe schlafen zu können!')
        elif wolves_count == 1 and villager_count == 1:
            wolves = None
            villager = None
            for user in self.alive:
                if user.is_evil():
                    wolves = user
                else:
                    villager = user
            if wolves is not None and villager is not None:
                if wolves.loved() and wolves.loved_user is villager:
                    self.display_end('Das Liebespaar hat gewonnen!', 'Listig haben sie gemeinsam alle Werwölfe und '
                                                                     'Dorfbewohner hintergangen und leben nun in '
                                                                     'Liebe allein bis ans Ende ihrer Tage.')

    def display_end(self, header, text):
        for user in self.game_users:
            emit('', '')

    def start_game(self):
        self.started = True

        users = random.sample(self.game_users, len(self.game_users))
        for i in range(0, self.wolves_count):
            if len(users) > i:
                users.pop(0).role = 'Werwolf'
            else:
                break

        for i in range(0, self.searchers_count):
            if len(users) > i:
                users.pop(0).role = 'Seherin'
            else:
                break

        for i in range(0, self.witches_count):
            if len(users) > i:
                users.pop(0).role = 'Hexe'
            else:
                break

        for i in range(0, self.armor_count):
            if len(users) > i:
                users.pop(0).role = 'Armor'
            else:
                break

        for i in range(0, self.hunter_count):
            if len(users) > i:
                users.pop(0).role = 'Jäger'
            else:
                break

        for i in range(0, self.protector_count):
            if len(users) > i:
                users.pop(0).role = 'Beschützer'
            else:
                break

        for user in users:
            user.role = 'Dorfbewohner'

        self.alive = self.game_users.copy()

        for user in self.alive:
            send_userdata(user=user)

    def get_players(self):
        to_return = ""
        print(to_return)

        for player in self.game_users:
            name = player.username
            print(name)
            to_return += """<div class="option """ + name + """">
                    <input type="radio" class="radio" id="sidebar-""" + name + """" name="category">
                    <label for="sidebar-""" + name + """">""" + name + """
                    </label>
                    </div>"""

        return to_return

    def settings(self, wolves, witches, searchers, armors, hunters, protectors):
        self.wolves_count = int(wolves)
        self.witches_count = int(witches)
        self.searchers_count = int(searchers)
        self.armor_count = int(armors)
        self.hunter_count = int(hunters)
        self.protector_count = int(protectors)

        if self.armor_count > 1:
            self.armor_count = 1
        if self.wolves_count < 1:
            self.wolves_count = 1
        if self.armor_count < 0:
            self.armor_count = 0
        if self.witches_count < 0:
            self.witches_count = 0
        if self.searchers_count < 0:
            self.searchers_count = 0
        if self.hunter_count < 0:
            self.hunter_count = 0
        if self.protector_count < 0:
            self.protector_count = 0

        for user in self.game_users:
            self.show_settings(user=user)

    def kill(self, user):
        if self.game_users.__contains__(user) and self.alive.__contains__(user):
            if self.master is user:
                if len(self.alive) > 0:
                    self.master = self.alive[random.randint(0, self.alive.__len__())]
            if user.role == 'Jäger':

                return

            self.dead.append(user)
            self.alive.remove(user)

    def handle_vote(self, user, vote_for):
        self.votes[user] = vote_for
        return

    def playing(self):
        while True:
            if self.wait_for_votes is len(self.votes):
                self.next_step()
            time.sleep(200)

    def next_step(self):
        if self.actual_step == '':
            self.actual_step = 'start'
        elif self.actual_step == 'start':
            self.actual_step = 'armor1'
        elif self.actual_step == 'armor1':
            self.actual_step = 'armor2'
        elif self.actual_step == 'armor2':
            self.actual_step = 'loved'
        elif self.actual_step == 'loved':
            self.actual_step = 'searcher'
        elif self.actual_step == 'searcher':
            self.actual_step = 'protector'
        elif self.actual_step == 'protector':
            self.actual_step = 'wolves'
        elif self.actual_step == 'wolves':
            self.actual_step = 'witch1'
        elif self.actual_step == 'witch1':
            self.actual_step = 'witch2'
        elif self.actual_step == 'witch2':
            self.actual_step = 'day'
        elif self.actual_step == 'day':
            if self.master is None:
                self.actual_step = 'vote_master'
            else:
                self.actual_step = 'vote'
        elif self.actual_step == 'vote_master':
            self.actual_step = 'display_master'
        elif self.actual_step == 'display_master':
            self.actual_step = 'vote'
        elif self.actual_step == 'vote':
            self.actual_step = 'day_end'
        elif self.actual_step == 'day_end':
            self.actual_step = 'searcher'
