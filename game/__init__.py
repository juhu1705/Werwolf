import os

from flask import Flask, request
from flask_socketio import SocketIO, send, emit

from game.room import Room, is_user_contained
from game.user import User
from . import game

app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(SECRET_KEY='219z4r34äc3ü696567ß50917325#897235jhkle65bju#5')

os.makedirs(app.instance_path, exist_ok=True)

users = {}
sids = {}
rooms = {}

socketio = SocketIO(app)
if __name__ == "__main__":
    socketio.run(app)


app.register_blueprint(game.bp)


def get_username(sid):
    return sids[sid].username


@socketio.on('message')
def message(data):
    print(data)
    emit('display_header', "Please Login", broadcast=False)
    emit('display_text', "Choose your name!", broadcast=False)
    emit('set_role', 'Rolle: ', broadcast=False)
    emit('set_explanation', 'Beschreibung: ', broadcast=False)


@socketio.on('username')
def user_login(username):
    if not len(str(username).strip()):
        emit('warn', "A username must be chosen!", broadcast=False)
        return

    if users.__contains__(username) or username == 'Ja' or username == 'Nein':
        emit('warn', "Username is already in use!", broadcast=False)
        return
    player = User(username=username, sid=request.sid)
    users[username] = player
    sids[request.sid] = player
    emit('set_username', "Name: " + username, broadcast=False)
    emit('display_header', "Choose your room", broadcast=False)
    emit('display_text', "Join a room or create your own one!", broadcast=False)
    emit('show_rooms', '', broadcast=False)
    emit('display_volume', 'off', broadcast=False, room=request.sid)
    print(users)


@socketio.on('disconnect')
def leave():
    sid = request.sid
    if not sids.__contains__(sid):
        return
    name = get_username(sid)
    print('Client leave ' + name)
    user = sids[sid]
    del sids[sid]
    del users[name]
    room = user.room
    user.leave()
    if room is not None and room.deletable:
        del rooms[room.room_name]


@socketio.on('exit_room')
def on_exit_room(data):
    room = sids[request.sid].room
    sids[request.sid].leave()
    if room is not None and room.deletable:
        del rooms[room.room_name]
    emit('display_header', "Choose your room", broadcast=False)
    emit('display_text', "Join a room or create your own one!", broadcast=False)
    emit('show_rooms', '', broadcast=False)
    emit('set_role', 'Rolle: ', broadcast=False)
    emit('set_explanation', 'Beschreibung: ', broadcast=False)


@socketio.on('create_room')
def create_room(room_name):
    if rooms.__contains__(room_name):
        emit('warn', "There is a match with this name! Please try another name!", broadcast=False)
        return
    rooms[room_name] = Room(room_name=room_name, user=sids[request.sid])


@socketio.on('join_room')
def join_room(room_name):
    if not rooms.__contains__(room_name):
        emit('warn', "There is no match with this name! You can create one!", broadcast=False, room=request.sid)
        return

    room = rooms[room_name]
    if room.started:
        emit('warn', "This match has already been started!", broadcast=False, room=request.sid)
        return

    emit('display_text', "Players: ", broadcast=False)
    rooms[room_name].add_user(new_user=sids[request.sid])
    print(rooms)


@socketio.on('room_settings')
def room_settings(data):
    room = sids[request.sid].room
    if room is None:
        emit('warn', "Du bist in keinem Raum!", room=request.sid)
        return
    if room.admin is not sids[request.sid]:
        emit('warn', "Du hast hierzu keine Berechtigungen!", room=request.sid)
        return
    if room.started:
        emit('warn', "Spiel wurde bereits gestartet!", room=request.sid)
        return
    room.settings(wolves=data['wolves_count'], witches=data['witches_count'], searchers=data['searchers_count'],
                  hunters=data['hunter_count'], protectors=data['protector_count'], amors=data['amor_count'])


@socketio.on('start_game')
def start_game(data):
    user = sids[request.sid]
    if user.room is None:
        emit('warn', "Please create a match to enable this option", room=request.sid)
        return
    if user.room.admin is not user:
        emit('warn', "Please ask the admin to start the match", room=request.sid)
        return
    if user.room.started:
        emit('warn', "Spiel wurde bereits gestartet!", room=request.sid)
        return

    user.room.start_game()


@socketio.on('player_vote')
def on_player_vote(voted_player):
    user = sids[request.sid]
    emit('hide_action', '', room=request.sid, broadcast=False)

    if user.room is not None and user.room.started and is_user_contained(user.room.alive, user):
        if user.room.actual_step == 'witch1':
            user.room.handle_vote(user=user, vote_for=voted_player)
            return
        elif user.room.actual_step == 'witch2' and voted_player == 'Nein':
            user.room.handle_vote(user=user, vote_for=voted_player)
            return

        if not users.keys().__contains__(voted_player):
            emit('warn', 'You must vote for an existing player!', room=request.sid)
            return

        if user.room.actual_step == 'searcher':
            if user.role == 'Seherin':
                emit('display_header', 'Du erblickst den gesuchten in der Glaskugel und erkennst...', room=request.sid)
                emit('display_text', users[voted_player].username + ' ist ' + users[voted_player].role, room=request.sid)
                emit('request_next', '', room=request.sid)
            return

        user.room.handle_vote(user=user, vote_for=users[voted_player])


@socketio.on('player_next')
def on_player_next(data):
    user = sids[request.sid]
    emit('hide_continue', '', room=request.sid, broadcast=False)

    if user.room is not None and user.room.started and is_user_contained(user.room.alive, user):
        print('Player ' + user.username + ' trying to vote in game ' + user.room.room_name)
        user.room.handle_vote(user=user, vote_for='next')
    if user.room is not None and user.room.started and user.room.admin is user and user.room.actual_step == 'end':
        user.room.handle_vote(user=user, vote_for='next')


@socketio.on('mute_change')
def mute_change(data):
    if request.sid in sids:
        user = sids[request.sid]
        user.sounds_active = not user.sounds_active
        if user.sounds_active:
            emit('display_volume', 'on', broadcast=False, room=request.sid)
        else:
            emit('display_volume', 'off', broadcast=False, room=request.sid)
    else:
        emit('warn', 'You must choose a username to use this function', broadcast=False, room=request.sid)
