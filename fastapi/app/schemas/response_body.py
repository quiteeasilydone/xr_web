from pydantic import BaseModel
from typing import List, Optional


class Instruction_form(BaseModel):
    instruction: str
    instruction_type: str
    options: Optional[List[str]]
    answer: Optional[List[str]]

class Inspection_form(BaseModel):
    topic: str
    instruction_list: List[Instruction_form]
    image_required: bool

class report_form(BaseModel):
    infra: str
    inspection_list: List[Inspection_form]

class InspectedReport(BaseModel):
    start_time: str
    end_time: str
    report_form_id: str
    infra: str
    inspection_list: List[Inspection_form]

class User(BaseModel):
    employee_identification_number: int
    user_name: str
    email: str