import os

from flask import Flask, request
from flask_socketio import SocketIO, send, emit

from game.room import Room
from game.user import User

app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(SECRET_KEY='219z4r34äc3ü696567ß50917325#897235jhkle65bju#5',
                        DATABASE=os.path.join(app.instance_path, 'wolves.sqlite'))

os.makedirs(app.instance_path, exist_ok=True)

users = {}
sids = {}
rooms = {}

socketio = SocketIO(app)
if __name__ == "__main__":
    socketio.run(app)

from . import game

app.register_blueprint(game.bp)


def get_username(sid):
    return sids[sid].username


@socketio.on('message')
def message(data):
    print(data)
    emit('display_header', "Please Login", broadcast=False)
    emit('display_text', "Choose your name!", broadcast=False)


@socketio.on('username')
def user_login(username):
    if not len(str(username).strip()):
        emit('warn', "A username must be chosen!", broadcast=False)
        return

    if users.__contains__(username):
        emit('warn', "Username is already in use!", broadcast=False)
        return

    users[username] = User(username=username, sid=request.sid)
    sids[request.sid] = User(username=username, sid=request.sid)
    emit('set_username', "Name: " + username, broadcast=False)
    emit('display_header', "Choose your room", broadcast=False)
    emit('display_text', "Join a room or create your own one!", broadcast=False)
    emit('show_rooms', '', broadcast=False)
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
    rooms[room_name].show_settings(user=sids[request.sid])
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
                  hunters=data['hunter_count'], protectors=data['protector_count'], armors=data['armor_count'])


@socketio.on('start_game')
def start_game(data):
    user = sids[request.sid]
    if user.room is None:
        emit('warn', "Please create a match to enable this option", room=request.sid)
        return
    if user.room.admin is not user:
        emit('warn', "Please ask the admin to start the match", room=request.sid)
        return
