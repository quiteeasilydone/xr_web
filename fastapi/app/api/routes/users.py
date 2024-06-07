from fastapi import APIRouter
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from db import postgres_connection
from schemas.response_body import User as response_user
from schemas.request_body import User as request_user
from typing import List
from fastapi.responses import HTMLResponse
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
@router.get("/api/wearable-qr-image")
async def registration_wearable(request: Request, body: request_user):
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

# 안드로이드 기기에서 식별자 데이터 서버로 전송( {회사 이름, 식별자 데이터} ) - DB에 저장
@router.post("/api/send-wearable-identification")
async def registration_wearable(request: Request):

    # 이 함수에서 {회사 이름, 식별자 데이터} 이 쌍이 이미 있으면
    # "DUP" 의미하는 거 return

    # 없으면
    # 등록하고 등록했다고 하는 정보랑 Return
    # "Successfully registered."

    # 에러나면
    # 에러났다고 return
    # "Error occur." - 에러 원인도 제공

    return 0


# 회사가 가지고 있는 모든 안드로이드 기기의 list return
@router.post("/api/send-wearable-identification")
async def registration_wearable(request: Request):
    # wearable_identification_number INT[] 의 모든 요소를 return

    return 0
