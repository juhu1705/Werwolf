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
                     'Amor': 'Du besitzt wahrlich die Macht der Liebe. Zu Beginn des Spiels wählst du ein '
                              'Liebespaar, das für den Rest des Spiels nicht mehr ohne den Partner existieren kann.',
                     'Jäger': 'Auf der Jagt hast du gelernt so schnell zu reagieren, das du selbst im Sterben noch '
                              'eine Person tödlich verletzen kannst.',
                     'Beschützer': 'Jede Nacht wählst du einen Mitspieler den du beschützen willst, dieser Spieler '
                                   'kann in der Nacht nicht sterben.',
                     'Dorfbewohner': 'Du lebst im Dorf und bemerkst die seltsamen Vorkommnisse in der Nacht, '
                                     'deine Aufgabe ist es die Werwölfe zu finden und am Tag in der Abstimmung zu '
                                     'entarnen und dann zu lynchen.'}

role_imgs = {'Werwolf': '#wolf_img', 'Hexe': '#witch_img', 'Seherin': '#searcher_img', 'Amor': '#amor_img',
             'Jäger': '#hunter_img', 'Beschützer': '#guard_img', 'Dorfbewohner': '#villager_img'}


def send_userdata(user):
    emit('set_role', 'Rolle: ' + user.role, room=user.sid, broadcast=False)
    emit('set_explanation', 'Beschreibung: ' + role_descriptions.get(user.role), room=user.sid, broadcast=False)
    emit('set_role_img', role_imgs.get(user.role), room=user.sid, broadcast=False)


def pack_voteable_player(name):
    return """<div class="option">
                        <input type="radio" class="radio" id="sidebar-""" + str(hash(name)) + """" name="category">
                        <label for="sidebar-""" + str(hash(name)) + """">""" + name + """</label></div>"""


def get_witch_votes():
    return """<div class="option Ja"><input type="radio" class="radio" id="sidebar-Ja" name="category"><label for="sidebar-Ja">Ja</label></div><div class="option Nein"><input type="radio" class="radio" id="sidebar-Nein" name="category"><label for="sidebar-Nein">Nein</label></div>"""


def make_voteable_player_list(voteable_players):
    to_return = ""
    for player in voteable_players:
        to_return += pack_voteable_player(player.username)
    return to_return


def is_user_contained(players, user):
    for player in players:
        if user.username == player.username:
            return True
    return False


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
        self.amor_count = 1
        self.hunter_count = 0
        self.protector_count = 0
        self.wolves_choose = None
        self.started = False
        self.deletable = False
        self.votes = {}
        self.wait_for_votes_from = []
        self.actual_step = ""
        self.allow_tie = True
        self.loved1 = None
        self.loved2 = None
        self.protected = None
        self.to_kill = None
        self.killed_due_night = []
        self.used_heal = []
        self.used_kill = []
        self.killed_list = []
        self.before_hunter_kill = ''
        self.hunter_killed = []
        self.lynched = None

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
             '<div class="line"><div>Amor:</div><input class="setting" type="number" name="amor_count" '
             'id="amor_count" value="' + str(
                 self.amor_count) + '" readonly="readonly"></input></div>', room=user.sid)

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
        self.show_settings(user=new_user)

    def get_user_from_name(self, username):
        for player in self.game_users:
            if player.username == username:
                return player
        return None

    def del_user(self, user):
        if is_user_contained(self.alive, user):
            self.alive.remove(user)
        if is_user_contained(self.dead, user):
            self.dead.remove(user)
        self.game_users.remove(user)

        if user is self.admin:
            if self.game_users.__len__() > 0:
                self.admin = self.game_users[0]
            else:
                self.deletable = True
        if self.started:
            self.check_for_winner()
        elif not self.deletable:
            for player in self.game_users:
                emit('display_text', "Spieler: ", room=player.sid)
                emit('display_header', "Raum: " + self.room_name, room=player.sid)

                for user in self.game_users:
                    emit('append_text', user.username, room=player.sid)

                emit('show_room', "", room=player.sid, broadcast=False)
                emit('set_room_name', "Raum: " + self.room_name, room=player.sid, broadcast=False)
                emit('set_role', 'Rolle: ', room=player.sid, broadcast=False)
                emit('set_explanation', 'Beschreibung: ', room=player.sid, broadcast=False)
                self.show_settings(user=player)

    def check_for_winner(self):
        wolves_count = 0
        villager_count = 0

        for user in self.alive:
            user.dead = False
            if user.is_evil():
                wolves_count += 1
            else:
                villager_count += 1

        if wolves_count == 0 and villager_count == 0:
            self.display_end(header='Kein Sieger', text='Alle Spieler sind tragisch gestorben!')
            self.actual_step = 'end'
        elif wolves_count > 0 and villager_count == 0:
            self.display_end(header='Die Werwölfe haben gewonnen!',
                             text='Die Dorfbewohner haben die wahren Feinde ihres Dorfes wohl erst zu spät erkannt!')
            self.actual_step = 'end'
        elif wolves_count == 0 and villager_count > 0:
            self.display_end(header='Die Dorfbewohner haben gewonnen!',
                             text='Siegreich stehen sie um den Kadawer des letzten Wolfes und sind froh endlich '
                                  'wieder in Ruhe schlafen zu können!')
            self.actual_step = 'end'
        elif wolves_count == 1 and villager_count == 1:
            wolves = None
            villager = None
            for user in self.alive:
                if user.is_evil():
                    wolves = user
                else:
                    villager = user
            if wolves is not None and villager is not None:
                if wolves is self.loved1 or wolves is self.loved2:
                    if villager is self.loved1 or villager is self.loved2:
                        self.display_end('Das Liebespaar hat gewonnen!', 'Listig haben sie gemeinsam alle Werwölfe und '
                                                                         'Dorfbewohner hintergangen und leben nun in '
                                                                         'Liebe allein bis ans Ende ihrer Tage.')
                        self.actual_step = 'end'

    def display_end(self, header, text):
        self.votes = {}
        self.wait_for_votes_from = []
        self.allow_tie = True
        for player in self.game_users:
            emit('display_header', header, room=player.sid)
            emit('display_text', text, room=player.sid)
            if player is self.admin:
                emit('request_next', '', room=player.sid)
        print(self.admin.username)
        if self.admin is not None:
            self.wait_for_votes_from.append(self.admin)

    def start_game(self):
        self.alive = []
        self.dead = []
        self.master = None

        self.wolves_choose = None
        self.started = False
        self.deletable = False
        self.votes = {}
        self.wait_for_votes_from = []
        self.actual_step = ""
        self.allow_tie = True
        self.loved1 = None
        self.loved2 = None
        self.protected = None
        self.to_kill = None
        self.killed_due_night = []
        self.used_heal = []
        self.used_kill = []
        self.killed_list = []
        self.before_hunter_kill = ''
        self.hunter_killed = []
        self.lynched = None
        self.started = True

        print('Calculate roles for game ' + self.room_name)

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

        for i in range(0, self.amor_count):
            if len(users) > i:
                users.pop(0).role = 'Amor'
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

        print('Setting up first phase of game ' + self.room_name)

        self.alive = self.game_users.copy()

        for user in self.alive:
            send_userdata(user=user)
            print('Alive players: ' + user.username)

        self.actual_step = ''
        self.check_for_winner()
        if self.actual_step == 'end':
            return

        self.handle_last_step()
        self.next_step()

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

    def settings(self, wolves, witches, searchers, amors, hunters, protectors):
        self.wolves_count = int(wolves)
        self.witches_count = int(witches)
        self.searchers_count = int(searchers)
        self.amor_count = int(amors)
        self.hunter_count = int(hunters)
        self.protector_count = int(protectors)

        if self.amor_count > 1:
            self.amor_count = 1
        if self.wolves_count < 1:
            self.wolves_count = 1
        if self.amor_count < 0:
            self.amor_count = 0
        if self.witches_count < 0:
            self.witches_count = 0
        if self.searchers_count < 0:
            self.searchers_count = 0
        if self.hunter_count < 0:
            self.hunter_count = 0
        if self.protector_count < 0:
            self.protector_count = 0
        if self.protector_count > 1:
            self.protector_count = 1

        for user in self.game_users:
            self.show_settings(user=user)

    def kill(self, user):
        if is_user_contained(self.game_users, user) and is_user_contained(self.alive, user):

            if user.role == 'Jäger':
                self.before_hunter_kill = self.actual_step
                self.actual_step = 'hunter_kill'
                self.hunter_killed.append(user)
                return

            self.dead.append(user)
            self.alive.remove(user)
            if self.master is user:
                if len(self.alive) > 0:
                    self.master = self.alive[random.randrange(0, len(self.alive))]
                    for player in self.game_users:
                        emit('info', 'Der Bürgermeister ist gestorben! Der neue Bürgermeister ist: ' +
                             self.master.username, room=player.sid)
            user.kill()
            self.killed_list.append(user)

            if user is self.loved1 and not self.loved2.dead:
                self.kill(self.loved2)
            elif user is self.loved2 and not self.loved1.dead:
                self.kill(self.loved1)
            self.check_for_winner()

    def handle_vote(self, user, vote_for):
        print('Check vote for ' + user.username)
        if is_user_contained(self.wait_for_votes_from, user):
            self.votes[user] = vote_for
            if self.actual_step == 'witch1' and vote_for == 'Ja':
                for player in self.wait_for_votes_from:
                    emit('info', 'Der Mitspieler wurde geheilt!', room=player.sid)
                    emit('hide_vote', '', room=player.sid)

                self.used_heal.append(user)
                self.to_kill = None

                self.next_step()
                return
            if self.actual_step == 'witch2' and vote_for != 'Nein':
                print(user.username + ' -> ' + str(vote_for))
                self.killed_due_night.append(vote_for)
                self.used_kill.append(user)
            if self.actual_step == 'wolves' or self.actual_step == 'vote_master' or self.actual_step == 'vote':
                self.show_votes()
        if len(self.wait_for_votes_from) is len(self.votes):
            if not self.allow_tie and self.is_tie():
                for player in self.wait_for_votes_from:
                    emit('correct_vote', '', room=player.sid)
                    emit('warn', 'Tie is not allowed, please vote another person!', room=player.sid)
                return
            self.handle_last_step()
            self.next_step()
        return

    def is_tie(self):
        counted_votes = {}
        for vote in self.votes.values():
            if not counted_votes.__contains__(vote):
                counted_votes[vote] = 1
            else:
                counted_votes[vote] += 1
        max_vote = -1
        print(counted_votes)
        for counted_vote in counted_votes.values():
            if counted_vote > max_vote:
                max_vote = counted_vote
        count_of_max_votes = 0
        for counted_vote in counted_votes.values():
            if counted_vote == max_vote:
                count_of_max_votes += 1
                if count_of_max_votes > 1:
                    return True
        return False

    def get_voted_player(self):
        if self.is_tie():
            return None
        counted_votes = {}
        for vote in self.votes.values():
            if not is_user_contained(counted_votes, vote):
                counted_votes[vote] = 1
            else:
                counted_votes[vote] += 1
            print(vote.username)
        max_voted_player = None
        max_vote = -1
        for vote in self.votes.values():
            if counted_votes[vote] > max_vote:
                max_vote = counted_votes[vote]
                max_voted_player = vote
        return max_voted_player

    def get_voted_player_by_double_master(self):
        counted_votes = {}
        for vote in self.votes.values():
            if not is_user_contained(counted_votes, vote):
                counted_votes[vote] = 1
            else:
                counted_votes[vote] += 1
            print(vote.username)
        if self.master is not None:
            counted_votes[self.votes[self.master]] += 1
        max_voted_player = None
        max_vote = -1
        max_vote_count = 0
        for vote in self.votes.values():
            if counted_votes[vote] > max_vote:
                max_vote = counted_votes[vote]
                max_voted_player = vote
                max_vote_count = 0
            elif counted_votes[vote] == max_vote:
                max_vote_count += 1
        if max_vote_count > 0:
            return None
        return max_voted_player

    def request_player_vote(self, role, header, message, votes):
        self.votes = {}
        self.wait_for_votes_from = []
        print(self.votes)
        found_player = False
        for player in self.alive:
            if role == 'all' or player.role == role:
                if role == 'Hexe' and self.actual_step == 'witch1' and self.used_heal.__contains__(player):
                    continue
                if role == 'Hexe' and self.actual_step == 'witch2' and self.used_kill.__contains__(player):
                    continue
                if role == 'Jäger' and self.actual_step == 'hunter_kill' and \
                        not self.hunter_killed.__contains__(player):
                    continue
                print('Send message to ' + player.username)
                emit('display_header', header, room=player.sid)
                emit('display_text', message, room=player.sid)
                emit('put_choices', votes, room=player.sid)
                self.wait_for_votes_from.append(player)
                found_player = True
        return found_player

    def send_message_except(self, role, header, message):
        for player in self.alive:
            if player.role is not role:
                emit('display_header', header, room=player.sid)
                emit('display_text', message, room=player.sid)
                emit('wait', '', room=player.sid)

    def request_player_continue(self, role, header, message):
        self.votes = {}
        self.wait_for_votes_from = []
        for player in self.alive:
            if role == 'all' or player.role == role:
                emit('display_header', header, room=player.sid)
                emit('display_text', message, room=player.sid)
                emit('request_next', '', room=player.sid)
                self.wait_for_votes_from.append(player)

    def clear_votes(self):
        for player in self.game_users:
            emit('display_votes', '', room=player.sid)

    def show_votes(self):
        for player in self.alive:
            if self.actual_step == 'wolves' and player.role == 'Werwolf':
                emit('display_votes', self.get_votes(), room=player.sid)
            elif self.actual_step == 'vote':
                emit('display_votes', self.get_votes(), room=player.sid)
            elif self.actual_step == 'vote_master':
                emit('display_votes', self.get_votes_friendly(), room=player.sid)
        for player in self.dead:
            emit('display_votes', self.get_votes(), room=player.sid)

    def display_dead_screens(self):
        for player in self.dead:
            emit('display_header', 'Du bist gestorben!', room=player.sid)
            emit('display_text', self.get_player_infos(), room=player.sid)

    def get_player_infos(self):
        infos = ""
        for player in self.game_users:
            if player.dead:
                infos += player.username + ' ist ' + player.role + ' [Tod]<br>'
            else:
                infos += player.username + ' ist ' + player.role + ' [Lebend]<br>'
        return infos

    def get_votes(self):
        votes = ''
        for player in self.wait_for_votes_from:
            if self.votes.__contains__(player):
                votes += player.username + ' möchte ' + self.votes[player].username + ' umbringen<br>'
            else:
                votes += player.username + ' hat noch nicht abgestimmt!<br>'
        return votes

    def get_votes_friendly(self):
        votes = ''
        for player in self.wait_for_votes_from:
            if self.votes.__contains__(player):
                votes += player.username + ' wählt ' + self.votes[player].username + '<br>'
            else:
                votes += player.username + ' hat noch nicht abgestimmt!<br>'
        return votes

    def get_player_by_role(self, role):
        players = []
        for player in self.alive:
            if role == 'all' or role == player.role:
                players.append(player)
        return players

    def get_player_except(self, not_voteable_players):
        players = []
        print(self.alive)
        for player in self.alive:
            if not is_user_contained(not_voteable_players, player):
                players.append(player)
        return players

    def role_is_present(self, role):
        for player in self.alive:
            if role == player.role:
                return True
        return False

    def handle_last_step(self):
        print('Handle step ' + self.actual_step)

        if self.actual_step == 'amor1':
            voted_player = self.get_voted_player()
            print('Loved1 ' + voted_player.username)
            if voted_player is None:
                self.actual_step = 'start'
                return
            self.loved1 = voted_player
        elif self.actual_step == 'amor2':
            voted_player = self.get_voted_player()
            print('Loved2 ' + voted_player.username)
            if voted_player is None or voted_player is self.loved1:
                self.actual_step = 'amor1'
                return
            self.loved2 = voted_player
        elif self.actual_step == 'protector':
            protected_player = self.get_voted_player()
            if protected_player is None:
                self.actual_step = 'searcher'
                return
            self.protected = protected_player
        elif self.actual_step == 'wolves':
            to_kill = self.get_voted_player()
            if to_kill is None:
                self.actual_step = 'protector'
                return
            self.to_kill = to_kill
        elif self.actual_step == 'witch2':
            if self.to_kill is not None and self.to_kill != self.protected:
                self.kill(self.to_kill)
            for player in self.killed_due_night:
                self.kill(player)
        elif self.actual_step == 'hunter_kill':
            kill_loved = None
            for hunter in self.hunter_killed:
                self.dead.append(hunter)
                self.alive.remove(hunter)
                hunter.kill()
                self.killed_list.append(hunter)

                if hunter is self.loved1 and not self.loved2.dead:
                    if kill_loved is None:
                        kill_loved = self.loved2
                    else:
                        kill_loved = None
                elif hunter is self.loved2 and not self.loved1.dead:
                    if kill_loved is None:
                        kill_loved = self.loved1
                    else:
                        kill_loved = None
            self.hunter_killed = []
            self.actual_step = self.before_hunter_kill
            if kill_loved is not None:
                self.kill(kill_loved)
            for user in self.votes.values():
                self.kill(user)
        elif self.actual_step == 'end':
            print('Reset game')

            self.alive = []
            self.dead = []
            self.started = False
            self.votes = {}
            self.wait_for_votes_from = []
            self.allow_tie = True
            self.loved1 = None
            self.loved2 = None
            self.protected = None
            self.to_kill = None
            self.killed_due_night = []
            self.used_heal = []
            self.used_kill = []
            self.killed_list = []
            self.before_hunter_kill = ''
            self.hunter_killed = []
            self.master = None

            for player in self.game_users:
                emit('display_text', "Spieler: ", room=player.sid)
                emit('display_header', "Raum: " + self.room_name, room=player.sid)

                for user in self.game_users:
                    emit('append_text', user.username, room=player.sid)

                emit('show_room', "", room=player.sid, broadcast=False)
                emit('set_room_name', "Raum: " + self.room_name, room=player.sid, broadcast=False)
                emit('set_role', 'Rolle: ', room=player.sid, broadcast=False)
                emit('set_explanation', 'Beschreibung: ', room=player.sid, broadcast=False)
                self.show_settings(user=player)
        elif self.actual_step == 'vote_master':
            self.master = self.get_voted_player()
            if self.master is None:
                self.actual_step = 'day'
        elif self.actual_step == 'vote':
            if self.is_tie():
                self.lynched = self.get_voted_player_by_double_master()
                if self.lynched is not None:
                    self.kill(self.lynched)
            else:
                self.lynched = self.get_voted_player()
                if self.lynched is not None:
                    self.kill(self.lynched)

    def next_step(self):
        print('Next step ' + self.actual_step)
        if self.actual_step == '':
            self.clear_votes()
            self.actual_step = 'start'
            self.request_player_continue(role='all', header='Spiel starten', message='Drücke weiter um im Spiel dabei '
                                                                                     'zu sein!')
        elif self.actual_step == 'start':
            if not self.role_is_present('Amor'):
                self.actual_step = 'loved'
                self.next_step()
                return

            self.actual_step = 'amor1'
            self.send_message_except(role='Amor', header='Warte bis du and der Reihe bist',
                                     message='Ein seltsamer Duft weht dir in die Nase und aus der Ferne hörst du das '
                                             'zischen eines Pfeils.')
            self.request_player_vote(role='Amor', header='Liebespaar wählen', message='Schieße deinen Liebespfeil '
                                                                                       'auf den ersten Liebespartner '
                                                                                       'den du wählst!',
                                     votes=make_voteable_player_list(self.get_player_by_role('all')))
        elif self.actual_step == 'amor1':
            self.actual_step = 'amor2'
            self.request_player_vote(role='Amor', header='Liebespaar wählen', message='Schieße deinen Liebespfeil '
                                                                                       'auf den zweiten Liebespartner '
                                                                                       'den du wählst!',
                                     votes=make_voteable_player_list(self.get_player_except([self.loved1])))
        elif self.actual_step == 'amor2':
            self.actual_step = 'loved'
            self.votes = {}
            self.wait_for_votes_from = [self.loved1, self.loved2]
            self.send_message_except(role='', header='Warte bis du an der Reihe bist', message='Du vernimmst ein '
                                                                                               'fröhliches Kichern in '
                                                                                               'deinen Träumen, nanu, '
                                                                                               'woher kam das bloß?')

            emit('display_header', 'Du wachst auf und scheinst in deinen schönsten Träumen angelangt zu sein',
                 room=self.loved1.sid)
            emit('display_text', 'Du siehst ' + self.loved2.username + ' in die Augen und weißt das du nie wieder ohne '
                                                                       'ihn leben können wirst', room=self.loved1.sid)
            emit('request_next', '', room=self.loved1.sid)
            emit('display_header', 'Du wachst auf und scheinst in deinen schönsten Träumen angelangt zu sein',
                 room=self.loved2.sid)
            emit('display_text', 'Du siehst ' + self.loved1.username + ' in die Augen und weißt das du nie wieder ohne '
                                                                       'ihn leben können wirst', room=self.loved2.sid)
            emit('request_next', '', room=self.loved2.sid)
        elif self.actual_step == 'loved':
            if not self.role_is_present('Seherin'):
                self.actual_step = 'searcher'
                self.next_step()
                return
            self.actual_step = 'searcher'
            self.allow_tie = True
            self.send_message_except(role='Seherin', header='Warte bis du an der Reihe bist',
                                     message='In deinem Traum erscheint für eine Sekunde ein kleines Mädchen, '
                                             'das dich kurz und durchdringend anschaut, dann ist es auch schon wieder '
                                             'verschwunden...')
            self.request_player_vote(role='Seherin', header='Die Seherinnen sind nun am Zug!',
                                     message='Du wachst auf um heimlich einen Mitspieler diese Nacht mithilfe deiner '
                                             'Glaskugel zu enttarnen.', votes=make_voteable_player_list(self.alive))
        elif self.actual_step == 'searcher':
            if not self.role_is_present('Beschützer'):
                self.protected = None
                self.actual_step = 'protector'
                self.next_step()
                return
            self.actual_step = 'protector'
            self.allow_tie = True
            self.send_message_except(role='Beschützer', header='Warte bis du an der Reihe bist',
                                     message='Du hörst ein metallisches Klirren, doch du denkst dir nichts weiter '
                                             'dabei...')
            if self.protected is None:
                self.request_player_vote(role='Beschützer', header='Wen möchtest du beschützen?',
                                         message='Du kannst jede Nacht eine Person vor dem grausigen Tod durch die '
                                                 'Werwölfe beschützen, doch wäre es zu auffällig zweimal hintereinander '
                                                 'die gleiche Person zu beschützen',
                                         votes=make_voteable_player_list(self.alive))
            else:
                self.request_player_vote(role='Beschützer', header='Wen möchtest du beschützen?',
                                         message='Du kannst jede Nacht eine Person vor dem grausigen Tod durch die '
                                                 'Werwölfe beschützen, doch wäre es zu auffällig zweimal hintereinander '
                                                 'die gleiche Person zu beschützen',
                                         votes=make_voteable_player_list(self.get_player_except([self.protected])))
        elif self.actual_step == 'protector':
            if not self.role_is_present('Werwolf'):
                self.actual_step = 'witch1'
                self.next_step()
                return
            self.actual_step = 'wolves'
            self.allow_tie = False
            self.send_message_except(role='Werwolf', header='Warte bis du an der Reihe bist',
                                     message='Aus der Ferne hörst du ein gedämpftes Heulen, ein kalter Schauder läuft '
                                             'dir den Rücken herunter...')
            self.request_player_vote(role='Werwolf', header='Die Werwölfe erwachen',
                                     message='Hungrig wachst du auf und findest die anderen Werwölfe! Ihr macht euch '
                                             'auf die Jagt im Dorf! Wen werdet ihr euch diese Nacht wohl vornehmen?',
                                     votes=make_voteable_player_list(self.alive))
            self.show_votes()
        elif self.actual_step == 'wolves':
            if not self.role_is_present('Hexe'):
                self.actual_step = 'witch2'
                self.handle_last_step()
                self.next_step()
                return
            self.actual_step = 'witch1'
            self.allow_tie = True
            self.send_message_except(role='Hexe', header='Warte bis du an der Reihe bist',
                                     message='Betörende Düfte liegen über der Stadt und du hörst schaurige Wörter in '
                                             'deinen Träumen!')
            if not self.request_player_vote(role='Hexe', header='Die Hexen erwachen',
                                     message=self.to_kill.username + ' wurde von den Werwölfen verwundet. Möchtest du '
                                                                     'ihn '
                                                                     'heilen?',
                                     votes=get_witch_votes()):
                self.next_step()
        elif self.actual_step == 'witch1':
            self.actual_step = 'witch2'
            self.allow_tie = True
            self.clear_votes()
            self.send_message_except(role='Hexe', header='Warte bis du an der Reihe bist',
                                     message='Betörende Düfte liegen über der Stadt und du hörst schaurige Wörter in '
                                             'deinen Träumen!')
            if not self.request_player_vote(role='Hexe', header='Die Hexen erwachen',
                                     message='Möchtest du jemandem noch deinen Todestrank einflößen?',
                                     votes="""</div><div class="option Nein"><input type="radio" class="radio" id="sidebar-Nein" name="category"><label for="sidebar-Nein">Nein</label></div>""" + make_voteable_player_list(
                                         self.alive)):
                self.handle_last_step()
                self.next_step()
        elif self.actual_step == 'witch2':
            self.actual_step = 'day'
            happening = ""

            for user in self.killed_list:
                happening += user.username + ' ist verstorben! Er war ' + user.role + '.<br>'
            if happening == '':
                happening = 'Auch wenn diese Nacht aus mancher Augen unheimlich schien,' \
                            ' hat ein jeder sie unbeschadet überstanden! '
            self.killed_list = []

            self.request_player_continue(role='all', header='Es wird Tag', message=happening)
        elif self.actual_step == 'day':
            if self.master is None:
                self.actual_step = 'vote_master'
                self.allow_tie = False
                self.request_player_vote(role='all', header='Bürgermeisterwahl', message='Wählt einen Bürgermeister',
                                         votes=make_voteable_player_list(self.alive))
                self.show_votes()
            else:
                self.actual_step = 'display_master'
                self.next_step()
        elif self.actual_step == 'vote_master':
            self.actual_step = 'display_master'
            self.request_player_continue(role='all', header='Ihr habt einen Bürgermeister gewählt!',
                                         message='Euer Bürgermeister ist ' + self.master.username)
            self.clear_votes()
        elif self.actual_step == 'display_master':
            self.actual_step = 'vote'
            self.allow_tie = True
            self.request_player_vote(role='all', header='Abstimmung',
                                     message='Nach den schrecklichen Vorkommnissen in der Nacht hab ihr euch '
                                             'entschieden heute eine Abstimmung durchzuführen, um den Täter zu '
                                             'lynchen!', votes=make_voteable_player_list(self.alive))
            self.show_votes()
        elif self.actual_step == 'vote':
            self.actual_step = 'day_end'
            self.clear_votes()
            if self.lynched is None:
                self.request_player_continue(role='all', header='Ergebniss', message='Es wurde keiner gelynched!')
            else:
                happening = self.lynched.username + ' wurde gelynched! Nach Durchsuchung seiner Bleibe stellt ihr ' \
                                                    'fest: Er war ' + self.lynched.role + '<br> '

                for user in self.killed_list:
                    happening += user.username + ' ist verstorben! Er war ' + user.role + '.<br>'
                self.killed_list = []

                self.request_player_continue(role='all', header='Ergebniss', message=happening)
        elif self.actual_step == 'day_end':
            self.actual_step = 'loved'
            self.next_step()
        elif self.actual_step == 'hunter_kill':
            self.allow_tie = True
            self.request_player_vote(role='Jäger', header='Du stirbst...',
                                     message='Doch noch bevor dein letzter Atem deinen Körper verlässt ziehst du '
                                             'deine Waffe und schießt auf...',
                                     votes=make_voteable_player_list(self.alive))
        elif self.actual_step == 'end' and not self.started:
            print('End game')
            self.clear_votes()
            self.actual_step = ''
        if self.actual_step != 'end' and self.actual_step != '':
            self.display_dead_screens()
