"""
Base Repository Pattern cho Clean Architecture
Generic CRUD operations với pagination, filtering, sorting
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func, text
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel

from app.db.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository với generic CRUD operations"""
    
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object với default methods để Create, Read, Update, Delete (CRUD).
        
        **Parameters**
        * `model`: SQLAlchemy model class
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Get single record by ID"""
        try:
            return db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    def get_by_field(self, db: Session, field: str, value: Any) -> Optional[ModelType]:
        """Get single record by field"""
        try:
            return db.query(self.model).filter(getattr(self.model, field) == value).first()
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        search: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get multiple records với pagination, filtering, search, sorting
        
        Returns:
            Dict với keys: items, total, page, size, pages, has_next, has_prev
        """
        try:
            query = db.query(self.model)
            
            # Apply user filter if provided
            if user_id is not None and hasattr(self.model, 'user_id'):
                query = query.filter(self.model.user_id == user_id)
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if value is not None and hasattr(self.model, field):
                        if isinstance(value, list):
                            query = query.filter(getattr(self.model, field).in_(value))
                        else:
                            query = query.filter(getattr(self.model, field) == value)
            
            # Apply search
            if search and search_fields:
                search_conditions = []
                for field in search_fields:
                    if hasattr(self.model, field):
                        search_conditions.append(
                            getattr(self.model, field).ilike(f"%{search}%")
                        )
                if search_conditions:
                    query = query.filter(or_(*search_conditions))
            
            # Get total count before pagination
            total = query.count()
            
            # Apply sorting
            if sort_by and hasattr(self.model, sort_by):
                if sort_order.lower() == "desc":
                    query = query.order_by(desc(getattr(self.model, sort_by)))
                else:
                    query = query.order_by(asc(getattr(self.model, sort_by)))
            else:
                # Default sorting by created_at if available
                if hasattr(self.model, 'created_at'):
                    query = query.order_by(desc(self.model.created_at))
            
            # Apply pagination
            items = query.offset(skip).limit(limit).all()
            
            # Calculate pagination metadata
            page = (skip // limit) + 1 if limit > 0 else 1
            size = limit
            pages = (total + limit - 1) // limit if limit > 0 else 1
            has_next = skip + limit < total
            has_prev = skip > 0
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "size": size,
                "pages": pages,
                "has_next": has_next,
                "has_prev": has_prev
            }
            
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    def create(self, db: Session, *, obj_in: CreateSchemaType, user_id: Optional[int] = None) -> ModelType:
        """Create new record"""
        try:
            obj_in_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
            
            # Add user_id if provided và model có user_id field
            if user_id is not None and hasattr(self.model, 'user_id'):
                obj_in_data['user_id'] = user_id
            
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
            
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update existing record"""
        try:
            obj_data = db_obj.__dict__.copy()
            
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in
            
            for field in obj_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])
            
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
            
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    def delete(self, db: Session, *, id: Any) -> Optional[ModelType]:
        """Delete record by ID"""
        try:
            obj = db.query(self.model).get(id)
            if obj:
                db.delete(obj)
                db.commit()
                return obj
            return None
            
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    def bulk_create(self, db: Session, *, objs_in: List[CreateSchemaType], user_id: Optional[int] = None) -> List[ModelType]:
        """Bulk create multiple records"""
        try:
            db_objs = []
            for obj_in in objs_in:
                obj_in_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
                
                if user_id is not None and hasattr(self.model, 'user_id'):
                    obj_in_data['user_id'] = user_id
                
                db_obj = self.model(**obj_in_data)
                db_objs.append(db_obj)
            
            db.add_all(db_objs)
            db.commit()
            
            for db_obj in db_objs:
                db.refresh(db_obj)
            
            return db_objs
            
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    def bulk_update(
        self,
        db: Session,
        *,
        updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Bulk update multiple records
        updates format: [{"id": 1, "field1": "value1"}, ...]
        """
        try:
            success_count = 0
            failed_ids = []
            
            for update_data in updates:
                if "id" not in update_data:
                    continue
                
                obj_id = update_data.pop("id")
                obj = db.query(self.model).get(obj_id)
                
                if obj:
                    for field, value in update_data.items():
                        if hasattr(obj, field):
                            setattr(obj, field, value)
                    success_count += 1
                else:
                    failed_ids.append(obj_id)
            
            db.commit()
            
            return {
                "success": success_count,
                "failed": len(failed_ids),
                "failed_ids": failed_ids
            }
            
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    def bulk_delete(self, db: Session, *, ids: List[Any]) -> Dict[str, Any]:
        """Bulk delete multiple records by IDs"""
        try:
            deleted = db.query(self.model).filter(self.model.id.in_(ids)).all()
            deleted_count = len(deleted)
            
            db.query(self.model).filter(self.model.id.in_(ids)).delete(synchronize_session=False)
            db.commit()
            
            return {
                "success": deleted_count,
                "failed": len(ids) - deleted_count,
                "deleted_ids": [obj.id for obj in deleted]
            }
            
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    def count(self, db: Session, *, filters: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None) -> int:
        """Count records with optional filters"""
        try:
            query = db.query(func.count(self.model.id))
            
            if user_id is not None and hasattr(self.model, 'user_id'):
                query = query.filter(self.model.user_id == user_id)
            
            if filters:
                for field, value in filters.items():
                    if value is not None and hasattr(self.model, field):
                        query = query.filter(getattr(self.model, field) == value)
            
            return query.scalar()
            
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    def exists(self, db: Session, *, id: Any) -> bool:
        """Check if record exists by ID"""
        try:
            return db.query(self.model).filter(self.model.id == id).first() is not None
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    def get_or_create(
        self,
        db: Session,
        *,
        defaults: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> tuple[ModelType, bool]:
        """
        Get existing record or create new one
        Returns: (object, created_flag)
        """
        try:
            # Try to get existing record
            query = db.query(self.model)
            for field, value in kwargs.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
            
            obj = query.first()
            
            if obj:
                return obj, False
            
            # Create new record
            create_data = kwargs.copy()
            if defaults:
                create_data.update(defaults)
            
            obj = self.model(**create_data)
            db.add(obj)
            db.commit()
            db.refresh(obj)
            
            return obj, True
            
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    def raw_query(self, db: Session, query: str, params: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Execute raw SQL query"""
        try:
            result = db.execute(text(query), params or {})
            return result.fetchall()
        except SQLAlchemyError as e:
            db.rollback()
            raise e