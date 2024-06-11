from pydantic import BaseModel
from typing import List, Optional


# 회원가입 요청 바디 모델
class SignUpRequest(BaseModel):
    email: str
    company_name: str
    employee_identification_number: int

# 로그인 요청 데이터 모델 정의
class LoginRequest(BaseModel):
    email: str

class InstructionForm(BaseModel):
    instruction: str
    instruction_type: str
    options: Optional[List[str]]
    answer: Optional[List[str]]

class InspectionForm(BaseModel):
    topic: str
    instruction_list: List[InstructionForm]
    image_required: bool

class ReportForm(BaseModel):
    company_name: str
    infra: str
    last_modified_time: str
    inspection_list: List[InspectionForm]

class InspectedReport(BaseModel):
    start_time: str
    end_time: str
    company_name: str
    infra: str
    inspection_list: List[InspectionForm]

# 설비에 대한 가장 최근의 보고서 요청 모델 스키마
class SubmittedReportForm(BaseModel):
    infra: str
    company_name: str

class User(BaseModel):
    employee_identification_number: int
    company_name: str
    email: str

# 안드로이드 기기 식별자 정보 모델 wearable-identification
class WearableIdentifier(BaseModel):
    company_name: str
    wearable_identification: str

# 회사 이름 request 모델 
class Company(BaseModel):
    company_name: str

# Infra request 모델
class Infra(BaseModel):
    infra_name: str
    company_name: str