from fastapi import APIRouter
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from fastapi.responses import HTMLResponse

from schemas.response_body import User as response_user
from schemas.request_body import User as request_user
from schemas.request_body import WearableIdentifier
from schemas.request_body import Company

from typing import List
from db import postgres_connection

import json
import qrcode # QR 코드를 생성하기 위한 라이브러리
import io # QR 코드를 메모리에 저장하기 위한 라이브러리
import base64 # QR 코드를 인코딩하기 위한 라이브러리

router = APIRouter()


# 더미 사용자 생성
@router.post("/api/user")
async def make_dummy_company(request: Request):

    # 임시 company_name 0000
    company_name = "dummy"
    email = "dummy_company12@gmail.com"
    employee_identification_number = 8888

    conn = await postgres_connection.connect_db()

    try:
        await conn.fetch('''
            INSERT INTO users ("company_name", "email", "employee_identification_number")
            VALUES ($1, $2, $3)
        ''', company_name, email, employee_identification_number
        )
        
        await conn.close()
        return JSONResponse(content={"message": "Data saved successfully"}, status_code=200)
        
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=f"Error saving data: {str(e)}")

# DB에 있는 모든 유저 정보 돌려주기
@router.post("/api/users", response_model=List[response_user])
async def login(request: Request):
    conn = await postgres_connection.connect_db()

    try:
        # 모든 유저 정보 조회
        users = await conn.fetch("SELECT user_id, employee_identification_number, company_name, email FROM users")
        await conn.close()

        # 조회된 유저 정보를 리스트로 변환
        user_list = [response_user(**user) for user in users]

        return user_list
    except Exception as e:

        await conn.close()
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")


# qr code 생성 함수
def generate_qr_code(data: str) -> io.BytesIO:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


# 웹에서 호출하면 QR코드화면 호스팅
@router.post("/api/wearable-qr-image")
async def get_qr_image_for_registering(request: Request, body: request_user):
    company_name = body.company_name
    if not company_name:
        raise HTTPException(status_code=400, detail="company name is required")

    try:
        # Generate the QR code with the company name
        qr_data = f"company_name: {company_name}"
        qr_image = generate_qr_code(qr_data)

        return StreamingResponse(qr_image, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating QR code: {str(e)}")


# (로그인 한 사용자가) infra를 입력하면 infra에 해당하는 보고서 양식을 가져갈 수 있도록 QR 이미지 호스팅
@router.post("/api/report-form-qr-image")
async def get_qr_image_for_getting_report_form(request: Request, body: request_user, infra: str):
    company_name = body.company_name

    if not infra:
        raise HTTPException(status_code=400, detail="Infra name is missing in request body")
    if not company_name:
        raise HTTPException(status_code=400, detail="Company name is missing in request body")

    try:
        # 데이터베이스 연결
        conn = await postgres_connection.connect_db()

        # 보고서 양식 데이터 가져오기
        report_form = await conn.fetchrow('''
            SELECT * FROM report_forms
            WHERE infra_id = (
                SELECT infra_id FROM infras WHERE infra_name = $1 AND company_name = $2
            )
            ORDER BY last_modified_time DESC
            LIMIT 1;
        ''', infra, company_name)

        if not report_form:
            raise HTTPException(status_code=404, detail=f'No report form found for infra "{infra}" and company "{company_name}"')

        # Retrieve inspection list
        inspection_list = await conn.fetch('''
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
        ''', report_form['report_form_id'])

        # Format the response data
        response_data = {
            "infra_name": infra,
            "report_form_id": report_form['report_form_id'],
            "inspection_list": []
        }

        for record in inspection_list:
            inspection = {
                "topic": record["topic_form_name"],
                "instruction_list": [],
                "image_required": record["image_required"]
            }
            for instruction_json in record["instruction_list"]:
                instruction = json.loads(instruction_json)
                instruction_data = {
                    "instruction": instruction["instruction"],
                    "instruction_type": instruction["instruction_type"],
                    "options": instruction["options"],
                    "answer": instruction["answer"]
                }
                inspection["instruction_list"].append(instruction_data)
            response_data["inspection_list"].append(inspection)

        # 데이터베이스 연결 종료
        await conn.close()

        # JSON 데이터를 문자열로 변환
        report_form_json = json.dumps(response_data)

        # QR 코드 생성
        qr_image = generate_qr_code(report_form_json)
        
        # # 로컬 파일로 저장
        # file_path = f"/usr/src/fastapi_app/api/{infra}_report_form_qr.png"
        # with open(file_path, "wb") as file:
        #     file.write(qr_image.getvalue())

        # QR 코드 이미지 파일 반환
        return StreamingResponse(qr_image, media_type="image/png")



    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# 회사가 가지고 있는 모든 안드로이드 기기의 list return
@router.post("/api/wearable-machine-lists")
async def get_wearable_machine_lists(request: Request, body: Company):
    # wearable_identification INT[] 의 모든 요소를 return
    conn = await postgres_connection.connect_db()

    try:
        # 회사 이름을 통해 wearable_identification 배열 검색
        query = """
        SELECT wearable_identification FROM users 
        WHERE company_name = $1
        """
        result = await conn.fetchrow(query, body.company_name)
        
        if result is None:
            raise HTTPException(status_code=404, detail="Company not found")

        wearable_ids = result['wearable_identification']
        
        return {"wearable_identifications": wearable_ids}
    
    except Exception as e:
        await conn.close()

        # 오류 발생 시 오류 메시지 반환
        raise HTTPException(status_code=500, detail=f"Error occur: {str(e)}")

@router.get("/api/wearable-machine-check/{android_UUID}")
async def get_wearable_machine_check(android_UUID : str):
    conn = await postgres_connection.connect_db()
    
    try:
        query = """
        SELECT *
        FROM users
        WHERE $1 = ANY(wearable_identification);
        """
        
        result = await conn.fetchrow(query, android_UUID)
        
        if result is None:
            return {"result" : False}
        else:
            return {"result" : True}
        
    except Exception as e:
        await conn.close()
        
        raise HTTPException(status_code=500, detail=f"Error occur: {str(e)}")
