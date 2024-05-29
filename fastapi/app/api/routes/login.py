from fastapi import APIRouter
from fastapi.security import OAuth2PasswordBearer
from fastapi import FastAPI, Request, HTTPException, Depends
from jose import jwt
from db import postgres_connection
from starlette.status import HTTP_202_ACCEPTED
from schemas import request_body

import os
import requests

router = APIRouter()




## 구글 SSO 연동
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
GOOGLE_CLIENT_ID = os.environ['XR_WEB_SERVER_GOOGLE_CLIENT_ID']
GOOGLE_CLIENT_SECRET = os.environ['XR_WEB_SERVER_GOOGLE_CLIENT_SECRET']
GOOGLE_REDIRECT_URI = os.environ['XR_WEB_SERVER_GOOGLE_REDIRECT_URI']

# Initiating the Google login flow
# redirect_uri 끝에 query param 으로 code가 붙는데, 이걸 /api/auth/google 에 같이 요청하면 로그인 한 사용자 정보를 돌려줌
@router.get("/api/login/google")
async def login_google(request: Request):
    return {
        "url": f"https://accounts.google.com/o/oauth2/v2/auth/oauthchooseaccount?client_id={GOOGLE_CLIENT_ID}"
    f"&redirect_uri={GOOGLE_REDIRECT_URI}&response_type=code&scope=email%20profile&service=lso&o2v=2&ddm=0&flowName=GeneralOAuthFlow"
    }

# Exchanging the authorization code for an access token
@router.get("/api/auth/google")
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
@router.get("/api/token")
async def get_token(token: str = Depends(oauth2_scheme)):
    return jwt.decode(token, GOOGLE_CLIENT_SECRET, algorithms=["HS256"])

# 회원가입
@router.post("/api/sign-up")
async def sign_up(request: request_body.SignUpRequest):
    conn = await postgres_connection.connect_db()
    # body에 email, user_name, employee_identification_number 담아옴
    # 이걸 DB user table에 저장
    # 이미 row 있으면 저장 안하고 http status code 202 돌려주면서 에러 메세지도 돌려줌
    # 202 - Accepted - 허용됨 - 요청은 접수하였지만, 처리가 완료되지 않았다. 응답 헤더의 Location, Retry-After를 참고하여 클라이언트는 다시 요청을 보냅니다.
    try:
        # 사용자 존재 여부 확인
        existing_user = await conn.fetchrow(
            "SELECT user_id FROM users WHERE email = $1 OR employee_identification_number = $2",
            request.email, request.employee_identification_number
        )
        if existing_user:
            await conn.close()
            raise HTTPException(
                status_code=HTTP_202_ACCEPTED,
                detail="User with this email or employee identification number already exists."
            )

        # 새로운 사용자 삽입
        await conn.execute(
            "INSERT INTO users (email, user_name, employee_identification_number) VALUES ($1, $2, $3)",
            request.email, request.user_name, request.employee_identification_number
        )
        await conn.close()

        return {"message": "User registered successfully"}
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=f"Error registering user: {str(e)}")

# 로그인
@router.post("/api/login")
async def login(request: request_body.LoginRequest):
    conn = await postgres_connection.connect_db()
    # body에 email 담아서 받음
    
    # DB에 email이 있으면(회원가입 된 상태면), 이름이랑 사원번호 돌려 줌
    # DB에 email이 없으면 401 Unauthorized 돌려줌
    # 클라이언트는 이걸 받고 회원가입하라고 리다이렉션
    try:
        # 사용자 정보 조회
        user = await conn.fetchrow(
            "SELECT user_name, employee_identification_number FROM users WHERE email = $1",
            request.email
        )
        await conn.close()

        if user:
            return {
                "user_name": user['user_name'],
                "employee_identification_number": user['employee_identification_number']
            }
        else:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Email not registered. Please sign up."
            )
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")



