"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError

from app.dependencies import get_db
from app.models.user import User
from app.schemas.user import Token, UserResponse
from app.utils.auth import verify_password, create_access_token, decode_token

router = APIRouter(tags=[])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        User object of authenticated user

    Raises:
        HTTPException 401: If token is invalid or user doesn't exist
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode token and get username
        token_data = decode_token(token)
        username = token_data.username

        if username is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Get user from database
    user = db.query(User).filter(User.username == username).first()

    if user is None:
        raise credentials_exception

    return user


async def get_current_user_optional(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme_optional)
) -> User | None:
    """
    Optional authentication dependency based on AUTH_MODE setting

    Args:
        token: JWT token from Authorization header (optional if AUTH_MODE=public)
        db: Database session

    Returns:
        User object if authenticated, None if AUTH_MODE=public and no token

    Raises:
        HTTPException 401: If AUTH_MODE=token and token is invalid or missing
    """
    # Import settings inside function to allow test mocking
    from app.config import settings

    # In token mode, authentication is required
    if settings.AUTH_MODE == "token":
        # Token is required in token mode
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Validate token
        return await get_current_user(token=token, db=db)

    # In public mode, authentication is optional
    if token:
        # If token is provided, try to authenticate
        try:
            token_data = decode_token(token)
            username = token_data.username
            if username:
                user = db.query(User).filter(User.username == username).first()
                if user:
                    return user
        except JWTError:
            pass

    # No token or invalid token in public mode - return None
    return None


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


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information

    Args:
        current_user: Current authenticated user from JWT token

    Returns:
        UserResponse with username and role (no password)

    Raises:
        HTTPException 401: If token is invalid
    """
    return current_user
