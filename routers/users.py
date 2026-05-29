from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from database import get_db
from models import User
from schemas import UserCreate, UserPublic, Token, UserProfile
from auth import get_password_hash, verify_password, create_access_token
from dependencies import CurrentUser


router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserPublic)
def register_user(user: UserCreate, db: Annotated[Session,Depends(get_db)]):
    existing_username = db.query(User).filter( User.username == user.username).first()
    if existing_username :
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    existing_email = db.query(User).filter( User.email == user.email).first()
    if existing_email :
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user.password)

    new_user = User(
        username = user.username,
        email = user.email,
        hashed_password = hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user



@router.post("/token", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm,Depends()], db: Annotated[Session,Depends(get_db)]):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = create_access_token(
        data={"sub": user.username}
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }



@router.get("/me",response_model=UserPublic)
def get_me(current_user: CurrentUser):
    return current_user


@router.get("/profile", response_model=UserProfile)
def get_profile(
    current_user: CurrentUser
):

    return current_user