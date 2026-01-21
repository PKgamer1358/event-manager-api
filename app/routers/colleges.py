# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from typing import List

# from app.database import get_db
# from app.models import College, User
# from app.schemas import CollegeCreate, CollegeResponse, MessageResponse
# from app.dependencies import get_current_user
# from datetime import datetime

# router = APIRouter(prefix="/colleges", tags=["Colleges"])


# def require_admin(current_user: User = Depends(get_current_user)):
#     """
#     Dependency to check if the current user is an admin
#     """
#     if not current_user.is_admin:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Only administrators can perform this action"
#         )
#     return current_user


# @router.post("", response_model=CollegeResponse, status_code=status.HTTP_201_CREATED)
# def create_college(
#     college_data: CollegeCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(require_admin)
# ):
#     """
#     Create a new college (Admin only)
#     Also creates a college admin user automatically.
#     """
#     # Check if college code already exists
#     existing_college = db.query(College).filter(College.code == college_data.code).first()
#     if existing_college:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"College with code '{college_data.code}' already exists"
#         )
    
#     # Check if college admin username already exists
#     admin_username = f"admin.{college_data.code.lower()}"
#     existing_user = db.query(User).filter(User.username == admin_username).first()
#     if existing_user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Admin user for college code '{college_data.code}' already exists"
#         )
    
#     # Create new college
#     new_college = College(
#         name=college_data.name,
#         code=college_data.code,
#         city=college_data.city,
#         contact_email=college_data.contact_email,
#         contact_phone=college_data.contact_phone,
#         website=college_data.website,
#         is_active=college_data.is_active
#     )
    
#     db.add(new_college)
#     db.flush()  # Flush to get the college ID
    
#     # Create college admin user
#     college_admin = User(
#         username=admin_username,
#         email=college_data.contact_email,
#         first_name=college_data.code,
#         last_name="Admin",
#         is_admin=True,
#         is_active=True
#     )
#     # Set default password as college code
#     college_admin.set_password(f"{college_data.code}@{datetime.now().year}")
    
#     db.add(college_admin)
#     db.commit()
#     db.refresh(new_college)
    
#     return new_college


# @router.get("", response_model=List[CollegeResponse])
# def list_colleges(
#     skip: int = 0,
#     limit: int = 100,
#     active_only: bool = True,
#     db: Session = Depends(get_db)
# ):
#     """
#     Get list of colleges (Public - for student registration)
#     """
#     query = db.query(College)
    
#     if active_only:
#         query = query.filter(College.is_active == True)
    
#     colleges = query.offset(skip).limit(limit).all()
#     return colleges


# @router.get("/{college_id}", response_model=CollegeResponse)
# def get_college(
#     college_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Get a specific college by ID
#     """
#     college = db.query(College).filter(College.id == college_id).first()
    
#     if not college:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"College with ID {college_id} not found"
#         )
    
#     return college


# @router.delete("/{college_id}", response_model=MessageResponse)
# def delete_college(
#     college_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(require_admin)
# ):
#     """
#     Delete a college (Admin only)
#     """
#     college = db.query(College).filter(College.id == college_id).first()
    
#     if not college:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"College with ID {college_id} not found"
#         )
    
#     db.delete(college)
#     db.commit()
    
#     return MessageResponse(
#         message="College deleted successfully",
#         detail=f"College '{college.name}' has been removed"
#     )
