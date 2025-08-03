from fastapi import APIRouter
router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    """
    This endpoint can be used by monitoring services to check if the application is running.
    """
    return {
                "status": "ok", 
                "message": "Health check passed"
            }