from fastapi import APIRouter
from fastapi.security import OAuth2PasswordBearer
from fastapi import FastAPI, Request, HTTPException, Depends
from jose import jwt

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