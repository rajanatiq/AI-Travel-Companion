import uvicorn
from app.config import settings

if __name__ == "__main__":
    print(f"==================================================")
    print(f" Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f" Server URL: http://localhost:{settings.PORT}")
    print(f" Swagger UI: http://localhost:{settings.PORT}/docs")
    print(f" ReDoc Docs: http://localhost:{settings.PORT}/redoc")
    print(f"==================================================")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
