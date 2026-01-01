import os
import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Health Tracking API Gateway")

# Allow the frontend (and other callers) to reach the gateway from the browser
FRONTEND_ORIGINS = os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
allowed_origins = [origin.strip() for origin in FRONTEND_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8000")
HEALTH_SERVICE_URL = os.getenv("HEALTH_SERVICE_URL", "http://health_service:8000")
ANALYTICS_SERVICE_URL = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics_service:8000")

async def forward_request(url: str, request: Request):
    client = httpx.AsyncClient()
    try:
        # Forward query params, headers (excluding host), and body
        params = dict(request.query_params)
        headers = dict(request.headers)
        headers.pop("host", None)
        headers.pop("content-length", None) # Let httpx handle content-length
        
        # Read body
        body = await request.body()

        response = await client.request(
            request.method,
            url,
            params=params,
            headers=headers,
            content=body
        )
        return response
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
    finally:
        await client.aclose()

@app.get("/")
async def root():
    return {"message": "Health Tracking API Gateway is running"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# -------------------------------------------------------------------------
# Generic Proxy Routes
# -------------------------------------------------------------------------

@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_auth(request: Request, path: str):
    return await forward_request(f"{AUTH_SERVICE_URL}/{path}", request)

@app.api_route("/health/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_health(request: Request, path: str):
    # Forwards /health/data -> health_service/data
    return await forward_request(f"{HEALTH_SERVICE_URL}/{path}", request)

@app.api_route("/analytics/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_analytics(request: Request, path: str):
    return await forward_request(f"{ANALYTICS_SERVICE_URL}/{path}", request)
