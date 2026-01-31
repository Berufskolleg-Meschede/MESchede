from fastapi import APIRouter

router = APIRouter(
    prefix="/sites",
    tags=["sites"]
)

@router.get("/")
def list_sites():
    return {"message": "Hello World"}

@router.get("/{site_id}")
def get_site(site_id: str):
