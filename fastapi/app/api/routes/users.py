from fastapi import APIRouter
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from db import postgres_connection

router = APIRouter()


# 더미 사용자 생성
@router.post("/api/user")
async def make_dummy_user(request: Request):

    # 임시 user_name 0000
    user_name = "0000"
    email = "dummy@dummy.com"

    conn = await postgres_connection.connect_db()

    try:
        await conn.fetch('''
            INSERT INTO users ("user_name", "email")
            VALUES ($1, $2)
        ''', user_name, email
        )
        
        await conn.close()
        return JSONResponse(content={"message": "Data saved successfully"}, status_code=200)
        
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=f"Error saving data: {str(e)}")