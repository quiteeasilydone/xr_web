from pydantic import BaseModel
from typing import List, Optional


# 회원가입 요청 바디 모델
class SignUpRequest(BaseModel):
    email: str
    user_name: str
    employee_identification_number: int

# 로그인 요청 데이터 모델 정의
class LoginRequest(BaseModel):
    email: str