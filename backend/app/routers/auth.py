from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.auth_service import authenticate_user
from ..core.security import create_access_token
from ..schemas.user import Token, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    token = create_access_token(data={
        "sub": str(user.id),
        "role": user.role
    })
    return Token(
        access_token=token,
        token_type="bearer",
        user=UserOut.model_validate(user),
    )
