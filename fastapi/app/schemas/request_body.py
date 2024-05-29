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

class Instruction_form(BaseModel):
    instruction: str
    instruction_type: str
    options: Optional[List[str]]
    answer: Optional[List[str]]

class Inspection_form(BaseModel):
    topic: str
    instruction_list: List[Instruction_form]
    image_required: bool

class Report_form(BaseModel):
    user_name: str
    infra: str
    inspection_list: List[Inspection_form]

class InspectedReport(BaseModel):
    start_time: str
    end_time: str
    report_form_id: str
    infra: str
    inspection_list: List[Inspection_form]

# 설비에 대한 가장 최근의 보고서 요청 모델 스키마
class Submitted_report_form(BaseModel):
    infra: str
    user_name: str