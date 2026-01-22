from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models import User, Student #College
from app.schemas import StudentSignup, UserResponse, Token, UserInToken, MessageResponse
from app.dependencies import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def signup(student_data: StudentSignup, db: Session = Depends(get_db)):
    """
    Register a new student user
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == student_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username already exists"
        )
    
    # Check if college exists
    # college = db.query(College).filter(College.id == student_data.college_id).first()
    # if not college:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"College with ID {student_data.college_id} not found"
    #     )
    
    # Create new user
    new_user = User(
        username=student_data.username,
        email=student_data.email,
        first_name=student_data.first_name,
        last_name=student_data.last_name,
        is_admin=False,
        is_active=True
    )
    new_user.set_password(student_data.password)
    
    db.add(new_user)
    db.flush()  # Flush to get the user ID
    
    # Create student profile
    new_student = Student(
        user_id=new_user.id,
        # college_id=student_data.college_id,
        roll_number=student_data.roll_number,
        branch=student_data.branch,
        year_of_study=student_data.year_of_study,
        is_verified=False
    )
    
    db.add(new_student)
    db.commit()
    db.refresh(new_user)
    
    return MessageResponse(
        message="Student registration successful",
        detail=f"User ID: {new_user.id}. Your account is pending activation by admin."
    )


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    print("Received username:", form_data.username)

    """
    Login with username and password to get access token.
    
    For Swagger UI testing:
    - Username field = your username
    - Password field = your password
    """
    # Find user by username (OAuth2PasswordRequestForm uses 'username' field)
    

    user = db.query(User).filter(
    or_(
        User.username == form_data.username,
        User.email == form_data.username
    )
    ).first()

    
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user is not active. Please contact admin to activate",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "is_admin": user.is_admin,
            "is_super_admin": user.is_super_admin
        }
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserInToken(
            id=user.id,
            username=user.username,
            is_admin=user.is_admin
        )
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_db)
):
    """
    Get current user information
    """
    from app.dependencies import get_current_user
    current_user = Depends(get_current_user)
    return current_user
