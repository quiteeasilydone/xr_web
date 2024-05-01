from flask import Flask, render_template, redirect, url_for
from flask_socketio import SocketIO, join_room, emit
from flask import Flask, request, jsonify
import psycopg2

server = Flask(__name__)
server.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(server)
# socketio.init_app(server, cors_allowed_origins="*")



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
    print('zoom')
    return render_template('zoom.html')

# @server.route('/api/db-submit/', methods = ['POST'])
# def submit():
#     data = request.json  # 클라이언트로부터 받은 JSON 데이터
#     description = data['description']
#     selection = data['selection']
    
#     # 데이터베이스에 데이터를 저장
#     conn = connect_db()
#     cur = conn.cursor()
#     cur.execute('INSERT INTO procedure ("infraName", "inspectionList") VALUES (%s, %s)', (description, selection))
#     conn.commit()
#     cur.close()
#     conn.close()
    
#     return jsonify({"message": "Data saved successfully"}), 200

@server.route('/api/reports', methods = ['POST'])
def db_submit():
    data = request.get_json()  # 클라이언트로부터 받은 JSON 데이터

    # json data parsing
    infra_id = data['infra'] # json data 'infra' field
    start_time = '0000'
    end_time = '0000'
    client_id = '0000'

    # 데이터베이스에 데이터를 저장
    conn = connect_db()
    cur = conn.cursor()

    ## postgres SQL
    # Insert into reports
    cur.execute('INSERT INTO reports ("infra", "start_time", "end_time", "client_id") VALUES (%s, %s, %s, %s) RETURNING report_id', (infra_id, start_time, end_time, client_id))
    report_id = cur.fetchone()[0]  # Fetch the generated report_id


    # inspectionList의 각 topic에 대해 처리
    for inspection in data['inspection_list']:  # json data 'inspectionList' field
        topic_name = inspection['topic']
        image_required = inspection['image_required']
        
        # topics 테이블에 삽입
        cur.execute('INSERT INTO topics ("report_id", "topic_name", "image_required") VALUES (%s, %s, %s) RETURNING topic_id', (report_id, topic_name, image_required))
        topic_id = cur.fetchone()[0]

        # instructionList의 각 instruction에 대해 처리
        for instruction in inspection['instruction_list']:
            instruction_text = instruction['instruction']
            instruction_type = instruction['instruction_type']
            options = "{" + ','.join(instruction.get('options', [])) + "}" if instruction.get('options') else "{}" # insert into varchar[]
            answer = "{" + ','.join(instruction.get('answer', [])) + "}" if instruction.get('answer') else "{}" # insert into varchar[]
            
            # instructions 테이블에 삽입
            cur.execute('INSERT INTO instructions ("topic_id", "instruction", "instruction_type", "options", "answer") VALUES (%s, %s, %s, %s, %s)', (topic_id, instruction_text, instruction_type, options, answer))


    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({"message": "Data saved successfully"}), 200

# 쿼리 파라미터로 {infra : [infra_name]} 이 오면 해당 infra name 에 맞는 infra report 중 가장 최신(id가 가장 높은)거 return
@server.route('/api/infra/report', methods=['GET'])
def db_view():
    # 인프라 이름 파라미터 확인
    infra_name = request.args.get('infra')

    if infra_name is None:
        return jsonify({'error': 'Infra name is missing in query parameters'}), 400
    
    # 데이터베이스 연결
    conn = connect_db()
    cur = conn.cursor()

    # 보고서 조회
    cur.execute('SELECT * FROM reports WHERE infra = %s ORDER BY report_id DESC LIMIT 1', (infra_name,))
    report = cur.fetchone()
    if report is None:
        return jsonify({'error': f'No reports found for infra name: {infra_name}'}), 404

    report_id = report[0]  # 튜플의 첫 번째 요소는 report_id

    # 카테고리 및 해당하는 주제와 지시사항 조회
    cur.execute('SELECT * FROM topics WHERE report_id = %s', (report_id,))
    topic_data = cur.fetchall()

    # 보고서 내용을 담을 리스트 생성
    inspection_list = []

    # 각 카테고리에 대해 처리
    for topic in topic_data:
        # 주제와 지시사항 조회
        cur.execute('SELECT * FROM instructions WHERE topic_id = %s', (topic[0],))
        instruction_data = cur.fetchall()

        # 지시사항을 담을 리스트 생성
        instructions_list = []

        # 각 지시사항에 대해 처리
        for instruction in instruction_data:
            instructions_list.append({
                'instruction': instruction[2],
                'instruction_type': instruction[3],
                'options': instruction[4],
                'answer': instruction[5]
            })

        # 각 카테고리에 대한 정보를 추가
        inspection_list.append({
            'topic': topic[2],
            'instruction_list': instructions_list,
            'image_required': topic[3]
        })

    # 데이터베이스 연결 종료
    cur.close()
    conn.close()

    # JSON 응답 생성
    response_data = {
        'infra': infra_name,
        'inspection_list': inspection_list
    }

    return jsonify(response_data), 200

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

# 로컬에서 테스트 중인 join_room
# @socketio.on('join_room')
# def handle_join_room(roomName):
#     print(f'Joining room: {roomName}')
    
#     # 방에 속한 모든 소켓의 ID 출력

#     join_room(roomName)

#     # 방에 있는 모든 소켓 가져오기
#     room_sid_list = list(socketio.server.manager.rooms["/"].get(roomName, set()))
#     # 자신의 소켓 ID 가져오기
#     client_sid = request.sid
    
#     # room_sid_list를 순회하면서 자신의 소켓 ID와 다른 소켓 ID를 출력
#     print("방에 속한 소켓 id들중, 제가 아닌 것만 출력할게요")
#     for sid in room_sid_list:
#         if sid != client_sid:
#             print(sid);
#             emit('welcome', room=sid)

@socketio.on('offer')
def handle_offer(offer, room_name):
    emit('offer', offer, room=room_name)

@socketio.on('answer')
def handle_answer(answer, room_name):
    emit('answer', answer, room=room_name)

@socketio.on('ice')
def handle_ice(ice, room_name):
    emit('ice', ice, room=room_name)