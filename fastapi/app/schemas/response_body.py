from pydantic import BaseModel
from typing import List, Optional


class User(BaseModel):
    employee_identification_number: int
    user_name: str
    email: str