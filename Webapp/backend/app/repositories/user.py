"""
User Repository - Specialized CRUD operations cho User model
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.repositories.base import CRUDBase
from app.models.database_models import User
from app.schemas.schemas import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


class UserRepository(CRUDBase[User, UserCreate, UserUpdate]):
    """User repository với specialized methods"""

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get user by email address"""
        return db.query(User).filter(User.email == email).first()

    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()

    def create_user(self, db: Session, *, user_in: UserCreate) -> User:
        """Create new user với hashed password"""
        db_obj = User(
            email=user_in.email,
            username=user_in.username,
            full_name=user_in.full_name,
            hashed_password=get_password_hash(user_in.password),
            is_active=user_in.is_active,
            is_superuser=user_in.is_superuser,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_password(self, db: Session, *, user: User, new_password: str) -> User:
        """Update user password"""
        user.hashed_password = get_password_hash(new_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        """Authenticate user với email và password"""
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """Check if user is active"""
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        """Check if user is superuser"""
        return user.is_superuser

    def search_users(
        self, 
        db: Session, 
        *, 
        search: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Search users by email, username, or full_name"""
        return self.get_multi(
            db,
            skip=skip,
            limit=limit,
            search=search,
            search_fields=["email", "username", "full_name"]
        )

    def get_active_users(self, db: Session, *, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all active users"""
        return self.get_multi(
            db,
            skip=skip,
            limit=limit,
            filters={"is_active": True}
        )

    def get_superusers(self, db: Session, *, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all superusers"""
        return self.get_multi(
            db,
            skip=skip,
            limit=limit,
            filters={"is_superuser": True}
        )

    def deactivate_user(self, db: Session, *, user_id: int) -> Optional[User]:
        """Deactivate user account"""
        user = self.get(db, id=user_id)
        if user:
            user.is_active = False
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def activate_user(self, db: Session, *, user_id: int) -> Optional[User]:
        """Activate user account"""
        user = self.get(db, id=user_id)
        if user:
            user.is_active = True
            db.add(user)
            db.commit()
            db.refresh(user)
        return user


# Create repository instance
user_repo = UserRepository(User)