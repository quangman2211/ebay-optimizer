"""
Product Management API Endpoints - SOLID Architecture
RESTful API for comprehensive product catalog management with supplier integration
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.product_service import ProductService
from app.services.pricing_service import PricingService
from app.schemas.schemas import (
    Product, ProductCreate, ProductUpdate, ProductStatus, StockStatus,
    SupplierProduct, SupplierProductCreate, SupplierProductUpdate,
    ProductPerformanceStats, PriceHistory, PaginationParams, FilterParams,
    APIResponse, PaginatedResponse, BulkActionRequest, BulkActionResponse
)
from app.core.auth import get_current_user, require_role
from app.models.database_models import User

router = APIRouter(prefix="/products", tags=["products"])


# ===========================================
# CORE PRODUCT CRUD ENDPOINTS
# ===========================================

@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "EBAY_MANAGER"]))
):
    """
    Create a new product with inventory and pricing setup
    
    **Required Roles:** ADMIN, EBAY_MANAGER
    
    **Features:**
    - SKU uniqueness validation
    - Automatic profit margin calculation
    - Stock status determination
    - Price history initialization
    """
    try:
        service = ProductService(db)
        product = service.create_product(product_data)
        
        return APIResponse(
            success=True,
            message="Product created successfully",
            data=product
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create product: {str(e)}"
        )


@router.get("/", response_model=PaginatedResponse)
async def get_products(
    # Pagination parameters
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    sort_by: Optional[str] = Query(None, description="Sort field: name, sku, price, stock, sales, created"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    
    # Filter parameters
    search: Optional[str] = Query(None, description="Search in SKU, name, brand, description"),
    status: Optional[ProductStatus] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier"),
    stock_status: Optional[StockStatus] = Query(None, description="Filter by stock status"),
    low_stock_only: bool = Query(False, description="Show only low stock products"),
    
    # Dependencies
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get products with comprehensive filtering and pagination
    
    **Features:**
    - Advanced search across multiple fields
    - Status and category filtering
    - Supplier-based filtering
    - Stock level filtering
    - Performance-based sorting
    """
    try:
        service = ProductService(db)
        
        pagination = PaginationParams(
            page=page,
            size=size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        filters = FilterParams(search=search, category=category)
        
        products, total = service.get_products(
            pagination=pagination,
            filters=filters,
            status=status,
            category=category,
            supplier_id=supplier_id,
            stock_status=stock_status,
            low_stock_only=low_stock_only
        )
        
        return PaginatedResponse(
            items=products,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
            has_next=page * size < total,
            has_prev=page > 1
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch products: {str(e)}"
        )


@router.get("/{product_id}", response_model=APIResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get product by ID with supplier relationships"""
    try:
        service = ProductService(db)
        product = service.get_product(product_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        return APIResponse(
            success=True,
            data=product
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch product: {str(e)}"
        )


@router.get("/sku/{sku}", response_model=APIResponse)
async def get_product_by_sku(
    sku: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get product by SKU"""
    try:
        service = ProductService(db)
        product = service.get_product_by_sku(sku)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        return APIResponse(
            success=True,
            data=product
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch product: {str(e)}"
        )


@router.put("/{product_id}", response_model=APIResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "EBAY_MANAGER"]))
):
    """
    Update product information with price history tracking
    
    **Required Roles:** ADMIN, EBAY_MANAGER
    
    **Features:**
    - Automatic profit margin recalculation
    - Stock status updates
    - Price change history tracking
    - Stock level management
    """
    try:
        service = ProductService(db)
        product = service.update_product(product_id, product_data)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        return APIResponse(
            success=True,
            message="Product updated successfully",
            data=product
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update product: {str(e)}"
        )


@router.delete("/{product_id}", response_model=APIResponse)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """
    Delete product (soft delete if has pending orders)
    
    **Required Roles:** ADMIN only
    
    **Features:**
    - Soft delete for products with pending orders
    - Hard delete for products without dependencies
    - Safety checks for data integrity
    """
    try:
        service = ProductService(db)
        success = service.delete_product(product_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        return APIResponse(
            success=True,
            message="Product deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete product: {str(e)}"
        )


# ===========================================
# INVENTORY MANAGEMENT ENDPOINTS
# ===========================================

@router.put("/{product_id}/stock", response_model=APIResponse)
async def update_stock_level(
    product_id: int,
    new_stock: int = Query(..., ge=0, description="New stock level"),
    reason: str = Query("Manual update", description="Reason for stock change"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "EBAY_MANAGER", "FULFILLMENT_STAFF"]))
):
    """
    Update product stock level
    
    **Required Roles:** ADMIN, EBAY_MANAGER, FULFILLMENT_STAFF
    
    **Features:**
    - Automatic stock status calculation
    - Change history tracking
    - Audit trail in product notes
    """
    try:
        service = ProductService(db)
        success = service.update_stock_level(product_id, new_stock, reason)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        return APIResponse(
            success=True,
            message=f"Stock level updated to {new_stock}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update stock level: {str(e)}"
        )


@router.get("/inventory/low-stock", response_model=APIResponse)
async def get_low_stock_products(
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get products that need reordering"""
    try:
        service = ProductService(db)
        products = service.get_low_stock_products(limit=limit)
        
        return APIResponse(
            success=True,
            data={
                "count": len(products),
                "products": products
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch low stock products: {str(e)}"
        )


@router.get("/inventory/summary", response_model=APIResponse)
async def get_inventory_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive inventory summary with value calculations"""
    try:
        service = ProductService(db)
        summary = service.get_inventory_summary()
        
        return APIResponse(
            success=True,
            data=summary
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch inventory summary: {str(e)}"
        )


# ===========================================
# SUPPLIER RELATIONSHIP ENDPOINTS
# ===========================================

@router.post("/{product_id}/suppliers", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def add_supplier_to_product(
    product_id: int,
    supplier_product_data: SupplierProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "EBAY_MANAGER"]))
):
    """
    Add supplier relationship to product
    
    **Required Roles:** ADMIN, EBAY_MANAGER
    
    **Features:**
    - Duplicate relationship validation
    - Preferred supplier handling
    - Automatic cost price updates
    - Price history tracking
    """
    try:
        # Override product_id from URL
        supplier_product_data.product_id = product_id
        
        service = ProductService(db)
        relationship = service.add_supplier_to_product(supplier_product_data)
        
        return APIResponse(
            success=True,
            message="Supplier added to product successfully",
            data=relationship
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add supplier to product: {str(e)}"
        )


@router.get("/{product_id}/suppliers", response_model=APIResponse)
async def get_product_suppliers(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all suppliers for a product"""
    try:
        service = ProductService(db)
        suppliers = service.get_product_suppliers(product_id)
        
        return APIResponse(
            success=True,
            data={
                "product_id": product_id,
                "supplier_count": len(suppliers),
                "suppliers": suppliers
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch product suppliers: {str(e)}"
        )


# ===========================================
# PERFORMANCE & ANALYTICS ENDPOINTS
# ===========================================

@router.get("/{product_id}/performance", response_model=APIResponse)
async def get_product_performance(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed performance statistics for a product"""
    try:
        service = ProductService(db)
        stats = service.get_product_performance_stats(product_id)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        return APIResponse(
            success=True,
            data=stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch product performance: {str(e)}"
        )


@router.post("/{product_id}/update-performance", response_model=APIResponse)
async def update_product_performance(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "EBAY_MANAGER"]))
):
    """
    Manually trigger performance metrics update
    
    **Required Roles:** ADMIN, EBAY_MANAGER
    """
    try:
        service = ProductService(db)
        success = service.update_product_performance(product_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        return APIResponse(
            success=True,
            message="Product performance updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update product performance: {str(e)}"
        )


@router.get("/analytics/top-performers", response_model=APIResponse)
async def get_top_products(
    limit: int = Query(10, ge=1, le=50, description="Number of products to return"),
    metric: str = Query("revenue", regex="^(revenue|sales|rating|margin)$", description="Ranking metric"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get top performing products by specified metric"""
    try:
        service = ProductService(db)
        top_products = service.get_top_products(limit=limit, metric=metric)
        
        return APIResponse(
            success=True,
            data={
                "metric": metric,
                "limit": limit,
                "products": top_products
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch top products: {str(e)}"
        )


# ===========================================
# PRICING ENDPOINTS
# ===========================================

@router.get("/{product_id}/pricing/optimize", response_model=APIResponse)
async def optimize_product_price(
    product_id: int,
    target_margin: Optional[float] = Query(None, ge=0, le=100, description="Target profit margin %"),
    market_price: Optional[float] = Query(None, gt=0, description="Current market price"),
    competitive_factor: Optional[float] = Query(None, ge=0, le=1, description="Competitive adjustment factor"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get optimal pricing recommendations for a product"""
    try:
        pricing_service = PricingService(db)
        optimization = pricing_service.calculate_optimal_price(
            product_id=product_id,
            target_margin=target_margin,
            market_price=market_price,
            competitive_factor=competitive_factor
        )
        
        return APIResponse(
            success=True,
            data=optimization
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize product price: {str(e)}"
        )


@router.get("/{product_id}/pricing/history", response_model=APIResponse)
async def get_price_history(
    product_id: int,
    limit: Optional[int] = Query(20, ge=1, le=100, description="Number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get price change history for a product"""
    try:
        service = ProductService(db)
        history = service.get_price_history(product_id, limit=limit)
        
        return APIResponse(
            success=True,
            data={
                "product_id": product_id,
                "history_count": len(history),
                "price_history": history
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch price history: {str(e)}"
        )


@router.get("/{product_id}/profitability", response_model=APIResponse)
async def analyze_product_profitability(
    product_id: int,
    days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive profitability analysis for a product"""
    try:
        pricing_service = PricingService(db)
        analysis = pricing_service.analyze_product_profitability(
            product_id=product_id,
            time_period_days=days
        )
        
        return APIResponse(
            success=True,
            data=analysis
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze product profitability: {str(e)}"
        )


# ===========================================
# BULK OPERATIONS ENDPOINTS
# ===========================================

@router.post("/bulk/update-performance", response_model=APIResponse)
async def bulk_update_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """
    Bulk update performance metrics for all active products
    
    **Required Roles:** ADMIN only
    """
    try:
        service = ProductService(db)
        results = service.bulk_update_performance()
        
        return APIResponse(
            success=True,
            message=f"Bulk performance update completed: {results['updated']}/{results['total']} successful",
            data=results
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update performance: {str(e)}"
        )


@router.post("/bulk/optimize-pricing", response_model=APIResponse)
async def bulk_optimize_pricing(
    product_ids: Optional[List[int]] = Query(None, description="Specific product IDs to optimize"),
    category: Optional[str] = Query(None, description="Optimize all products in category"),
    supplier_id: Optional[int] = Query(None, description="Optimize all products from supplier"),
    target_margin: Optional[float] = Query(None, ge=0, le=100, description="Target profit margin %"),
    auto_apply: bool = Query(False, description="Automatically apply recommendations"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "EBAY_MANAGER"]))
):
    """
    Bulk pricing optimization for multiple products
    
    **Required Roles:** ADMIN, EBAY_MANAGER
    """
    try:
        pricing_service = PricingService(db)
        results = pricing_service.bulk_price_optimization(
            product_ids=product_ids,
            category=category,
            supplier_id=supplier_id,
            target_margin=target_margin
        )
        
        # Auto-apply if requested
        if auto_apply and results["recommendations"]:
            apply_results = pricing_service.apply_pricing_recommendations(
                results["recommendations"]
            )
            results["auto_apply_results"] = apply_results
        
        return APIResponse(
            success=True,
            message=f"Bulk pricing optimization completed: {results['optimized']}/{results['total_products']} products optimized",
            data=results
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk optimize pricing: {str(e)}"
        )


# ===========================================
# CATEGORY & LOOKUP ENDPOINTS
# ===========================================

@router.get("/categories", response_model=APIResponse)
async def get_product_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of all product categories with counts"""
    try:
        from sqlalchemy import func
        from app.models.database_models import Product
        
        categories = db.query(
            Product.category,
            Product.subcategory,
            func.count(Product.id).label('count')
        ).filter(Product.status == "active")\
         .group_by(Product.category, Product.subcategory)\
         .order_by(Product.category, Product.subcategory)\
         .all()
        
        # Organize into hierarchical structure
        category_tree = {}
        for cat in categories:
            main_cat = cat.category or "Uncategorized"
            sub_cat = cat.subcategory or "General"
            
            if main_cat not in category_tree:
                category_tree[main_cat] = {}
            
            category_tree[main_cat][sub_cat] = cat.count
        
        return APIResponse(
            success=True,
            data={
                "category_tree": category_tree,
                "flat_categories": [
                    {
                        "category": c.category,
                        "subcategory": c.subcategory,
                        "product_count": c.count
                    }
                    for c in categories
                ]
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch product categories: {str(e)}"
        )


@router.get("/brands", response_model=APIResponse)
async def get_product_brands(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of all product brands with counts"""
    try:
        from sqlalchemy import func
        from app.models.database_models import Product
        
        brands = db.query(
            Product.brand,
            func.count(Product.id).label('count')
        ).filter(Product.brand.isnot(None))\
         .filter(Product.status == "active")\
         .group_by(Product.brand)\
         .order_by(func.count(Product.id).desc())\
         .all()
        
        return APIResponse(
            success=True,
            data=[{"brand": b.brand, "product_count": b.count} for b in brands]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch product brands: {str(e)}"
        )