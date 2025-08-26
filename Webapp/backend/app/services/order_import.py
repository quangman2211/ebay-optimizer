"""
Order Import Service following Open/Closed Principle (OCP)
Extensible for different import sources without modifying existing code
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.services.interfaces import IDataValidator, IDataTransformer, INotificationService
from app.services.google_sheets import GoogleSheetsService
from app.models.database_models import Order, Account, User, SheetsSyncLog, OrderStatusHistory
from app.core.rbac import RBACService

logger = logging.getLogger(__name__)


class ImportSource(str, Enum):
    """Import source types - extensible"""
    GOOGLE_SHEETS = "google_sheets"
    MANUAL_CSV = "manual_csv"
    EBAY_API = "ebay_api"
    WEBHOOK = "webhook"


class ImportStatus(str, Enum):
    """Import operation status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class ImportResult:
    """Result of import operation"""
    status: ImportStatus
    total_rows: int
    successful_imports: int
    failed_imports: int
    errors: List[str]
    warnings: List[str]
    import_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None


class IOrderImporter(ABC):
    """Interface for order importers - Open for extension"""
    
    @abstractmethod
    async def import_orders(
        self, 
        source_config: Dict[str, Any], 
        account_id: int, 
        user_id: int
    ) -> ImportResult:
        """Import orders from specific source"""
        pass
    
    @abstractmethod
    def get_source_type(self) -> ImportSource:
        """Get the source type this importer handles"""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate source configuration"""
        pass


class OrderDataValidator(IDataValidator):
    """Validates order data before import - Single Responsibility"""
    
    def validate_order(self, order_data: Dict) -> tuple[bool, List[str]]:
        """Validate individual order data"""
        errors = []
        
        # Required fields validation
        required_fields = [
            'customer_email', 'customer_name', 'shipping_address',
            'product_title', 'quantity', 'price_ebay'
        ]
        
        for field in required_fields:
            if not order_data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Data format validation
        try:
            quantity = int(order_data.get('quantity', 0))
            if quantity <= 0:
                errors.append("Quantity must be positive integer")
        except (ValueError, TypeError):
            errors.append("Invalid quantity format")
        
        try:
            price = float(order_data.get('price_ebay', 0))
            if price <= 0:
                errors.append("Price must be positive number")
        except (ValueError, TypeError):
            errors.append("Invalid price format")
        
        # Email validation
        email = order_data.get('customer_email', '')
        if email and '@' not in email:
            errors.append("Invalid email format")
        
        return len(errors) == 0, errors
    
    def validate_address(self, address: str) -> tuple[bool, str]:
        """Basic address validation"""
        if not address or len(address.strip()) < 10:
            return False, "high"  # Too short addresses are risky
        
        # Basic blacklist words (should be extended)
        blacklist_words = ['po box', 'pobox', 'freight forwarder', 'mail forwarding']
        address_lower = address.lower()
        
        for word in blacklist_words:
            if word in address_lower:
                return False, "blocked"
        
        return True, "clean"


class OrderDataTransformer(IDataTransformer):
    """Transforms order data between formats - Single Responsibility"""
    
    def transform_to_order(self, raw_data: Dict) -> Dict:
        """Transform raw import data to order format"""
        # Handle different field name mappings from various sources
        field_mappings = {
            # Google Sheets mappings
            'Customer_Name': 'customer_name',
            'Customer_Email': 'customer_email',
            'Customer_Phone': 'customer_phone',
            'Shipping_Address': 'shipping_address',
            'Product_Title': 'product_title',
            'Order_Date': 'order_date',
            'eBay_Order_ID': 'ebay_order_id',
            'Price': 'price_ebay',
            'Quantity': 'quantity',
            'Tracking_Number': 'tracking_number',
            'Carrier': 'carrier',
            'Status': 'status',
            
            # Alternative field names
            'customer': 'customer_name',
            'email': 'customer_email',
            'phone': 'customer_phone',
            'address': 'shipping_address',
            'title': 'product_title',
            'date': 'order_date',
            'ebay_id': 'ebay_order_id',
            'amount': 'price_ebay',
            'qty': 'quantity'
        }
        
        transformed = {}
        
        # Apply field mappings
        for source_field, target_field in field_mappings.items():
            if source_field in raw_data:
                transformed[target_field] = raw_data[source_field]
        
        # Copy unmapped fields directly
        for key, value in raw_data.items():
            if key not in field_mappings and not key.startswith('_'):
                transformed[key] = value
        
        # Set default values
        transformed.setdefault('status', 'pending')
        transformed.setdefault('sync_source', 'google_sheets')
        transformed.setdefault('created_at', datetime.now())
        
        # Store original row reference
        if '_row_id' in raw_data:
            transformed['sheets_row_id'] = raw_data['_row_id']
        if '_source_id' in raw_data:
            transformed['sheets_source_id'] = raw_data['_source_id']
        
        return transformed
    
    def transform_from_order(self, order: Any) -> Dict:
        """Transform order model to export format"""
        return {
            'Order_ID': order.id,
            'eBay_Order_ID': order.ebay_order_id or '',
            'Customer_Name': order.customer_name or '',
            'Customer_Email': order.customer_email or '',
            'Customer_Phone': order.customer_phone or '',
            'Shipping_Address': order.shipping_address or '',
            'Product_Title': order.product_title or '',
            'Quantity': order.quantity or 1,
            'Price': order.price_ebay or 0,
            'Order_Date': order.order_date.isoformat() if order.order_date else '',
            'Status': order.status or 'pending',
            'Tracking_Number': order.tracking_number or '',
            'Carrier': order.carrier or '',
            'Last_Update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


class GoogleSheetsOrderImporter(IOrderImporter):
    """Google Sheets order importer - Concrete implementation"""
    
    def __init__(
        self, 
        sheets_service: GoogleSheetsService,
        validator: IDataValidator,
        transformer: IDataTransformer,
        db: Session
    ):
        self.sheets_service = sheets_service
        self.validator = validator
        self.transformer = transformer
        self.db = db
    
    def get_source_type(self) -> ImportSource:
        return ImportSource.GOOGLE_SHEETS
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate Google Sheets configuration"""
        errors = []
        
        required_fields = ['spreadsheet_id', 'sheet_name', 'range']
        for field in required_fields:
            if not config.get(field):
                errors.append(f"Missing required config: {field}")
        
        # Validate spreadsheet_id format
        spreadsheet_id = config.get('spreadsheet_id', '')
        if spreadsheet_id and len(spreadsheet_id) < 40:
            errors.append("Invalid spreadsheet_id format")
        
        return len(errors) == 0, errors
    
    async def import_orders(
        self, 
        source_config: Dict[str, Any], 
        account_id: int, 
        user_id: int
    ) -> ImportResult:
        """Import orders from Google Sheets"""
        import_id = f"import_{account_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        started_at = datetime.now()
        
        # Validate configuration
        is_valid_config, config_errors = self.validate_config(source_config)
        if not is_valid_config:
            return ImportResult(
                status=ImportStatus.FAILED,
                total_rows=0,
                successful_imports=0,
                failed_imports=0,
                errors=config_errors,
                warnings=[],
                import_id=import_id,
                started_at=started_at,
                completed_at=datetime.now()
            )
        
        try:
            # Create sync log entry
            sync_log = SheetsSyncLog(
                sync_type="import",
                spreadsheet_id=source_config['spreadsheet_id'],
                sheet_name=source_config['sheet_name'],
                started_by=user_id,
                status="running"
            )
            self.db.add(sync_log)
            self.db.commit()
            
            # Read data from Google Sheets
            raw_data = await self.sheets_service.read_orders(source_config)
            
            total_rows = len(raw_data)
            successful_imports = 0
            failed_imports = 0
            errors = []
            warnings = []
            
            # Process each row
            for i, row_data in enumerate(raw_data):
                try:
                    # Transform data
                    transformed_data = self.transformer.transform_to_order(row_data)
                    
                    # Validate data
                    is_valid, validation_errors = self.validator.validate_order(transformed_data)
                    if not is_valid:
                        errors.extend([f"Row {i+1}: {error}" for error in validation_errors])
                        failed_imports += 1
                        continue
                    
                    # Check for duplicate orders
                    ebay_order_id = transformed_data.get('ebay_order_id')
                    if ebay_order_id:
                        existing_order = (
                            self.db.query(Order)
                            .filter(
                                Order.ebay_order_id == ebay_order_id,
                                Order.account_id == account_id
                            )
                            .first()
                        )
                        if existing_order:
                            warnings.append(f"Row {i+1}: Duplicate order {ebay_order_id} - updated existing")
                            # Update existing order
                            for key, value in transformed_data.items():
                                if hasattr(existing_order, key) and value:
                                    setattr(existing_order, key, value)
                            existing_order.sheets_last_sync = datetime.now()
                            successful_imports += 1
                            continue
                    
                    # Validate address against blacklist
                    address = transformed_data.get('shipping_address', '')
                    is_safe_address, risk_level = self.validator.validate_address(address)
                    transformed_data['blacklist_checked'] = True
                    transformed_data['blacklist_status'] = risk_level
                    if not is_safe_address:
                        transformed_data['blacklist_reason'] = "Address matched blacklist pattern"
                        warnings.append(f"Row {i+1}: Address flagged as {risk_level}")
                    
                    # Create new order
                    order = Order(
                        account_id=account_id,
                        user_id=user_id,
                        **transformed_data
                    )
                    self.db.add(order)
                    
                    # Create status history entry
                    status_history = OrderStatusHistory(
                        order_id=order.id,
                        old_status=None,
                        new_status="pending",
                        changed_by=user_id,
                        change_reason=f"Imported from Google Sheets: {source_config['sheet_name']}"
                    )
                    self.db.add(status_history)
                    
                    successful_imports += 1
                    
                except Exception as e:
                    error_msg = f"Row {i+1}: {str(e)}"
                    errors.append(error_msg)
                    failed_imports += 1
                    logger.error(f"Error importing row {i+1}: {e}")
            
            # Update sync log
            sync_log.rows_processed = total_rows
            sync_log.rows_success = successful_imports
            sync_log.rows_error = failed_imports
            sync_log.completed_at = datetime.now()
            sync_log.status = "completed" if failed_imports == 0 else "partial"
            sync_log.error_details = {"errors": errors, "warnings": warnings}
            
            # Commit all changes
            self.db.commit()
            
            # Determine final status
            if failed_imports == 0:
                final_status = ImportStatus.COMPLETED
            elif successful_imports == 0:
                final_status = ImportStatus.FAILED
            else:
                final_status = ImportStatus.PARTIAL
            
            return ImportResult(
                status=final_status,
                total_rows=total_rows,
                successful_imports=successful_imports,
                failed_imports=failed_imports,
                errors=errors,
                warnings=warnings,
                import_id=import_id,
                started_at=started_at,
                completed_at=datetime.now(),
                metadata={
                    "sync_log_id": sync_log.id,
                    "spreadsheet_id": source_config['spreadsheet_id'],
                    "sheet_name": source_config['sheet_name']
                }
            )
            
        except Exception as e:
            # Update sync log with error
            if 'sync_log' in locals():
                sync_log.status = "failed"
                sync_log.error_details = {"errors": [str(e)]}
                sync_log.completed_at = datetime.now()
                self.db.commit()
            
            logger.error(f"Failed to import orders from Google Sheets: {e}")
            return ImportResult(
                status=ImportStatus.FAILED,
                total_rows=0,
                successful_imports=0,
                failed_imports=0,
                errors=[str(e)],
                warnings=[],
                import_id=import_id,
                started_at=started_at,
                completed_at=datetime.now()
            )


class OrderImportService:
    """Main service for importing orders - follows OCP principle"""
    
    def __init__(self, db: Session, rbac_service: RBACService):
        self.db = db
        self.rbac_service = rbac_service
        self.importers: Dict[ImportSource, IOrderImporter] = {}
        self.validator = OrderDataValidator()
        self.transformer = OrderDataTransformer()
    
    def register_importer(self, importer: IOrderImporter) -> None:
        """Register new importer - Open for extension"""
        source_type = importer.get_source_type()
        self.importers[source_type] = importer
        logger.info(f"Registered importer for source: {source_type}")
    
    def get_available_sources(self) -> List[ImportSource]:
        """Get list of available import sources"""
        return list(self.importers.keys())
    
    async def import_orders(
        self,
        source_type: ImportSource,
        source_config: Dict[str, Any],
        account_id: int,
        user_id: int
    ) -> ImportResult:
        """Import orders using specified source"""
        if source_type not in self.importers:
            return ImportResult(
                status=ImportStatus.FAILED,
                total_rows=0,
                successful_imports=0,
                failed_imports=0,
                errors=[f"No importer registered for source: {source_type}"],
                warnings=[],
                import_id="unknown",
                started_at=datetime.now(),
                completed_at=datetime.now()
            )
        
        # Verify user permissions
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return ImportResult(
                status=ImportStatus.FAILED,
                total_rows=0,
                successful_imports=0,
                failed_imports=0,
                errors=["User not found"],
                warnings=[],
                import_id="unauthorized",
                started_at=datetime.now(),
                completed_at=datetime.now()
            )
        
        # Check permissions
        has_permission = self.rbac_service.has_permission(user, "orders.import")
        if not has_permission:
            return ImportResult(
                status=ImportStatus.FAILED,
                total_rows=0,
                successful_imports=0,
                failed_imports=0,
                errors=["Insufficient permissions for order import"],
                warnings=[],
                import_id="unauthorized",
                started_at=datetime.now(),
                completed_at=datetime.now()
            )
        
        # Verify account access
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            return ImportResult(
                status=ImportStatus.FAILED,
                total_rows=0,
                successful_imports=0,
                failed_imports=0,
                errors=[f"Account {account_id} not found"],
                warnings=[],
                import_id="not_found",
                started_at=datetime.now(),
                completed_at=datetime.now()
            )
        
        # Execute import
        importer = self.importers[source_type]
        return await importer.import_orders(source_config, account_id, user_id)
    
    async def get_import_history(self, account_id: Optional[int] = None) -> List[Dict]:
        """Get import history for account or all accounts"""
        query = self.db.query(SheetsSyncLog).filter(SheetsSyncLog.sync_type == "import")
        
        if account_id:
            # Filter by account through orders
            query = query.join(Order, SheetsSyncLog.spreadsheet_id == Order.sheets_source_id)
            query = query.filter(Order.account_id == account_id)
        
        logs = query.order_by(SheetsSyncLog.started_at.desc()).limit(50).all()
        
        history = []
        for log in logs:
            history.append({
                "id": log.id,
                "sync_type": log.sync_type,
                "spreadsheet_id": log.spreadsheet_id,
                "sheet_name": log.sheet_name,
                "rows_processed": log.rows_processed,
                "rows_success": log.rows_success,
                "rows_error": log.rows_error,
                "status": log.status,
                "started_at": log.started_at.isoformat(),
                "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                "started_by": log.started_by,
                "error_details": log.error_details
            })
        
        return history