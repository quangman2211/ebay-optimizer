"""
CSV Import Service
Handles importing and processing CSV data from eBay reports
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import pandas as pd

from app.core.config import settings
from app.domain.models.enums import OrderStatusEnum, ListingStatusEnum
from app.repositories.order import OrderRepository
from app.repositories.listing import ListingRepository
from app.repositories.account import AccountRepository
from app.services.infrastructure.sheets_data_service import SheetsDataService

logger = logging.getLogger(__name__)

class CSVImportService:
    """Service for importing CSV data from eBay reports"""
    
    def __init__(self, db: Session):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.listing_repo = ListingRepository(db)
        self.account_repo = AccountRepository(db)
        self.sheets_service = SheetsDataService()
        
        # CSV field mapping
        self.order_field_mapping = {
            'Sales Record Number': 'sales_record_number',
            'Order Number': 'order_number',
            'Buyer Username': 'buyer_username',
            'Buyer Name': 'buyer_name',
            'Buyer Email': 'buyer_email',
            'Item Number': 'item_number',
            'Item Title': 'item_title',
            'Custom Label': 'custom_label',
            'Quantity': 'quantity',
            'Sold For': 'sold_for',
            'Total Price': 'total_price',
            'Sale Date': 'sale_date',
            'Paid On Date': 'paid_date',
            'Ship By Date': 'ship_by_date',
            'Tracking Number': 'tracking_number'
        }
        
        self.listing_field_mapping = {
            'Item number': 'item_number',
            'Title': 'title',
            'Custom label (SKU)': 'custom_label',
            'Available quantity': 'available_quantity',
            'Current price': 'current_price',
            'Sold quantity': 'sold_quantity',
            'Watchers': 'watchers',
            'Start date': 'start_date',
            'End date': 'end_date',
            'Condition': 'condition'
        }

    async def import_orders_from_sheets(
        self,
        sheet_id: str,
        account_id: int,
        user_id: int,
        import_options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Import orders from Google Sheets"""
        try:
            logger.info(f"Starting orders import from sheet {sheet_id}")
            
            # Get account
            account = self.account_repo.get_by_id(account_id)
            if not account:
                raise Exception(f"Account {account_id} not found")
            
            # Fetch data from Google Sheets
            sheet_data = await self.sheets_service.get_sheet_data(
                sheet_id=sheet_id,
                sheet_name="Orders"
            )
            
            if not sheet_data or len(sheet_data) == 0:
                logger.warning(f"No data found in sheet {sheet_id}")
                return {"success": True, "imported_count": 0, "message": "No data to import"}
            
            # Process and validate data
            processed_data = self._process_order_data(sheet_data, account)
            validation_result = self._validate_order_data(processed_data)
            
            if not validation_result["is_valid"]:
                logger.error(f"Data validation failed: {validation_result['errors']}")
                return {
                    "success": False,
                    "error": "Data validation failed",
                    "validation_errors": validation_result["errors"]
                }
            
            # Import valid records
            imported_count = 0
            errors = []
            
            for order_data in validation_result["valid_records"]:
                try:
                    # Check if order already exists
                    existing_order = self.order_repo.get_by_order_number(
                        order_data["order_number"]
                    )
                    
                    if existing_order:
                        # Update existing order
                        updated_order = self.order_repo.update(
                            existing_order.id, order_data
                        )
                        logger.debug(f"Updated order {order_data['order_number']}")
                    else:
                        # Create new order
                        new_order = self.order_repo.create(order_data)
                        logger.debug(f"Created order {order_data['order_number']}")
                    
                    imported_count += 1
                    
                except Exception as e:
                    error_msg = f"Failed to import order {order_data.get('order_number', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            result = {
                "success": True,
                "imported_count": imported_count,
                "total_records": len(sheet_data),
                "valid_records": len(validation_result["valid_records"]),
                "invalid_records": validation_result["invalid_records"],
                "errors": errors,
                "account_id": account_id,
                "sheet_id": sheet_id
            }
            
            logger.info(f"Orders import completed: {imported_count} imported, {len(errors)} errors")
            return result
            
        except Exception as e:
            logger.error(f"Orders import failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def import_listings_from_sheets(
        self,
        sheet_id: str,
        account_id: int,
        user_id: int,
        import_options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Import listings from Google Sheets"""
        try:
            logger.info(f"Starting listings import from sheet {sheet_id}")
            
            # Get account
            account = self.account_repo.get_by_id(account_id)
            if not account:
                raise Exception(f"Account {account_id} not found")
            
            # Fetch data from Google Sheets
            sheet_data = await self.sheets_service.get_sheet_data(
                sheet_id=sheet_id,
                sheet_name="Listings"
            )
            
            if not sheet_data or len(sheet_data) == 0:
                logger.warning(f"No data found in sheet {sheet_id}")
                return {"success": True, "imported_count": 0, "message": "No data to import"}
            
            # Process and validate data
            processed_data = self._process_listing_data(sheet_data, account)
            validation_result = self._validate_listing_data(processed_data)
            
            if not validation_result["is_valid"]:
                logger.error(f"Data validation failed: {validation_result['errors']}")
                return {
                    "success": False,
                    "error": "Data validation failed",
                    "validation_errors": validation_result["errors"]
                }
            
            # Import valid records
            imported_count = 0
            errors = []
            
            for listing_data in validation_result["valid_records"]:
                try:
                    # Check if listing already exists
                    existing_listing = self.listing_repo.get_by_item_number(
                        listing_data["item_number"]
                    )
                    
                    if existing_listing:
                        # Update existing listing
                        updated_listing = self.listing_repo.update(
                            existing_listing.id, listing_data
                        )
                        logger.debug(f"Updated listing {listing_data['item_number']}")
                    else:
                        # Create new listing
                        new_listing = self.listing_repo.create(listing_data)
                        logger.debug(f"Created listing {listing_data['item_number']}")
                    
                    imported_count += 1
                    
                except Exception as e:
                    error_msg = f"Failed to import listing {listing_data.get('item_number', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            result = {
                "success": True,
                "imported_count": imported_count,
                "total_records": len(sheet_data),
                "valid_records": len(validation_result["valid_records"]),
                "invalid_records": validation_result["invalid_records"],
                "errors": errors,
                "account_id": account_id,
                "sheet_id": sheet_id
            }
            
            logger.info(f"Listings import completed: {imported_count} imported, {len(errors)} errors")
            return result
            
        except Exception as e:
            logger.error(f"Listings import failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def _process_order_data(self, raw_data: List[Dict], account) -> List[Dict]:
        """Process raw order data from CSV"""
        processed_data = []
        
        for row in raw_data:
            try:
                processed_row = {
                    "account_id": account.id,
                    "import_source": "csv_import",
                    "import_timestamp": datetime.now(),
                    "status": OrderStatusEnum.AWAITING_SHIPMENT
                }
                
                # Map CSV fields to database fields
                for csv_field, db_field in self.order_field_mapping.items():
                    if csv_field in row:
                        value = row[csv_field]
                        
                        # Clean and format the value
                        if db_field in ['sold_for', 'total_price']:
                            processed_row[db_field] = self._parse_currency(value)
                        elif db_field == 'quantity':
                            processed_row[db_field] = self._parse_integer(value)
                        elif db_field in ['sale_date', 'paid_date', 'ship_by_date']:
                            processed_row[db_field] = self._parse_date(value)
                        else:
                            processed_row[db_field] = str(value).strip() if value else None
                
                processed_data.append(processed_row)
                
            except Exception as e:
                logger.warning(f"Failed to process order row: {str(e)}")
                continue
        
        return processed_data

    def _process_listing_data(self, raw_data: List[Dict], account) -> List[Dict]:
        """Process raw listing data from CSV"""
        processed_data = []
        
        for row in raw_data:
            try:
                processed_row = {
                    "account_id": account.id,
                    "import_source": "csv_import",
                    "import_timestamp": datetime.now(),
                    "status": ListingStatusEnum.ACTIVE
                }
                
                # Map CSV fields to database fields
                for csv_field, db_field in self.listing_field_mapping.items():
                    if csv_field in row:
                        value = row[csv_field]
                        
                        # Clean and format the value
                        if db_field == 'current_price':
                            processed_row[db_field] = self._parse_currency(value)
                        elif db_field in ['available_quantity', 'sold_quantity', 'watchers']:
                            processed_row[db_field] = self._parse_integer(value)
                        elif db_field in ['start_date', 'end_date']:
                            processed_row[db_field] = self._parse_date(value)
                        else:
                            processed_row[db_field] = str(value).strip() if value else None
                
                processed_data.append(processed_row)
                
            except Exception as e:
                logger.warning(f"Failed to process listing row: {str(e)}")
                continue
        
        return processed_data

    def _validate_order_data(self, data: List[Dict]) -> Dict[str, Any]:
        """Validate processed order data"""
        valid_records = []
        invalid_records = 0
        errors = []
        warnings = []
        
        required_fields = ['order_number', 'buyer_name', 'item_number', 'total_price']
        
        for i, record in enumerate(data):
            try:
                record_errors = []
                
                # Check required fields
                for field in required_fields:
                    if not record.get(field):
                        record_errors.append(f"Missing required field: {field}")
                
                # Validate data types and ranges
                if record.get('total_price', 0) <= 0:
                    record_errors.append("Total price must be greater than 0")
                
                if record.get('quantity', 0) <= 0:
                    record_errors.append("Quantity must be greater than 0")
                
                if record_errors:
                    invalid_records += 1
                    errors.extend([f"Row {i+1}: {error}" for error in record_errors])
                else:
                    valid_records.append(record)
                    
            except Exception as e:
                invalid_records += 1
                errors.append(f"Row {i+1}: Validation error - {str(e)}")
        
        return {
            "is_valid": len(valid_records) > 0,
            "valid_records": valid_records,
            "invalid_records": invalid_records,
            "errors": errors,
            "warnings": warnings,
            "total_records": len(data)
        }

    def _validate_listing_data(self, data: List[Dict]) -> Dict[str, Any]:
        """Validate processed listing data"""
        valid_records = []
        invalid_records = 0
        errors = []
        warnings = []
        
        required_fields = ['item_number', 'title', 'current_price']
        
        for i, record in enumerate(data):
            try:
                record_errors = []
                
                # Check required fields
                for field in required_fields:
                    if not record.get(field):
                        record_errors.append(f"Missing required field: {field}")
                
                # Validate data types and ranges
                if record.get('current_price', 0) <= 0:
                    record_errors.append("Current price must be greater than 0")
                
                if record.get('available_quantity', 0) < 0:
                    record_errors.append("Available quantity cannot be negative")
                
                if record_errors:
                    invalid_records += 1
                    errors.extend([f"Row {i+1}: {error}" for error in record_errors])
                else:
                    valid_records.append(record)
                    
            except Exception as e:
                invalid_records += 1
                errors.append(f"Row {i+1}: Validation error - {str(e)}")
        
        return {
            "is_valid": len(valid_records) > 0,
            "valid_records": valid_records,
            "invalid_records": invalid_records,
            "errors": errors,
            "warnings": warnings,
            "total_records": len(data)
        }

    def _parse_currency(self, value: str) -> float:
        """Parse currency string to float"""
        if not value:
            return 0.0
        
        try:
            # Remove currency symbols and commas
            cleaned = str(value).replace('$', '').replace(',', '').strip()
            return float(cleaned) if cleaned else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _parse_integer(self, value: str) -> int:
        """Parse string to integer"""
        if not value:
            return 0
        
        try:
            # Remove non-numeric characters except decimal point
            cleaned = str(value).replace(',', '').strip()
            return int(float(cleaned)) if cleaned else 0
        except (ValueError, TypeError):
            return 0

    def _parse_date(self, value: str) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not value:
            return None
        
        try:
            # Handle eBay date format: Aug-21-25
            date_str = str(value).strip()
            if '-' in date_str:
                parts = date_str.split('-')
                if len(parts) == 3:
                    month_names = {
                        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
                        'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
                        'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                    }
                    
                    month = month_names.get(parts[0], 1)
                    day = int(parts[1])
                    year = 2000 + int(parts[2])
                    
                    return datetime(year, month, day)
            
            # Try standard date parsing
            return datetime.fromisoformat(date_str)
            
        except (ValueError, TypeError, IndexError):
            logger.warning(f"Failed to parse date: {value}")
            return None

    async def get_import_status(self, import_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an import operation"""
        # This would typically query a database table storing import status
        # For now, return a mock status
        return {
            "import_id": import_id,
            "status": "completed",
            "progress": 100,
            "message": "Import completed successfully"
        }

    async def get_import_history(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        import_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get import history for a user"""
        # This would typically query a database table storing import history
        # For now, return a mock history
        return {
            "imports": [],
            "total_count": 0
        }

    async def sync_from_sheets(
        self,
        sheet_id: str,
        account_id: int,
        data_type: str,
        user_id: int,
        sync_options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Sync data from Google Sheets"""
        try:
            logger.info(f"Starting sync from sheets: {sheet_id}, type: {data_type}")
            
            if data_type == "orders":
                result = await self.import_orders_from_sheets(
                    sheet_id, account_id, user_id, sync_options
                )
            elif data_type == "listings":
                result = await self.import_listings_from_sheets(
                    sheet_id, account_id, user_id, sync_options
                )
            else:
                raise ValueError(f"Unknown data type: {data_type}")
            
            return result
            
        except Exception as e:
            logger.error(f"Sync failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def validate_csv_data(
        self,
        data: List[Dict],
        import_type: str,
        account_id: int
    ) -> Dict[str, Any]:
        """Validate CSV data before importing"""
        try:
            account = self.account_repo.get_by_id(account_id)
            if not account:
                return {"is_valid": False, "errors": [f"Account {account_id} not found"]}
            
            if import_type == "orders":
                processed_data = self._process_order_data(data, account)
                return self._validate_order_data(processed_data)
            elif import_type == "listings":
                processed_data = self._process_listing_data(data, account)
                return self._validate_listing_data(processed_data)
            else:
                return {"is_valid": False, "errors": [f"Unknown import type: {import_type}"]}
                
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            return {"is_valid": False, "errors": [str(e)]}