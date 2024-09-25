from pydantic import BaseModel
from typing import List, Optional


class User(BaseModel):
    employee_identification_number: int
    company_name: str
    email: str

class InfraBase(BaseModel):
    infra_name : str
    company_name : str

class InfraCreate(InfraBase):
    pass

class Infra(InfraBase):
    infra_id: int

    class Config:
        orm_model = True
