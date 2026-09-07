from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import data, auth, users, dashboard, injection_quantity, export, health, explorer, catalog

app = FastAPI(
    title="EPÄ°AÅ Data Platform API",
    description="Centralized data platform for EPÄ°AÅ integrations with auto-partitioning and TGT management.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, this should be specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data.router, prefix="/api/v1/data", tags=["Data"])
app.include_router(injection_quantity.router, prefix="/api/v1/generation/injection-quantity", tags=["Injection Quantity"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(export.router, prefix="/api/v1/export", tags=["Export"])
app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])
app.include_router(explorer.router, prefix="/api/v1/explorer", tags=["Explorer"])
app.include_router(catalog.router, prefix="/api/v1/catalog", tags=["Catalog"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
