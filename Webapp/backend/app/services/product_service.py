"""
Product Catalog Service - SOLID Architecture Implementation
Handles comprehensive product management with pricing optimization and inventory control
Single Responsibility: Manages all product-related business logic and supplier relationships
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc, case

from app.models.database_models import (
    Product, Supplier, SupplierProduct, PriceHistory, OrderItem, Order
)
from app.schemas.schemas import (
    ProductCreate, ProductUpdate, ProductStatus, StockStatus, EbayCondition,
    SupplierProductCreate, SupplierProductUpdate, PriceHistoryCreate,
    ProductPerformanceStats, PaginationParams, FilterParams
)


class ProductService:
    """
    SOLID Principle: Single Responsibility
    Manages all product catalog operations including CRUD, pricing optimization,
    inventory management, and supplier relationships
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ===========================================
    # CORE PRODUCT CRUD OPERATIONS
    # ===========================================
    
    def create_product(self, product_data: ProductCreate) -> Product:
        """Create a new product with initial inventory and pricing"""
        try:
            # Check for duplicate SKU
            existing = self.get_product_by_sku(product_data.sku)
            if existing:
                raise ValueError(f"Product with SKU {product_data.sku} already exists")
            
            # Calculate profit margin if both cost and selling price provided
            profit_margin = None
            if product_data.cost_price and product_data.selling_price:
                profit_margin = ((product_data.selling_price - product_data.cost_price) / product_data.selling_price) * 100
            
            # Determine stock status
            stock_status = self._calculate_stock_status(
                product_data.stock_level, 
                product_data.reorder_point
            )
            
            # Create new product
            db_product = Product(
                sku=product_data.sku,
                name=product_data.name,
                description=product_data.description,
                category=product_data.category,
                subcategory=product_data.subcategory,
                brand=product_data.brand,
                primary_supplier_id=product_data.primary_supplier_id,
                backup_supplier_id=product_data.backup_supplier_id,
                cost_price=product_data.cost_price,
                selling_price=product_data.selling_price,
                profit_margin_percent=profit_margin,
                retail_price=product_data.retail_price,
                stock_level=product_data.stock_level,
                reorder_point=product_data.reorder_point,
                max_stock_level=product_data.max_stock_level,
                stock_status=stock_status.value,
                weight_kg=product_data.weight_kg,
                dimensions_cm=product_data.dimensions_cm,
                color=product_data.color,
                size=product_data.size,
                material=product_data.material,
                ebay_category_id=product_data.ebay_category_id,
                ebay_condition=product_data.ebay_condition.value,
                shipping_cost=product_data.shipping_cost,
                handling_days=product_data.handling_days,
                tags=product_data.tags,
                notes=product_data.notes,
                status="active"
            )
            
            self.db.add(db_product)
            self.db.commit()
            self.db.refresh(db_product)
            
            # Create initial price history record
            if product_data.cost_price or product_data.selling_price:
                self._create_price_history(
                    product_id=db_product.id,
                    new_cost=product_data.cost_price,
                    new_selling_price=product_data.selling_price,
                    change_reason="Initial product creation",
                    change_type="price_update"
                )
            
            return db_product
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to create product: {str(e)}")
    
    def get_product(self, product_id: int) -> Optional[Product]:
        """Get product by ID with supplier relationships"""
        return self.db.query(Product)\
            .options(
                joinedload(Product.primary_supplier),
                joinedload(Product.backup_supplier)
            )\
            .filter(Product.id == product_id)\
            .first()
    
    def get_product_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU"""
        return self.db.query(Product).filter(Product.sku == sku).first()
    
    def get_products(
        self,
        pagination: Optional[PaginationParams] = None,
        filters: Optional[FilterParams] = None,
        status: Optional[ProductStatus] = None,
        category: Optional[str] = None,
        supplier_id: Optional[int] = None,
        stock_status: Optional[StockStatus] = None,
        low_stock_only: bool = False
    ) -> Tuple[List[Product], int]:
        """Get products with comprehensive filtering and pagination"""
        
        query = self.db.query(Product)\
            .options(
                joinedload(Product.primary_supplier),
                joinedload(Product.backup_supplier)
            )
        
        # Apply filters
        if status:
            query = query.filter(Product.status == status.value)
        
        if category:
            query = query.filter(Product.category == category)
        
        if supplier_id:
            query = query.filter(
                or_(
                    Product.primary_supplier_id == supplier_id,
                    Product.backup_supplier_id == supplier_id
                )
            )
        
        if stock_status:
            query = query.filter(Product.stock_status == stock_status.value)
        
        if low_stock_only:
            query = query.filter(Product.stock_level <= Product.reorder_point)
        
        if filters:
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Product.sku.ilike(search_term),
                        Product.name.ilike(search_term),
                        Product.brand.ilike(search_term),
                        Product.description.ilike(search_term)
                    )
                )
            
            if filters.category:
                query = query.filter(Product.category == filters.category)
            
            if filters.date_from:
                query = query.filter(Product.created_at >= filters.date_from)
            
            if filters.date_to:
                query = query.filter(Product.created_at <= filters.date_to)
        
        # Get total count
        total = query.count()
        
        # Apply sorting
        if pagination and pagination.sort_by:
            if pagination.sort_by == "name":
                order_col = Product.name
            elif pagination.sort_by == "sku":
                order_col = Product.sku
            elif pagination.sort_by == "price":
                order_col = Product.selling_price
            elif pagination.sort_by == "stock":
                order_col = Product.stock_level
            elif pagination.sort_by == "sales":
                order_col = Product.total_sales
            elif pagination.sort_by == "created":
                order_col = Product.created_at
            else:
                order_col = Product.name
            
            if pagination.sort_order == "desc":
                query = query.order_by(desc(order_col))
            else:
                query = query.order_by(asc(order_col))
        else:
            query = query.order_by(Product.name)
        
        # Apply pagination
        if pagination:
            offset = (pagination.page - 1) * pagination.size
            query = query.offset(offset).limit(pagination.size)
        
        products = query.all()
        return products, total
    
    def update_product(self, product_id: int, product_data: ProductUpdate) -> Optional[Product]:
        """Update product with price history tracking"""
        try:
            product = self.get_product(product_id)
            if not product:
                return None
            
            # Store old values for price history
            old_cost = product.cost_price
            old_selling_price = product.selling_price
            
            # Update fields
            update_data = product_data.dict(exclude_unset=True)
            
            # Handle enum conversions
            if "status" in update_data and update_data["status"]:
                update_data["status"] = update_data["status"].value
            if "ebay_condition" in update_data and update_data["ebay_condition"]:
                update_data["ebay_condition"] = update_data["ebay_condition"].value
            
            # Track price changes
            new_cost = update_data.get("cost_price", old_cost)
            new_selling_price = update_data.get("selling_price", old_selling_price)
            
            # Update profit margin if prices changed
            if new_cost and new_selling_price:
                profit_margin = ((new_selling_price - new_cost) / new_selling_price) * 100
                update_data["profit_margin_percent"] = profit_margin
            
            # Update stock status if stock level changed
            if "stock_level" in update_data:
                new_stock_level = update_data["stock_level"]
                reorder_point = update_data.get("reorder_point", product.reorder_point)
                stock_status = self._calculate_stock_status(new_stock_level, reorder_point)
                update_data["stock_status"] = stock_status.value
            
            # Apply updates
            for field, value in update_data.items():
                if hasattr(product, field):
                    setattr(product, field, value)
            
            product.updated_at = datetime.utcnow()
            
            # Create price history if prices changed
            if (new_cost != old_cost) or (new_selling_price != old_selling_price):
                self._create_price_history(
                    product_id=product.id,
                    old_cost=old_cost,
                    new_cost=new_cost,
                    old_selling_price=old_selling_price,
                    new_selling_price=new_selling_price,
                    change_reason="Product update",
                    change_type="price_update"
                )
            
            self.db.commit()
            self.db.refresh(product)
            
            return product
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to update product: {str(e)}")
    
    def delete_product(self, product_id: int) -> bool:
        """Soft delete product (set status to discontinued)"""
        try:
            product = self.get_product(product_id)
            if not product:
                return False
            
            # Check if product has pending orders
            pending_orders = self.db.query(OrderItem).filter(
                and_(
                    OrderItem.product_id == product_id,
                    OrderItem.fulfillment_status.in_(["pending", "ordered"])
                )
            ).count()
            
            if pending_orders > 0:
                # Soft delete - set to discontinued
                product.status = "discontinued"
                product.stock_status = "discontinued"
                product.updated_at = datetime.utcnow()
            else:
                # Hard delete if no pending orders
                self.db.delete(product)
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to delete product: {str(e)}")
    
    # ===========================================
    # INVENTORY MANAGEMENT
    # ===========================================
    
    def update_stock_level(self, product_id: int, new_stock: int, reason: str = "Manual update") -> bool:
        """Update product stock level and stock status"""
        try:
            product = self.get_product(product_id)
            if not product:
                return False
            
            old_stock = product.stock_level
            product.stock_level = new_stock
            product.stock_status = self._calculate_stock_status(new_stock, product.reorder_point).value
            product.updated_at = datetime.utcnow()
            
            # Log stock change in notes or create audit log
            stock_change = new_stock - old_stock
            change_note = f"Stock changed: {old_stock} → {new_stock} ({stock_change:+d}). Reason: {reason}"
            
            if product.notes:
                product.notes += f"\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}: {change_note}"
            else:
                product.notes = f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}: {change_note}"
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to update stock level: {str(e)}")
    
    def get_low_stock_products(self, limit: Optional[int] = None) -> List[Product]:
        """Get products that need reordering"""
        query = self.db.query(Product)\
            .filter(
                and_(
                    Product.status == "active",
                    Product.stock_level <= Product.reorder_point
                )
            )\
            .order_by(
                case(
                    (Product.stock_level == 0, 1),  # Out of stock first
                    else_=2
                ),
                Product.stock_level  # Then by stock level ascending
            )
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_inventory_summary(self) -> Dict[str, Any]:
        """Get comprehensive inventory summary"""
        
        # Stock status distribution
        stock_dist = self.db.query(
            Product.stock_status,
            func.count(Product.id).label('count'),
            func.sum(Product.stock_level).label('total_units')
        ).filter(Product.status == "active")\
         .group_by(Product.stock_status)\
         .all()
        
        # Category inventory
        category_inv = self.db.query(
            Product.category,
            func.count(Product.id).label('products'),
            func.sum(Product.stock_level).label('total_stock'),
            func.sum(Product.stock_level * Product.cost_price).label('total_value')
        ).filter(Product.status == "active")\
         .group_by(Product.category)\
         .all()
        
        # Total inventory value
        total_value = self.db.query(
            func.sum(Product.stock_level * Product.cost_price).label('total_cost_value'),
            func.sum(Product.stock_level * Product.selling_price).label('total_selling_value')
        ).filter(Product.status == "active").first()
        
        return {
            "stock_distribution": [
                {
                    "status": item.stock_status,
                    "products": item.count,
                    "total_units": int(item.total_units or 0)
                }
                for item in stock_dist
            ],
            "category_inventory": [
                {
                    "category": item.category or "Uncategorized",
                    "products": item.products,
                    "total_stock": int(item.total_stock or 0),
                    "total_value": float(item.total_value or 0)
                }
                for item in category_inv
            ],
            "total_inventory_value": {
                "cost_value": float(total_value.total_cost_value or 0),
                "selling_value": float(total_value.total_selling_value or 0),
                "potential_profit": float((total_value.total_selling_value or 0) - (total_value.total_cost_value or 0))
            }
        }
    
    # ===========================================
    # SUPPLIER RELATIONSHIPS
    # ===========================================
    
    def add_supplier_to_product(self, supplier_product_data: SupplierProductCreate) -> SupplierProduct:
        """Add supplier relationship to product"""
        try:
            # Check if relationship already exists
            existing = self.db.query(SupplierProduct).filter(
                and_(
                    SupplierProduct.supplier_id == supplier_product_data.supplier_id,
                    SupplierProduct.product_id == supplier_product_data.product_id
                )
            ).first()
            
            if existing:
                raise ValueError("Supplier-Product relationship already exists")
            
            # Create new relationship
            db_supplier_product = SupplierProduct(
                supplier_id=supplier_product_data.supplier_id,
                product_id=supplier_product_data.product_id,
                supplier_sku=supplier_product_data.supplier_sku,
                supplier_name=supplier_product_data.supplier_name,
                supplier_cost=supplier_product_data.supplier_cost,
                lead_time_days=supplier_product_data.lead_time_days,
                minimum_quantity=supplier_product_data.minimum_quantity,
                quality_rating=supplier_product_data.quality_rating,
                is_preferred=supplier_product_data.is_preferred,
                notes=supplier_product_data.notes,
                status="active"
            )
            
            self.db.add(db_supplier_product)
            
            # If this is preferred supplier, update product's primary supplier
            if supplier_product_data.is_preferred:
                product = self.get_product(supplier_product_data.product_id)
                if product:
                    product.primary_supplier_id = supplier_product_data.supplier_id
                    # Update cost price if provided
                    if supplier_product_data.supplier_cost:
                        old_cost = product.cost_price
                        product.cost_price = supplier_product_data.supplier_cost
                        # Recalculate profit margin
                        if product.selling_price:
                            product.profit_margin_percent = ((product.selling_price - product.cost_price) / product.selling_price) * 100
                        
                        # Create price history
                        self._create_price_history(
                            product_id=product.id,
                            old_cost=old_cost,
                            new_cost=product.cost_price,
                            change_reason=f"Updated from preferred supplier {supplier_product_data.supplier_name}",
                            change_type="cost_update",
                            supplier_id=supplier_product_data.supplier_id
                        )
            
            self.db.commit()
            self.db.refresh(db_supplier_product)
            
            return db_supplier_product
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to add supplier to product: {str(e)}")
    
    def get_product_suppliers(self, product_id: int) -> List[SupplierProduct]:
        """Get all suppliers for a product"""
        return self.db.query(SupplierProduct)\
            .filter(SupplierProduct.product_id == product_id)\
            .order_by(desc(SupplierProduct.is_preferred), SupplierProduct.supplier_cost)\
            .all()
    
    def get_supplier_products(self, supplier_id: int) -> List[SupplierProduct]:
        """Get all products for a supplier"""
        return self.db.query(SupplierProduct)\
            .filter(SupplierProduct.supplier_id == supplier_id)\
            .order_by(SupplierProduct.supplier_name)\
            .all()
    
    # ===========================================
    # PERFORMANCE & ANALYTICS
    # ===========================================
    
    def update_product_performance(self, product_id: int) -> bool:
        """Update product performance metrics from order data"""
        try:
            product = self.get_product(product_id)
            if not product:
                return False
            
            # Get order statistics
            order_stats = self.db.query(
                func.count(OrderItem.id).label('total_orders'),
                func.sum(OrderItem.quantity).label('total_quantity'),
                func.sum(OrderItem.total_price).label('total_revenue'),
                func.avg(OrderItem.customer_rating).label('avg_rating'),
                func.count(
                    func.nullif(OrderItem.return_requested == True, False)
                ).label('returns'),
                func.max(OrderItem.created_at).label('last_sold')
            ).filter(OrderItem.product_id == product_id).first()
            
            # Update product metrics
            product.total_sales = int(order_stats.total_quantity or 0)
            product.total_revenue = float(order_stats.total_revenue or 0)
            product.average_rating = float(order_stats.avg_rating or 0)
            
            # Calculate return rate
            total_orders = order_stats.total_orders or 0
            returns = order_stats.returns or 0
            product.return_rate_percent = (returns / total_orders * 100) if total_orders > 0 else 0
            
            # Update last sold date
            if order_stats.last_sold:
                product.last_sold_date = order_stats.last_sold
            
            product.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to update product performance: {str(e)}")
    
    def get_product_performance_stats(self, product_id: int) -> Optional[ProductPerformanceStats]:
        """Get detailed performance statistics for a product"""
        product = self.get_product(product_id)
        if not product:
            return None
        
        # Calculate inventory turnover (sales / average stock)
        # Simplified calculation using current stock level
        inventory_turnover = 0.0
        if product.stock_level > 0:
            inventory_turnover = product.total_sales / product.stock_level
        
        return ProductPerformanceStats(
            product_id=product.id,
            sku=product.sku,
            name=product.name,
            total_sales=product.total_sales,
            total_revenue=product.total_revenue,
            profit_margin=float(product.profit_margin_percent or 0),
            inventory_turnover=inventory_turnover,
            return_rate=product.return_rate_percent
        )
    
    def get_top_products(self, limit: int = 10, metric: str = "revenue") -> List[ProductPerformanceStats]:
        """Get top performing products by specified metric"""
        
        if metric == "revenue":
            order_by = desc(Product.total_revenue)
        elif metric == "sales":
            order_by = desc(Product.total_sales)
        elif metric == "rating":
            order_by = desc(Product.average_rating)
        elif metric == "margin":
            order_by = desc(Product.profit_margin_percent)
        else:
            order_by = desc(Product.total_revenue)
        
        products = self.db.query(Product)\
            .filter(Product.status == "active")\
            .order_by(order_by)\
            .limit(limit)\
            .all()
        
        stats = []
        for product in products:
            stat = self.get_product_performance_stats(product.id)
            if stat:
                stats.append(stat)
        
        return stats
    
    # ===========================================
    # HELPER METHODS
    # ===========================================
    
    def _calculate_stock_status(self, stock_level: int, reorder_point: int) -> StockStatus:
        """Calculate stock status based on current levels"""
        if stock_level == 0:
            return StockStatus.OUT_OF_STOCK
        elif stock_level <= reorder_point:
            if stock_level <= reorder_point * 0.5:
                return StockStatus.LOW_STOCK
            else:
                return StockStatus.REORDER_NEEDED
        else:
            return StockStatus.IN_STOCK
    
    def _create_price_history(
        self,
        product_id: int,
        old_cost: Optional[float] = None,
        new_cost: Optional[float] = None,
        old_selling_price: Optional[float] = None,
        new_selling_price: Optional[float] = None,
        change_reason: str = "",
        change_type: str = "price_update",
        supplier_id: Optional[int] = None
    ) -> None:
        """Create price history record"""
        
        # Calculate impact percentage
        impact_percent = None
        if old_selling_price and new_selling_price and old_selling_price > 0:
            impact_percent = ((new_selling_price - old_selling_price) / old_selling_price) * 100
        
        price_history = PriceHistory(
            product_id=product_id,
            supplier_id=supplier_id,
            old_cost=old_cost,
            new_cost=new_cost,
            old_selling_price=old_selling_price,
            new_selling_price=new_selling_price,
            change_reason=change_reason,
            change_type=change_type,
            impact_percent=impact_percent,
            changed_by="system"  # Could be enhanced to track actual user
        )
        
        self.db.add(price_history)
    
    def get_price_history(self, product_id: int, limit: Optional[int] = 20) -> List[PriceHistory]:
        """Get price history for a product"""
        query = self.db.query(PriceHistory)\
            .filter(PriceHistory.product_id == product_id)\
            .order_by(desc(PriceHistory.created_at))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def bulk_update_performance(self) -> Dict[str, int]:
        """Update performance metrics for all active products"""
        try:
            active_products = self.db.query(Product)\
                .filter(Product.status == "active")\
                .all()
            
            updated = 0
            failed = 0
            
            for product in active_products:
                try:
                    self.update_product_performance(product.id)
                    updated += 1
                except Exception:
                    failed += 1
                    continue
            
            return {
                "total": len(active_products),
                "updated": updated,
                "failed": failed
            }
            
        except Exception as e:
            raise Exception(f"Failed to bulk update performance: {str(e)}")