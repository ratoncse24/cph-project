from fastapi import APIRouter

from app.api.v1 import user, health, client, role_options

# Create a main API router for version 1
# All routes included here will be prefixed by whatever prefix is
# given when this `api_router_v1` is included in main.py (e.g., /api/v1)
api_router_v1 = APIRouter()

# Include v1 routers
# The prefixes defined here will be relative to the prefix of api_router_v1
api_router_v1.include_router(user.router, tags=["Users"])
api_router_v1.include_router(health.router)  # Add health check route
api_router_v1.include_router(client.router, tags=["Clients"])
api_router_v1.include_router(role_options.router, tags=["Role Options"])

# You can add more v1 routers here if needed in the future
# e.g., from app.api.v1 import orders
# api_router_v1.include_router(orders.router, prefix="/orders", tags=["Orders"])