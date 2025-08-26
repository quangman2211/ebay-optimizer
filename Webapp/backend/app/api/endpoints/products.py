"""
Product Management API Endpoints
Handles operations for source products management
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user
from app.repositories.source import SourceRepository
from app.models.database_models import User, SourceProduct
from app.schemas.schemas import APIResponse
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()

# Pydantic models for request/response
class ProductCreate(BaseModel):
    source_id: str
    name: str
    description: Optional[str] = None
    source_price: float
    category: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    sku: Optional[str] = None
    suggested_price: Optional[float] = None
    market_price: Optional[float] = None
    profit_margin: Optional[float] = None
    in_stock: bool = True
    stock_quantity: int = 0
    min_order_quantity: int = 1
    source_url: Optional[str] = None
    image_urls: Optional[List[str]] = []
    specifications: Optional[Dict[str, Any]] = {}
    tags: Optional[List[str]] = []
    weight: Optional[float] = None
    dimensions: Optional[Dict[str, Any]] = {}
    gdrive_folder_url: Optional[str] = None
    image_notes: Optional[str] = None
    is_approved: bool = False

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    source_price: Optional[float] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    sku: Optional[str] = None
    suggested_price: Optional[float] = None
    market_price: Optional[float] = None
    profit_margin: Optional[float] = None
    in_stock: Optional[bool] = None
    stock_quantity: Optional[int] = None
    min_order_quantity: Optional[int] = None
    source_url: Optional[str] = None
    image_urls: Optional[List[str]] = None
    specifications: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    weight: Optional[float] = None
    dimensions: Optional[Dict[str, Any]] = None
    gdrive_folder_url: Optional[str] = None
    image_notes: Optional[str] = None
    is_approved: Optional[bool] = None

class ProductResponse(BaseModel):
    id: str
    source_id: str
    name: str
    description: Optional[str] = None
    source_price: float
    category: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    sku: Optional[str] = None
    suggested_price: Optional[float] = None
    market_price: Optional[float] = None
    profit_margin: Optional[float] = None
    in_stock: bool
    stock_quantity: int
    min_order_quantity: int
    source_url: Optional[str] = None
    image_urls: Optional[List[str]] = []
    specifications: Optional[Dict[str, Any]] = {}
    tags: Optional[List[str]] = []
    weight: Optional[float] = None
    dimensions: Optional[Dict[str, Any]] = {}
    views: Optional[int] = 0
    conversions: Optional[int] = 0
    roi: Optional[float] = None
    gdrive_folder_url: Optional[str] = None
    image_notes: Optional[str] = None
    is_approved: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_synced: Optional[datetime] = None

    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        # Handle null JSON fields
        data = obj.__dict__.copy()
        data['image_urls'] = data.get('image_urls') or []
        data['specifications'] = data.get('specifications') or {}
        data['tags'] = data.get('tags') or []
        data['dimensions'] = data.get('dimensions') or {}
        data['views'] = data.get('views') or 0
        data['conversions'] = data.get('conversions') or 0
        return cls(**data)

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    source_id: Optional[str] = Query(None, description="Filter by source"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    sort_by: Optional[str] = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order")
):
    """
    Get source products with filtering and pagination
    """
    try:
        # Build query
        query = db.query(SourceProduct)
        
        # Apply filters
        if source_id:
            query = query.filter(SourceProduct.source_id == source_id)
        if category:
            query = query.filter(SourceProduct.category == category)
        if status:
            query = query.filter(SourceProduct.status == status)
        if search:
            query = query.filter(
                (SourceProduct.name.ilike(f"%{search}%")) |
                (SourceProduct.description.ilike(f"%{search}%"))
            )
        
        # Apply sorting
        if sort_order.lower() == "desc":
            query = query.order_by(getattr(SourceProduct, sort_by).desc())
        else:
            query = query.order_by(getattr(SourceProduct, sort_by))
        
        # Apply pagination
        skip = (page - 1) * size
        products = query.offset(skip).limit(size).all()
        
        return products
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific source product by ID
    """
    try:
        product = db.query(SourceProduct).filter(SourceProduct.id == product_id).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching product: {str(e)}")

@router.post("/", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new source product
    """
    try:
        # Check if name already exists for this source
        existing = db.query(SourceProduct).filter(
            SourceProduct.source_id == product.source_id,
            SourceProduct.name == product.name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="Product with this name already exists for this source"
            )
        
        # Generate unique ID
        import uuid
        product_id = str(uuid.uuid4())
        
        # Create new product
        db_product = SourceProduct(
            id=product_id,
            source_id=product.source_id,
            name=product.name,
            description=product.description,
            source_price=product.source_price,
            category=product.category,
            brand=product.brand,
            model=product.model,
            sku=product.sku,
            suggested_price=product.suggested_price,
            market_price=product.market_price,
            profit_margin=product.profit_margin,
            in_stock=product.in_stock,
            stock_quantity=product.stock_quantity,
            min_order_quantity=product.min_order_quantity,
            source_url=product.source_url,
            image_urls=product.image_urls or [],
            specifications=product.specifications or {},
            tags=product.tags or [],
            weight=product.weight,
            dimensions=product.dimensions or {},
            gdrive_folder_url=product.gdrive_folder_url,
            image_notes=product.image_notes,
            is_approved=product.is_approved
        )
        
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        
        return db_product
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating product: {str(e)}")

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update an existing source product
    """
    try:
        # Get current product
        product = db.query(SourceProduct).filter(SourceProduct.id == product_id).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Update fields
        update_data = product_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        product.updated_at = datetime.now()
        
        db.add(product)
        db.commit()
        db.refresh(product)
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating product: {str(e)}")

@router.delete("/{product_id}", response_model=APIResponse)
async def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a source product
    """
    try:
        product = db.query(SourceProduct).filter(SourceProduct.id == product_id).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        db.delete(product)
        db.commit()
        
        return APIResponse(
            success=True,
            message="Product deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting product: {str(e)}")

@router.get("/categories/list", response_model=List[str])
async def get_product_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of all product categories
    """
    try:
        categories = db.query(SourceProduct.category).distinct().filter(
            SourceProduct.category.isnot(None)
        ).all()
        
        return [cat[0] for cat in categories if cat[0]]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")

@router.post("/{product_id}/create-draft", response_model=APIResponse)
async def create_draft_from_product(
    product_id: str,
    account_id: int = Query(..., description="Target eBay account ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a draft listing from a source product
    """
    try:
        from app.repositories.draft_listing import DraftListingRepository
        from app.models.database_models import DraftListing
        
        # Get the product
        product = db.query(SourceProduct).filter(SourceProduct.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Generate unique draft ID
        import uuid
        draft_id = str(uuid.uuid4())
        
        # Create draft listing
        draft = DraftListing(
            id=draft_id,
            user_id=current_user.id,
            account_id=account_id,
            source_product_id=str(product_id),
            title=product.name,
            description=product.description,
            category=product.category,
            price=product.suggested_price or product.source_price,
            cost_price=product.source_price
        )
        
        db.add(draft)
        db.commit()
        db.refresh(draft)
        
        return APIResponse(
            success=True,
            message=f"Draft listing created successfully from product '{product.name}'",
            data={"draft_id": draft.id, "product_id": product_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating draft from product: {str(e)}")

@router.get("/statistics/summary", response_model=APIResponse)
async def get_product_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get product statistics summary
    """
    try:
        from sqlalchemy import func
        
        # Count by status
        status_counts = db.query(
            SourceProduct.status,
            func.count(SourceProduct.id)
        ).group_by(SourceProduct.status).all()
        
        # Count by category
        category_counts = db.query(
            SourceProduct.category,
            func.count(SourceProduct.id)
        ).group_by(SourceProduct.category).all()
        
        # Total products
        total_products = db.query(func.count(SourceProduct.id)).scalar()
        
        # Average price
        avg_price = db.query(func.avg(SourceProduct.price)).scalar()
        
        stats = {
            "total_products": total_products,
            "average_price": float(avg_price) if avg_price else 0.0,
            "status_distribution": {status: count for status, count in status_counts},
            "category_distribution": {category: count for category, count in category_counts if category}
        }
        
        return APIResponse(
            success=True,
            message="Product statistics retrieved successfully",
            data=stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting product statistics: {str(e)}")