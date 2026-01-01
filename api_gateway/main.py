import os
import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

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
        return Response(content=response.content, status_code=response.status_code, headers=dict(response.headers))
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
    finally:
        await client.aclose()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Health Tracking API Gateway",
        version="1.0.0",
        description="Gateway for Health Tracking System",
        routes=[],
    )

    services = [
        (AUTH_SERVICE_URL, "/auth", "Auth Service"),
        (HEALTH_SERVICE_URL, "/health", "Health Service"),
        (ANALYTICS_SERVICE_URL, "/analytics", "Analytics Service"),
    ]

    openapi_schema["paths"] = {}
    openapi_schema["components"] = {}
    openapi_schema["tags"] = []

    # Keep track of the primary auth scheme (from Auth Service) to reuse in others
    primary_auth_scheme_name = None

    for service_url, prefix, tag_name in services:
        try:
            response = httpx.get(f"{service_url}/openapi.json", timeout=2.0)
            response.raise_for_status()
            service_schema = response.json()

            # Helper to recursively update $ref
            def update_refs(obj, tag_name):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key == "$ref" and isinstance(value, str) and value.startswith("#/components/schemas/"):
                            component_name = value.split("/")[-1]
                            unique_name = f"{tag_name.replace(' ', '')}_{component_name}"
                            obj[key] = f"#/components/schemas/{unique_name}"
                        else:
                            update_refs(value, tag_name)
                elif isinstance(obj, list):
                    for item in obj:
                        update_refs(item, tag_name)

            # Update references to point to the new unique names
            update_refs(service_schema, tag_name)

            # ---- COMPONENTS (safe merge) ----
            for comp_type, comps in service_schema.get("components", {}).items():
                openapi_schema["components"].setdefault(comp_type, {})
                for name, schema in comps.items():
                    unique_name = f"{tag_name.replace(' ', '')}_{name}"
                    
                    # Special handling for Security Schemes to UNIFY them
                    if comp_type == "securitySchemes" and schema.get("type") == "oauth2":
                        if tag_name == "Auth Service":
                            # This is our PRIMARY scheme.
                            primary_auth_scheme_name = unique_name
                            
                            # Fix logic for tokenUrl
                            for flow_name, flow in schema.get("flows", {}).items():
                                if "tokenUrl" in flow:
                                     token_url = flow["tokenUrl"]
                                     if not token_url.startswith("/") and not token_url.startswith("http"):
                                         flow["tokenUrl"] = f"/auth/{token_url}"
                            
                            openapi_schema["components"][comp_type][unique_name] = schema
                        else:
                            # It's a duplicate OAuth2 scheme from another service. SKIP IT.
                            # We will map references to primary_auth_scheme_name instead.
                            continue
                    else:
                        # Normal component (Schema, etc.) - just add it
                        openapi_schema["components"][comp_type][unique_name] = schema

            # ---- TAGS ----
            openapi_schema["tags"].append({
                "name": tag_name,
                "description": f"Endpoints from {tag_name}"
            })

            # ---- PATHS ----
            for path, methods in service_schema.get("paths", {}).items():
                new_path = f"{prefix}{path}"
                for method, op in methods.items():
                    if isinstance(op, dict):
                        op.setdefault("tags", [])
                        op["tags"].append(tag_name)
                        
                        # Fix Operation ID collision
                        if "operation_id" in op:
                            op["operationId"] = f"{tag_name.replace(' ', '')}_{op['operationId']}"
                        
                        # Update Security Requirements
                        if "security" in op:
                            new_security = []
                            for sec_req in op["security"]:
                                new_sec_req = {}
                                for sec_name, sec_scopes in sec_req.items():
                                    # Check if this security requirement points to an OAuth2 scheme
                                    is_oauth2 = False
                                    if "components" in service_schema and "securitySchemes" in service_schema["components"]:
                                        scheme = service_schema["components"]["securitySchemes"].get(sec_name)
                                        if scheme and scheme.get("type") == "oauth2":
                                            is_oauth2 = True
                                    
                                    # If it's OAuth2 and we have a primary scheme, USE IT.
                                    if is_oauth2 and primary_auth_scheme_name:
                                        new_sec_req[primary_auth_scheme_name] = sec_scopes
                                    else:
                                        # Use the prefixed name (local fallback)
                                        unique_sec_name = f"{tag_name.replace(' ', '')}_{sec_name}"
                                        new_sec_req[unique_sec_name] = sec_scopes
                                new_security.append(new_sec_req)
                            op["security"] = new_security

                openapi_schema["paths"][new_path] = methods

        except Exception as e:
            print(f"Swagger fetch failed from {service_url}: {e}")



    # ---- SERVERS ----
    openapi_schema["servers"] = [
        {"url": "/", "description": "API Gateway"}
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/")
async def root():
    return {"message": "Health Tracking API Gateway is running"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# -------------------------------------------------------------------------
# Generic Proxy Routes
# -------------------------------------------------------------------------

@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"], include_in_schema=False, operation_id="proxy_auth")
async def proxy_auth(request: Request, path: str):
    return await forward_request(f"{AUTH_SERVICE_URL}/{path}", request)

@app.api_route("/health/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"], include_in_schema=False, operation_id="proxy_health")
async def proxy_health(request: Request, path: str):
    # Forwards /health/data -> health_service/data
    return await forward_request(f"{HEALTH_SERVICE_URL}/{path}", request)

@app.api_route("/analytics/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"], include_in_schema=False, operation_id="proxy_analytics")
async def proxy_analytics(request: Request, path: str):
    return await forward_request(f"{ANALYTICS_SERVICE_URL}/{path}", request)

