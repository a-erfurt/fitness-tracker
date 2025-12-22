from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas.auth import RegisterRequest, RegisterResponse
from app.api.deps import get_db
from app.core.security import hash_password
from app.models.user import User

from app.api.schemas.login import LoginRequest, TokenResponse
from app.core.security import verify_password
from app.core.tokens import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> RegisterResponse:
    # 1) Prüfen, ob Email schon existiert
    existing_user = (
        db.query(User)
        .filter(User.email == str(payload.email))
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # 2) Passwort hashen
    password_hash = hash_password(payload.password)

    # 3) User erstellen
    user = User(
        email=str(payload.email),
        password_hash=password_hash,
    )

    # 4) In DB speichern
    db.add(user)
    db.commit()
    db.refresh(user)

    # 5) Response
    return RegisterResponse(
        id=user.id,
        email=payload.email,
    )

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = db.query(User).filter(User.email == str(payload.email)).first()

    if not user or not verify_password(payload.password, str(user.password_hash)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    access_token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=access_token)