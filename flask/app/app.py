from flask import Flask, render_template, redirect, url_for
from flask_socketio import SocketIO, join_room, emit
from flask import Flask, request, jsonify
import psycopg2

server = Flask(__name__)
server.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(server)
socketio.init_app(server, cors_allowed_origins="*")

def connect_db():
    conn = psycopg2.connect(
        dbname="flaskdb", user="flaskuser", password="flaskpassword", host="postgresdb"
    )
    return conn

@server.route('/api/')
def index():
    return render_template('index.html')

@server.route('/api/document/')
def document():
    return render_template('document.html')

@server.route('/api/zoom/')
def zoom():
    return render_template('zoom.html')

@server.route('/api/submit/', methods = ['POST'])
def submit():
    data = request.json  # 클라이언트로부터 받은 JSON 데이터
    description = data['description']
    selection = data['selection']
    
    # 데이터베이스에 데이터를 저장
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO procedure ("infraName", "inspectionList") VALUES (%s, %s)', (description, selection))
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({"message": "Data saved successfully"}), 200

def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    socketio.emit('my response', json, callback=messageReceived)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('join_room')
def handle_join_room(room_name):
    print(f'Join room: {room_name}')
    join_room(room_name)
    emit('welcome', room=room_name)

@socketio.on('offer')
def handle_offer(offer, room_name):
    emit('offer', offer, room=room_name)

@socketio.on('answer')
def handle_answer(answer, room_name):
    emit('answer', answer, room=room_name)

@socketio.on('ice')
def handle_ice(ice, room_name):
    emit('ice', ice, room=room_name)