from fastapi import APIRouter
from fastapi.security import OAuth2PasswordBearer
from fastapi import FastAPI, Request, HTTPException, Depends
from jose import jwt
from starlette.status import HTTP_202_ACCEPTED, HTTP_401_UNAUTHORIZED
from schemas import request_body
import os
import requests
from schemas.models import User as UserModel
from db.postgres_connection import connect_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
import uuid

router = APIRouter()

## 구글 SSO 연동
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
GOOGLE_CLIENT_ID = os.environ['XR_WEB_SERVER_GOOGLE_CLIENT_ID']
GOOGLE_CLIENT_SECRET = os.environ['XR_WEB_SERVER_GOOGLE_CLIENT_SECRET']
GOOGLE_REDIRECT_URI = os.environ['XR_WEB_SERVER_GOOGLE_REDIRECT_URI']

# 구글 로그인 플로우 시작
@router.get("/api/login/google", summary="구글 로그인 시작", description="구글 로그인 플로우를 시작하기 위한 URL을 반환합니다.")
async def login_google(request: Request):
    return {
        "url": f"https://accounts.google.com/o/oauth2/v2/auth/oauthchooseaccount?client_id={GOOGLE_CLIENT_ID}"
    f"&redirect_uri={GOOGLE_REDIRECT_URI}&response_type=code&scope=email%20profile&service=lso&o2v=2&ddm=0&flowName=GeneralOAuthFlow"
    }

# 인증 코드를 액세스 토큰으로 교환
@router.get("/api/auth/google", summary="구글 인증", description="구글로부터 받은 코드를 액세스 토큰으로 교환하고 사용자 정보를 반환합니다.")
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

# JWT 토큰 검증
@router.get("/api/token", summary="JWT 토큰 검증", description="JWT 토큰을 디코딩하고 검증합니다.")
async def get_token(token: str = Depends(oauth2_scheme)):
    return jwt.decode(token, GOOGLE_CLIENT_SECRET, algorithms=["HS256"])

# 회원가입
@router.post("/api/sign-up", summary="회원가입", description="새로운 사용자를 등록합니다. 동일한 이메일이나 사원 번호가 있는 사용자는 등록되지 않습니다.")
async def sign_up(request: request_body.SignUpRequest, db: AsyncSession = Depends(connect_db)):
    print('call login method')
    try:
        existing_user = await db.execute(
            select(UserModel).where(
                (UserModel.email == request.email) | 
                (UserModel.employee_identification_number == request.employee_identification_number)
            )
        )
        existing_user = existing_user.scalars().first()

        if existing_user:
            raise HTTPException(
                status_code=HTTP_202_ACCEPTED,
                detail="User with this email or employee identification number already exists."
            )

        # 디폴트 uuid 생성
        uuid_list = [str(uuid.uuid4())]
        # 새로운 사용자 삽입
        new_user = UserModel(
            email=request.email,
            company_name=request.company_name,
            employee_identification_number=request.employee_identification_number,
            # TODO wearable_uuid 디폴트로 추가
            wearable_identification = uuid_list
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return {"message": "User registered successfully"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error registering user: {str(e)}")

# 로그인
@router.post("/api/login", summary="로그인", description="이메일로 로그인합니다. 등록되지 않은 이메일일 경우 401 에러를 반환합니다.")
async def login(request: request_body.LoginRequest, db: AsyncSession = Depends(connect_db)):
    try:
        user = await db.execute(
            select(UserModel).where(UserModel.email == request.email)
        )
        user = user.scalars().first()

        if user:
            return {
                "company_name": user.company_name,
                "employee_identification_number": user.employee_identification_number
            }
        else:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Email not registered. Please sign up."
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")
