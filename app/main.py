from fastapi import FastAPI

from app.routes.hrms import router as hrms_router


app = FastAPI(title="Integration Core API")
app.include_router(hrms_router)
