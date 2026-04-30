from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.backend.database import get_db
from app.backend.models.user import User, UserProfile
from app.backend.schemas.user import UserCreate, UserLogin, TokenResponse, UserResponse
from app.backend.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    db.flush()  # get user.id before commit

    # Create empty profile
    profile = UserProfile(user_id=user.id)
    db.add(profile)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/demo", response_model=TokenResponse)
def demo_login(db: Session = Depends(get_db)):
    """Return a token for the shared demo account, creating it if needed."""
    demo_email = "demo@hoopdev.app"
    demo_username = "Demo Player"
    demo_password = "hoopdev-demo-2026"

    user = db.query(User).filter(User.email == demo_email).first()
    if not user:
        user = User(
            username=demo_username,
            email=demo_email,
            hashed_password=hash_password(demo_password),
        )
        db.add(user)
        db.flush()
        profile = UserProfile(
            user_id=user.id,
            skill_level="intermediate",
            position="PG",
            goals=["shooting", "ball_handling"],
        )
        db.add(profile)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(body: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))
