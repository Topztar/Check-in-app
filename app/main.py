from fastapi import FastAPI
from fastapi.responses import JSONResponse
import sys

def create_app() -> FastAPI:
    app = FastAPI(
        title="Enterprise Multi-Tenant Employee Attendance SaaS",
        description="Backend API for attendance tracking with biometric and geofencing capabilities.",
        version="1.0.0"
    )

    @app.get("/health", summary="Health Check")
    async def health_check():
        return JSONResponse(content={"status": "ok", "message": "服務運作正常"})

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
