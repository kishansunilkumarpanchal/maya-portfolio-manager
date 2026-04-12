from fastapi import FastAPI

from app.api.v1.api import api_router
from app.core.config import settings


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        debug=settings.DEBUG,
    )
    app.include_router(api_router)
    return app


app = create_application()

