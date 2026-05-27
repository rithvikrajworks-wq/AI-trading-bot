from fastapi import APIRouter

router = APIRouter()

@router.get(
    "/health", 
    summary="Health Check",
    description="Returns the status of the API to confirm the service is running."
)
async def health_check():
    return {
        "status": "healthy", 
        "service": "Stock Analysis API"
    }
