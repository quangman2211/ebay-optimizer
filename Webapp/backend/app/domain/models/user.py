"""
User Domain Models
Contains user-related entities and business logic
"""

from sqlalchemy import Column, String, Boolean, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel
from .enums import UserRoleEnum


class User(BaseModel):
    """
    User entity representing system users
    Follows Single Responsibility Principle - handles only user data
    """
    __tablename__ = "users"

    # Core user information
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    
    # User status
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Role assignment
    role_id = Column(Integer, ForeignKey("user_roles.id"), nullable=True)
    assigned_accounts = Column(JSON, nullable=True)  # eBay accounts assignment
    
    # Relationships - simplified for core functionality
    role = relationship("UserRole", back_populates="users")
    # listings = relationship("Listing", back_populates="user")
    accounts = relationship("Account", back_populates="user")
    # draft_listings = relationship("DraftListing", back_populates="user", foreign_keys="[DraftListing.user_id]")
    # messages = relationship("Message", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
    
    def is_admin(self) -> bool:
        """Check if user has admin privileges"""
        return self.is_superuser or (self.role and self.role.name == UserRoleEnum.ADMIN)
    
    def can_access_account(self, account_id: int) -> bool:
        """Check if user can access specific eBay account"""
        if self.is_admin():
            return True
        
        if not self.assigned_accounts:
            return False
            
        return account_id in self.assigned_accounts
    
    def activate(self):
        """Activate user account"""
        self.is_active = True
    
    def deactivate(self):
        """Deactivate user account"""
        self.is_active = False
    
    def can_import_data(self) -> bool:
        """Check if user can import CSV data"""
        if self.is_admin():
            return True
            
        if not self.role:
            return False
            
        return self.role.has_permission('import_data')


class UserRole(BaseModel):
    """
    User role entity defining permissions and access levels
    """
    __tablename__ = "user_roles"
    
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    permissions = Column(JSON, nullable=True)  # List of permissions
    
    # Relationships
    users = relationship("User", back_populates="role")
    
    def __repr__(self):
        return f"<UserRole(id={self.id}, name='{self.name}')>"
    
    def has_permission(self, permission: str) -> bool:
        """Check if role has specific permission"""
        if not self.permissions:
            return False
        return permission in self.permissions
    
    def add_permission(self, permission: str):
        """Add permission to role"""
        if not self.permissions:
            self.permissions = []
        
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, permission: str):
        """Remove permission from role"""
        if self.permissions and permission in self.permissions:
            self.permissions.remove(permission)