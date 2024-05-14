from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated, Union
from jose import jwt
from minio import Minio
import requests
import asyncpg
import os
import pytz
import json
import io

## FASTAPI application 생성
app = FastAPI()

## DB 및 Storage Connection
# postgresDB 연결
async def connect_db():
    conn = await asyncpg.connect(os.environ['DATABASE_URL'])
    return conn

# MinIO client 초기화
minio_client = Minio(
    os.environ['MINIO_ENDPOINT'],
    access_key=os.environ['MINIO_ACCESS_KEY'],
    secret_key=os.environ['MINIO_SECRET_KEY'],
    secure=True
)

## 구글 SSO 연동
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
GOOGLE_CLIENT_ID = os.environ['XR_WEB_SERVER_GOOGLE_CLIENT_ID']
GOOGLE_CLIENT_SECRET = os.environ['XR_WEB_SERVER_GOOGLE_CLIENT_SECRET']
GOOGLE_REDIRECT_URI = os.environ['XR_WEB_SERVER_GOOGLE_REDIRECT_URI']

# Initiating the Google login flow
# redirect_uri 끝에 query param 으로 code가 붙는데, 이걸 /api/auth/google 에 같이 요청하면 로그인 한 사용자 정보를 돌려줌
@app.get("/api/login/google")
async def login_google(request: Request):
    return {
        "url": f"https://accounts.google.com/o/oauth2/v2/auth/oauthchooseaccount?client_id={GOOGLE_CLIENT_ID}"
    f"&redirect_uri={GOOGLE_REDIRECT_URI}&response_type=code&scope=email%20profile&service=lso&o2v=2&ddm=0&flowName=GeneralOAuthFlow"
    }

# Exchanging the authorization code for an access token
@app.get("/api/auth/google")
async def auth_google(code: str):
    token_url = "https://accounts.google.com/o/oauth2/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    response = requests.post(token_url, data=data)
    access_token = response.json().get("access_token")
    user_info = requests.get("https://www.googleapis.com/oauth2/v1/userinfo", headers={"Authorization": f"Bearer {access_token}"})
    return user_info.json()

# Endpint to decode and verify the JWT token obtained after successful authentication
@app.get("/api/token")
async def get_token(token: str = Depends(oauth2_scheme)):
    return jwt.decode(token, GOOGLE_CLIENT_SECRET, algorithms=["HS256"])


### 보고서 관련 API ###

# 보고서(양식) 정보 입력
@app.post("/api/reports")
async def db_submit(request: Request):
    data = await request.json()  # 클라이언트로부터 받은 JSON 데이터

    # json data parsing
    infra_name = data.get('infra', None) # json data 'infra' field

    # 임시 user_name 0000
    user_name = "0000"

    if not infra_name:
        raise HTTPException(status_code=400, detail="Infra field is required")

    # 데이터베이스에 데이터를 저장
    conn = await connect_db()

    ## postgres SQL
    try:
        # Check if infra_name already exists in the infras table
        infra_id = await conn.fetchval('''
            SELECT infra_id FROM infras WHERE infra_name = $1
        ''', infra_name)

        # If infra_name does not exist, insert into infras table
        if not infra_id:
            infra_id = await conn.fetchval('''
                INSERT INTO infras ("infra_name")
                VALUES ($1)
                RETURNING infra_id
            ''', infra_name)

        # Insert into report_forms
        report_id = await conn.fetchval('''
            INSERT INTO report_forms ("infra_id", "user_name")
            VALUES ($1, $2)
            RETURNING report_form_id
        ''', infra_id, user_name)

        # inspectionList의 각 topic에 대해 처리
        for inspection in data.get('inspection_list', []):  # json data 'inspectionList' field
            topic_name = inspection['topic']
            image_required = inspection['image_required']
            
            # topic_forms 테이블에 삽입
            topic_id = await conn.fetchval('''
                INSERT INTO topic_forms ("report_form_id", "topic_form_name", "image_required")
                VALUES ($1, $2, $3)
                RETURNING topic_form_id
            ''', report_id, topic_name, image_required)

            # instructionList의 각 instruction에 대해 처리
            for instruction in inspection.get('instruction_list', []):
                instruction_text = instruction['instruction']
                instruction_type = instruction['instruction_type']
                options = instruction.get('options', [])  # options를 직접 사용합니다.
                answer = instruction.get('answer', [])    # answer를 직접 사용합니다.
                
                # instruction_forms 테이블에 삽입
                await conn.execute('''
                    INSERT INTO instruction_forms ("topic_form_id", "instruction", "instruction_type", "options", "answer")
                    VALUES ($1, $2, $3, $4, $5)
                ''', topic_id, instruction_text, instruction_type, options, answer)

        await conn.close()
        return JSONResponse(content={"message": "Data saved successfully"}, status_code=200)
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=f"Error saving data: {str(e)}")

# infra name에 해당하는 가장 최신의 report 받기
@app.get("/api/infra/report")
async def db_view(request: Request, infra: str = None):
    # 인프라 이름 파라미터 확인
    if not infra:
        raise HTTPException(status_code=400, detail="Infra name is missing in query parameters")
    
    # 데이터베이스 연결
    conn = await connect_db()

    try:
        # 보고서 조회
        infra_id = await conn.fetchval('''
            SELECT infra_id FROM infras where infra_name = $1
        ''', infra
        )
        report = await conn.fetchrow('''
            SELECT * FROM report_forms WHERE infra_id = $1 ORDER BY report_form_id DESC LIMIT 1
        ''', infra_id)
        if not report:
            raise HTTPException(status_code=404, detail=f'No reports found for infra name: {infra}')

        report_id = report[0]  # 튜플의 첫 번째 요소는 report_id

        # 카테고리 및 해당하는 주제와 지시사항 조회
        topic_data = await conn.fetch('SELECT * FROM topic_forms WHERE report_form_id = $1', report_id)

        # 보고서 내용을 담을 리스트 생성
        inspection_list = []

        # 각 카테고리에 대해 처리
        for topic in topic_data:
            # 주제와 지시사항 조회
            instruction_data = await conn.fetch('SELECT * FROM instruction_forms WHERE topic_form_id = $1', topic[0])

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

        # JSON 응답 생성
        response_data = {
            'infra': infra,
            'inspection_list': inspection_list
        }

        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=f"Error retrieving data: {str(e)}")

# 전체 설비 목록 가져오기
# 페이지네이션 필요
@app.get("/api/infra-list")
async def get_infra_list(request: Request):
    try:
        # DB 연결
        conn = await connect_db()

        # 모든 보고서의 인프라 이름 가져오기
        infra_list = await conn.fetch('SELECT DISTINCT infra_name FROM infras')

        # 데이터베이스 연결 종료
        await conn.close()

        # 인프라 목록을 JSON 응답으로 반환
        infra_names = [record['infra_name'] for record in infra_list]
        return JSONResponse(content={"infra_list": infra_names}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# 설비에 해당하는 보고서 제출 목록 가져오기(날짜 기준 오름차순)
@app.get("/api/posted-reports")
async def get_posted_reports(request: Request, infra: str = None):
    try:
        # 인프라 이름 파라미터 확인
        if not infra:
            raise HTTPException(status_code=400, detail="Infra name is missing in query parameters")
        infra_name = infra

        # 데이터베이스 연결
        conn = await connect_db()

        # 보고서 제출 목록 조회
        reports = await conn.fetch('''
            SELECT * FROM posted_reports
            WHERE report_form_id IN (
                SELECT report_form_id FROM report_forms
                WHERE infra_id = (
                    SELECT infra_id FROM infras WHERE infra_name = $1
                )
            )
            ORDER BY start_time ASC;
        ''', infra_name)

        # 데이터베이스 연결 종료
        await conn.close()

        # 보고서 목록을 JSON 응답으로 반환
        reports_list = [{
            'posted_report_id': report['posted_report_id'],
            'posted_report_path': report['posted_report_path'],
            'start_time': report['start_time'],
            'end_time': report['end_time'],
            'user_name': report['user_name']
        } for report in reports]

        return JSONResponse(content={"posted_reports": reports_list}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# 설비의 특정 날짜 보고서 가져오기
@app.get("/api/posted-reports")
async def get_posted_reports(request: Request, infra: str = None, Unixtime: int = None):
    # 인프라 이름 파라미터 확인
    if not infra:
        raise HTTPException(status_code=400, detail="Infra name is missing in query parameters")
    
    # Unixtime 파라미터 확인
    if not Unixtime:
        raise HTTPException(status_code=400, detail="Unixtime is missing in query parameters")
    
    # Unix timestamp를 datetime 객체로 변환
    try:
        report_date = datetime.fromtimestamp(Unixtime, tz=pytz.utc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Unixtime: {str(e)}")
    
    try:
        # DB 연결
        conn = await connect_db()
        
        # 인프라 이름에 해당하는 infra_id 가져오기
        infra_id = await conn.fetchval('SELECT infra_id FROM infras WHERE infra_name = $1', infra)
        
        if not infra_id:
            raise HTTPException(status_code=404, detail=f'Infra "{infra}" not found')
        
        # 특정 날짜에 해당하는 보고서 조회
        reports = await conn.fetch('''
            SELECT * FROM posted_reports
            WHERE report_form_id IN (
                SELECT report_form_id FROM report_forms
                WHERE infra_id = $1
            ) AND start_time <= to_timestamp($2) AND end_time >= to_timestamp($2)
        ''', infra_id, Unixtime)
        
        # 데이터베이스 연결 종료
        await conn.close()

        return JSONResponse(content={"posted_reports": reports}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# 점검 완료 결과를 DB 및 minIO에 저장
@app.post("/api/report")
async def submit_report(request: Request):
    try:
        data = await request.json()
    # Extract data from JSON
        start_time = int(data.get('start_time'))
        end_time = int(data.get('end_time'))
        report_form_id = int(data.get('report_form_id'))
        infra_name = data.get('infra')
        inspection_list = data.get('inspection_list')
    # Connect to the database
        conn = await connect_db()

        last_posted_report_id = await conn.fetchval('''
            SELECT count(*) FROM posted_reports;
        ''')

        # 1, 2 무결성 보장해야 함
        # 1
        posted_report_path = "/" + str(os.environ['MINIO_BUCKET']) + "/" + str(last_posted_report_id)

        # Insert data into posted_reports table
        posted_report_id = await conn.fetchval('''
            INSERT INTO posted_reports (posted_report_path, report_form_id, start_time, end_time, user_name)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING posted_report_id
        ''', posted_report_path, report_form_id, start_time, end_time, "0000")
        await conn.close()

        # 2
        # Save original JSON data to MinIO bucket
        # 파일명: {posted_report_id}.json
        data_json = json.dumps(data)
        file_name = f"{posted_report_id}.json"
        with io.BytesIO(data_json.encode('utf-8')) as data_file:
            minio_client.put_object(os.environ['MINIO_BUCKET'], file_name, data_file, length=-1, part_size=10*1024*1024, content_type="application/json")

        return JSONResponse(content={"message": "Report submitted successfully", "posted_report_id": posted_report_id}, status_code=200)
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=f"Error submitting report: {str(e)}")

# 설비 추가
@app.post("/api/infra")
async def add_infra(request: Request, infra: str = None):
    infra_name = infra

    if not infra_name:
        raise HTTPException(status_code=400, detail="Infra name is missing in query parameters")

    # DB 연결
    conn = await connect_db()

    # infras에 infra_name row 추가
    await conn.execute("INSERT INTO infras (infra_name) VALUES ($1)", infra_name)

    # DB 연결 종료
    await conn.close()


    return {"message": "Infra added successfully."}

# 설비에 대한 특정 보고서 양식을 가져오기 (보고서 양식 수정을 고려할 것인지 확인 필요)
@app.get("/api/report-form")
async def get_report_forms(request: Request, infra: str = None, report_form_id: int = None):
    infra_name = infra

    if not infra_name:
        raise HTTPException(status_code=400, detail="Infra name is missing in query parameters")
    try:
        conn = await connect_db()

        # Check if the infra_name exists
        infra_id = await conn.fetchval('''
            SELECT infra_id FROM infras WHERE infra_name = $1
        ''', infra_name)
        if not infra_id:
            raise HTTPException(status_code=404, detail=f"Infra with name '{infra_name}' not found")

        # Check if the report_form_id exists for the given infra_name
        report_exists = await conn.fetchval('''
            SELECT 1 FROM report_forms WHERE infra_id = $1 AND report_form_id = $2
        ''', infra_id, report_form_id)
        if not report_exists:
            raise HTTPException(status_code=404, detail=f"Report form with id '{report_form_id}' not found for infra '{infra_name}'")

        # Retrieve report form data
        report_form_data = await conn.fetch('''
            SELECT 
                t.topic_form_name, 
                t.image_required, 
                array_agg(
                    json_build_object(
                        'instruction', i.instruction,
                        'instruction_type', i.instruction_type,
                        'options', i.options,
                        'answer', i.answer
                    )
                ) AS instruction_list
            FROM 
                topic_forms t
            JOIN 
                instruction_forms i ON t.topic_form_id = i.topic_form_id
            WHERE 
                t.report_form_id = $1
            GROUP BY 
                t.topic_form_name, t.image_required
        ''', report_form_id)
        print(report_form_data)

        if not report_form_data:
            raise HTTPException(status_code=404, detail=f"No report form data found for report form id '{report_form_id}'")

        # Format the response data
        response_data = {
            "infra_name": infra_name,
            "report_form_id": report_form_id,
            "inspection_list": []
        }
        for record in report_form_data:
            inspection = {
                "topic": record['topic_form_name'],
                "instruction_list": [],
                "image_required": record['image_required']
            }
            for instruction_json in record['instruction_list']:
                instruction = json.loads(instruction_json)
                instruction_data = {
                    "instruction": instruction['instruction'],
                    "instruction_type": instruction['instruction_type'],
                    "options": instruction['options'],
                    "answer": None
                }
                inspection["instruction_list"].append(instruction_data)
            response_data["inspection_list"].append(inspection)



        await conn.close()
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=f"Error retrieving report form data: {str(e)}")

# 설비에 대한 모든 보고서 양식을 가져오기
@app.get("/api/report-forms")
async def get_report_forms(request: Request, infra: str):
    infra_name = infra

    if not infra_name:
        raise HTTPException(status_code=400, detail="Infra name is missing in query parameters")

    try:
        conn = await connect_db()

        # Check if the infra_name exists
        infra_id = await conn.fetchval('''
            SELECT infra_id FROM infras WHERE infra_name = $1
        ''', infra_name)
        if not infra_id:
            raise HTTPException(status_code=404, detail=f"Infra with name '{infra_name}' not found")

        # Retrieve report form ids for the given infra_name
        report_form_ids = await conn.fetch('''
            SELECT report_form_id FROM report_forms WHERE infra_id = $1
        ''', infra_id)

        # Format the response data
        response_data = {
            "infra_name": infra_name,
            "report_form_ids": [row['report_form_id'] for row in report_form_ids]
        }

        await conn.close()
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=f"Error retrieving report form data: {str(e)}")
