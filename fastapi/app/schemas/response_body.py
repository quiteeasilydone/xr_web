from pydantic import BaseModel
from typing import List, Optional


class User(BaseModel):
    employee_identification_number: int
    company_name: str
    email: str

class InfraBase(BaseModel):
    infra_name : str
    company_name : str

class InfrasResponseModel(BaseModel):
    infras : List[InfraBase]

class InfraCreate(InfraBase):
    pass

class Infra(InfraBase):
    infra_id: int

    class Config:
        orm_model = True


class InstructionModel(BaseModel):
    instruction: str
    instruction_type: str
    img_url: Optional[str]
    options: List[str]
    answer: List[str]

class TopicModel(BaseModel):
    topic: str
    instruction_list: List[InstructionModel]

class ReportModel(BaseModel):
    start_time: str
    end_time: str
    company_name: str
    infra: str
    user_name: str
    memo : str
    inspection_list: List[TopicModel]

class PostedReportResponseModel(BaseModel):
    posted_report_id: int
    posted_report_path: str
    report_form_id: int
    start_time: str
    end_time: str
    company_name: str
    user_name: str

class PostedReportsResponseModel(BaseModel):
    posted_reports : List[PostedReportResponseModel]

class ReportResponseModel(BaseModel):
    message: str
    report: ReportModel

    class Config:
        schema_extra = {
            "example": {
                "message": "Report fetched successfully",
                "report": {
                    "start_time": "2024-10-21T09:00:00",
                    "end_time": "2024-10-21T17:00:00",
                    "company_name": "hyeon",
                    "infra": "hyeon",
                    "user_name": "Jin Yongmin_1",
                    "memo" : "check",
                    "inspection_list": [
                        {
                            "topic": "topic1",
                            "instruction_list": [
                                {
                                    "instruction": "check",
                                    "instruction_type": "check",
                                    "img_url": "",
                                    "options": [],
                                    "answer": [
                                        "true"
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
        }

class DBReportFormModel(BaseModel):
    infra_name: str
    last_modified_time: str
    report_form_id: int
    inspection_list: List[TopicModel]

class DBReportsResponseModel(BaseModel):
    reports : List[DBReportFormModel]
class DBReportResponseModel(BaseModel):
    report_form: DBReportFormModel

    class Config:
        schema_extra = {
            "example": {
                "report_form": {
                    "infra_name": "hyeon",
                    "last_modified_time": "2024-10-21T17:00:00",
                    "report_form_id": 1,
                    "inspection_list": [
                        {
                            "topic": "topic1",
                            "instruction_list": [
                                {
                                    "instruction": "check",
                                    "instruction_type": "check",
                                    "img_url": "",
                                    "options": [],
                                    "answer": ["true"]
                                }
                            ]
                        }
                    ]
                }
            }
        }

class MediaFileResponse(BaseModel):
    media_id: int
    infra_name: str
    company_name: str
    file_type: str
    file_name: str

    class Config:
        orm_mode = True

class MediaFilesResponse(BaseModel):
    media_files : List[MediaFileResponse]


class UserLocationResponse(BaseModel):
    android_uuid: str
    company_name: str
    latitude: int
    longitude: int