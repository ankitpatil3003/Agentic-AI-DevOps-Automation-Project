# app/api/main.py

from fastapi import FastAPI
from app.utils.logger import init_logger
from app.api.routes.execute import router as execute_router
from app.api.routes.approve import router as approve_router
from app.api.routes.reject import router as reject_router
from app.api.routes.tasks import router as tasks_router


init_logger()

app = FastAPI(
    title="Agentic AI DevOps Service",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs"
)

app.include_router(execute_router)  # /api/v1/execute
app.include_router(approve_router)  # /api/v1/plans/{id}/approve
app.include_router(reject_router)   # /api/v1/plans/{id}/reject
app.include_router(tasks_router)    # /api/v1/tasks/{id}