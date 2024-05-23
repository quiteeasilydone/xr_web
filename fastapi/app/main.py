from fastapi import APIRouter
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.models import Info

from api.routes import login, infras, posted_reports, reports, users
from uvicorn import run

app = FastAPI(openapi_url="/api/docs/openapi.json")

@app.get("/api/docs", include_in_schema=False)
async def get_documentation():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url="/api/docs/oauth2-redirect.html",
    )

app.include_router(login.router, tags=["login"])
app.include_router(infras.router, tags=["infras"])
app.include_router(posted_reports.router, tags=["posted_reports"])
app.include_router(reports.router, tags=["reports"])
app.include_router(users.router, tags=["users"])

if __name__ == "__main__":
    run(app, host='0.0.0.0', port=80)
