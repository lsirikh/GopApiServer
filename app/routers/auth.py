"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.user import User
from app.schemas.user import Token
from app.utils.auth import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login endpoint - authenticate user and return JWT token

    Args:
        form_data: OAuth2 form with username and password
        db: Database session

    Returns:
        Token with access_token and token_type

    Raises:
        HTTPException 401: If credentials are invalid
    """
    # Find user by username
    user = db.query(User).filter(User.username == form_data.username).first()

    # Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT token
    access_token = create_access_token(data={"sub": user.username})

    return Token(access_token=access_token, token_type="bearer")
