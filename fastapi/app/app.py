from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import asyncpg

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

async def connect_db():
    conn = await asyncpg.connect(
        dbname="flaskdb", user="flaskuser", password="flaskpassword", host="postgresdb"
    )
    return conn

@app.get("/api/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/document/", response_class=HTMLResponse)
async def document(request: Request):
    return templates.TemplateResponse("document.html", {"request": request})

@app.get("/api/zoom/", response_class=HTMLResponse)
async def zoom(request: Request):
    print('zoom')
    return templates.TemplateResponse("zoom.html", {"request": request})

@app.post("/api/reports")
async def db_submit(request: Request):
    data = await request.json()  # 클라이언트로부터 받은 JSON 데이터

    # json data parsing
    infra_id = data.get('infra', None) # json data 'infra' field
    start_time = '0000'
    end_time = '0000'
    client_id = '0000'

    if not infra_id:
        raise HTTPException(status_code=400, detail="Infra field is required")

    # 데이터베이스에 데이터를 저장
    conn = await connect_db()

    ## postgres SQL
    # Insert into reports
    report_id = await conn.fetchval('INSERT INTO reports ("infra", "start_time", "end_time", "client_id") VALUES ($1, $2, $3, $4) RETURNING report_id', infra_id, start_time, end_time, client_id)

    # inspectionList의 각 topic에 대해 처리
    for inspection in data.get('inspection_list', []):  # json data 'inspectionList' field
        topic_name = inspection['topic']
        image_required = inspection['image_required']
        
        # topics 테이블에 삽입
        topic_id = await conn.fetchval('INSERT INTO topics ("report_id", "topic_name", "image_required") VALUES ($1, $2, $3) RETURNING topic_id', report_id, topic_name, image_required)

        # instructionList의 각 instruction에 대해 처리
        for instruction in inspection.get('instruction_list', []):
            instruction_text = instruction['instruction']
            instruction_type = instruction['instruction_type']
            options = "{" + ','.join(instruction.get('options', [])) + "}" if instruction.get('options') else "{}" # insert into varchar[]
            answer = "{" + ','.join(instruction.get('answer', [])) + "}" if instruction.get('answer') else "{}" # insert into varchar[]
            
            # instructions 테이블에 삽입
            await conn.execute('INSERT INTO instructions ("topic_id", "instruction", "instruction_type", "options", "answer") VALUES ($1, $2, $3, $4, $5)', topic_id, instruction_text, instruction_type, options, answer)

    await conn.close()
    
    return JSONResponse(content={"message": "Data saved successfully"}, status_code=200)

@app.get("/api/infra/report")
async def db_view(request: Request, infra: str = None):
    # 인프라 이름 파라미터 확인
    if not infra:
        raise HTTPException(status_code=400, detail="Infra name is missing in query parameters")
    
    # 데이터베이스 연결
    conn = await connect_db()

    # 보고서 조회
    report = await conn.fetchrow('SELECT * FROM reports WHERE infra = $1 ORDER BY report_id DESC LIMIT 1', infra)
    if not report:
        raise HTTPException(status_code=404, detail=f'No reports found for infra name: {infra}')

    report_id = report[0]  # 튜플의 첫 번째 요소는 report_id

    # 카테고리 및 해당하는 주제와 지시사항 조회
    topic_data = await conn.fetch('SELECT * FROM topics WHERE report_id = $1', report_id)

    # 보고서 내용을 담을 리스트 생성
    inspection_list = []

    # 각 카테고리에 대해 처리
    for topic in topic_data:
        # 주제와 지시사항 조회
        instruction_data = await conn.fetch('SELECT * FROM instructions WHERE topic_id = $1', topic[0])

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
    await conn.close()

    # JSON 응답 생성
    response_data = {
        'infra': infra,
        'inspection_list': inspection_list
    }

    return JSONResponse(content=response_data, status_code=200)

def messageReceived():
    print('message was received!!!')
