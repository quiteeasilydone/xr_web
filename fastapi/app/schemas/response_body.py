from pydantic import BaseModel
from typing import List, Optional


class User(BaseModel):
    employee_identification_number: int
    company_name: str
    email: str