"""
Enhanced Google Sheets Service - SOLID Architecture Implementation
Handles comprehensive multi-sheet integration with supplier/product management
Single Responsibility: Manages enhanced Google Sheets operations with per-account sheets
"""

import os
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import json

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    print("Warning: Google API libraries not installed. Using fallback mode.")

from app.core.config import settings
from app.models.database_models import Supplier, Product


class EnhancedGoogleSheetsService:
    """
    SOLID Principle: Single Responsibility
    Enhanced Google Sheets service for comprehensive supplier/product management
    Supports per-account sheets with multiple tabs
    """
    
    def __init__(self):
        self.service = None
        self.use_fallback = False
        self.fallback_data = {}
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Sheets API service or fallback mode"""
        use_fallback = os.getenv('USE_FALLBACK_DATA', 'false').lower() == 'true'
        
        if use_fallback or not GOOGLE_API_AVAILABLE:
            self._initialize_fallback_mode()
            return
            
        try:
            if os.path.exists(settings.GOOGLE_SHEETS_CREDENTIALS_PATH):
                credentials = service_account.Credentials.from_service_account_file(
                    settings.GOOGLE_SHEETS_CREDENTIALS_PATH,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                self.service = build('sheets', 'v4', credentials=credentials)
                print("✅ Enhanced Google Sheets service initialized successfully")
            else:
                print(f"Warning: Google Sheets credentials not found at {settings.GOOGLE_SHEETS_CREDENTIALS_PATH}")
                self._initialize_fallback_mode()
        except Exception as e:
            print(f"Error initializing Enhanced Google Sheets service: {e}")
            self._initialize_fallback_mode()
    
    def _initialize_fallback_mode(self):
        """Initialize fallback mode with comprehensive sample data"""
        self.use_fallback = True
        self.fallback_data = {
            'suppliers': [
                {
                    'id': 'SUP_001',
                    'name': 'TechSupply Co',
                    'company_name': 'TechSupply Corporation',
                    'contact_person': 'John Smith',
                    'email': 'john@techsupply.com',
                    'phone': '+1-555-0123',
                    'country': 'USA',
                    'performance_rating': 4.5,
                    'reliability_score': 92,
                    'payment_terms': 'NET 30',
                    'minimum_order_value': 500.00,
                    'currency': 'USD',
                    'status': 'active',
                    'created_at': datetime.now().isoformat()
                }
            ],
            'products': [
                {
                    'id': 'PROD_001',
                    'sku': 'TECH-001',
                    'name': 'Premium Wireless Mouse',
                    'category': 'Electronics',
                    'cost_price': 15.00,
                    'selling_price': 29.99,
                    'stock_level': 150,
                    'minimum_stock': 20,
                    'primary_supplier_id': 'SUP_001',
                    'status': 'active',
                    'created_at': datetime.now().isoformat()
                }
            ],
            'accounts': {
                'seller123@ebay.com': {
                    'orders': [],
                    'listings': [],
                    'messages': [],
                    'draft_listings': []
                }
            }
        }
        print("📦 Using enhanced fallback data with suppliers/products")
    
    # ===========================================
    # CORE SPREADSHEET MANAGEMENT
    # ===========================================
    
    def create_account_spreadsheet(self, account_email: str) -> Optional[str]:
        """Create a comprehensive spreadsheet for a specific eBay account"""
        if self.use_fallback:
            print(f"📝 Fallback: Would create spreadsheet for {account_email}")
            return f"fallback_spreadsheet_{account_email.replace('@', '_').replace('.', '_')}"
        
        if not self.service:
            return None
        
        try:
            # Create new spreadsheet
            spreadsheet_body = {
                'properties': {
                    'title': f'eBay Account - {account_email}',
                    'locale': 'en_US',
                    'timeZone': 'America/New_York'
                }
            }
            
            spreadsheet = self.service.spreadsheets().create(body=spreadsheet_body).execute()
            spreadsheet_id = spreadsheet['spreadsheetId']
            
            # Create all required sheets
            self._create_account_sheets(spreadsheet_id)
            
            print(f"✅ Created account spreadsheet for {account_email}: {spreadsheet_id}")
            return spreadsheet_id
            
        except HttpError as error:
            print(f"Error creating account spreadsheet: {error}")
            return None
    
    def _create_account_sheets(self, spreadsheet_id: str) -> bool:
        """Create all required sheets for an account spreadsheet"""
        try:
            # Define sheets to create
            sheets_config = [
                {'name': 'Orders', 'type': 'orders'},
                {'name': 'Listings', 'type': 'listings'},
                {'name': 'Messages', 'type': 'messages'},
                {'name': 'Draft_Listings', 'type': 'draft_listings'},
                {'name': 'Suppliers', 'type': 'suppliers'},
                {'name': 'Products', 'type': 'products'}
            ]
            
            # First, delete the default "Sheet1"
            self._delete_default_sheet(spreadsheet_id)
            
            # Create all required sheets
            requests = []
            for i, sheet_config in enumerate(sheets_config):
                requests.append({
                    'addSheet': {
                        'properties': {
                            'title': sheet_config['name'],
                            'index': i,
                            'sheetType': 'GRID',
                            'gridProperties': {
                                'rowCount': 1000,
                                'columnCount': 26
                            }
                        }
                    }
                })
            
            # Execute batch request to create sheets
            batch_request_body = {'requests': requests}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=batch_request_body
            ).execute()
            
            # Add headers to each sheet
            for sheet_config in sheets_config:
                self._add_sheet_headers(spreadsheet_id, sheet_config['name'], sheet_config['type'])
            
            print(f"✅ Created {len(sheets_config)} sheets with headers")
            return True
            
        except HttpError as error:
            print(f"Error creating account sheets: {error}")
            return False
    
    def _delete_default_sheet(self, spreadsheet_id: str):
        """Delete the default 'Sheet1' that comes with new spreadsheets"""
        try:
            # Get spreadsheet metadata
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            
            # Find Sheet1
            for sheet in spreadsheet['sheets']:
                if sheet['properties']['title'] == 'Sheet1':
                    sheet_id = sheet['properties']['sheetId']
                    
                    # Delete Sheet1
                    delete_request = {
                        'requests': [{
                            'deleteSheet': {
                                'sheetId': sheet_id
                            }
                        }]
                    }
                    
                    self.service.spreadsheets().batchUpdate(
                        spreadsheetId=spreadsheet_id,
                        body=delete_request
                    ).execute()
                    break
                    
        except HttpError as error:
            print(f"Warning: Could not delete default sheet: {error}")
    
    def _add_sheet_headers(self, spreadsheet_id: str, sheet_name: str, sheet_type: str):
        """Add appropriate headers to a specific sheet"""
        headers = self._get_sheet_headers(sheet_type)
        
        try:
            # Determine range
            last_column = chr(ord('A') + len(headers) - 1)
            range_name = f"{sheet_name}!A1:{last_column}1"
            
            body = {
                'values': [headers]
            }
            
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
        except HttpError as error:
            print(f"Error adding headers to {sheet_name}: {error}")
    
    def _get_sheet_headers(self, sheet_type: str) -> List[str]:
        """Get appropriate headers for different sheet types"""
        headers_map = {
            'orders': [
                'Order ID', 'Order Number', 'Customer Name', 'Customer Email', 
                'Product Name', 'Product SKU', 'Quantity', 'Unit Price', 'Total Price',
                'Order Status', 'Payment Status', 'Shipping Status', 'Order Date',
                'Ship Date', 'Delivery Date', 'Tracking Number', 'Carrier',
                'Supplier ID', 'Supplier Name', 'Cost Price', 'Profit Margin',
                'Customer Rating', 'Notes', 'Created', 'Updated'
            ],
            'listings': [
                'Listing ID', 'eBay Item ID', 'SKU', 'Title', 'Description',
                'Category', 'Condition', 'Price', 'Quantity', 'Status',
                'Views', 'Watchers', 'Sold Quantity', 'Revenue',
                'Performance Score', 'SEO Score', 'Keywords',
                'Primary Supplier', 'Backup Supplier', 'Cost Price', 'Profit Margin',
                'Stock Level', 'Last Updated', 'Created'
            ],
            'messages': [
                'Message ID', 'From', 'To', 'Subject', 'Message Content',
                'Message Type', 'Priority', 'Status', 'Order ID', 'Item ID',
                'Response Required', 'Response Date', 'Category',
                'Created', 'Updated'
            ],
            'draft_listings': [
                'Draft ID', 'Title', 'Description', 'Category', 'Price',
                'Quantity', 'Condition', 'Keywords', 'Product SKU',
                'Supplier ID', 'Cost Price', 'Target Margin', 'Status',
                'Optimization Score', 'Ready to Publish', 'Notes',
                'Created', 'Updated'
            ],
            'suppliers': [
                'Supplier ID', 'Name', 'Company Name', 'Contact Person',
                'Email', 'Phone', 'Address', 'Country', 'Website',
                'Business Type', 'Payment Terms', 'Minimum Order Value', 'Currency',
                'Discount Tier', 'Priority Level', 'Performance Rating',
                'Reliability Score', 'Total Orders', 'Successful Orders',
                'Average Delivery Days', 'Quality Rating', 'Cost Efficiency',
                'Status', 'Tags', 'Notes', 'Created', 'Updated'
            ],
            'products': [
                'Product ID', 'SKU', 'Name', 'Description', 'Category',
                'Cost Price', 'Selling Price', 'Profit Margin %', 'Stock Level',
                'Minimum Stock', 'Maximum Stock', 'Weight', 'Dimensions',
                'Primary Supplier ID', 'Primary Supplier Name', 'Backup Supplier ID',
                'Backup Supplier Name', 'Average Rating', 'Total Sales', 'Revenue',
                'Return Rate %', 'Performance Score', 'Status',
                'Created', 'Updated'
            ]
        }
        
        return headers_map.get(sheet_type, ['ID', 'Name', 'Status', 'Created', 'Updated'])
    
    # ===========================================
    # SUPPLIER DATA OPERATIONS
    # ===========================================
    
    def sync_suppliers_to_sheet(self, spreadsheet_id: str, suppliers: List[Supplier]) -> bool:
        """Sync supplier data to the Suppliers sheet"""
        if self.use_fallback:
            print(f"📝 Fallback: Would sync {len(suppliers)} suppliers to {spreadsheet_id}")
            return True
        
        if not self.service:
            return False
        
        try:
            # Prepare supplier data
            supplier_data = []
            for supplier in suppliers:
                row = [
                    supplier.id,
                    supplier.name,
                    supplier.company_name or '',
                    supplier.contact_person or '',
                    supplier.email or '',
                    supplier.phone or '',
                    supplier.address or '',
                    supplier.country or '',
                    supplier.website or '',
                    supplier.business_type or '',
                    supplier.payment_terms or '',
                    supplier.minimum_order_value or 0,
                    supplier.currency or 'USD',
                    supplier.discount_tier or '',
                    supplier.priority_level or 3,
                    supplier.performance_rating or 0.0,
                    supplier.reliability_score or 0,
                    supplier.total_orders or 0,
                    supplier.successful_orders or 0,
                    supplier.average_delivery_days or 15,
                    0.0,  # quality_rating placeholder
                    0.0,  # cost_efficiency placeholder
                    supplier.status or 'active',
                    supplier.tags or '',
                    supplier.notes or '',
                    supplier.created_at.isoformat() if supplier.created_at else '',
                    supplier.updated_at.isoformat() if supplier.updated_at else ''
                ]
                supplier_data.append(row)
            
            # Clear existing data (except headers)
            self._clear_sheet_data(spreadsheet_id, 'Suppliers')
            
            # Write new data
            if supplier_data:
                range_name = f"Suppliers!A2:Z{len(supplier_data) + 1}"
                body = {'values': supplier_data}
                
                self.service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()
            
            print(f"✅ Synced {len(suppliers)} suppliers to spreadsheet")
            return True
            
        except HttpError as error:
            print(f"Error syncing suppliers: {error}")
            return False
    
    def sync_products_to_sheet(self, spreadsheet_id: str, products: List[Product], suppliers_map: Dict[int, Supplier]) -> bool:
        """Sync product data to the Products sheet"""
        if self.use_fallback:
            print(f"📝 Fallback: Would sync {len(products)} products to {spreadsheet_id}")
            return True
        
        if not self.service:
            return False
        
        try:
            # Prepare product data
            product_data = []
            for product in products:
                # Get supplier names
                primary_supplier = suppliers_map.get(product.primary_supplier_id)
                backup_supplier = suppliers_map.get(product.backup_supplier_id)
                
                # Calculate profit margin
                profit_margin = 0.0
                if product.selling_price and product.cost_price:
                    profit_margin = ((product.selling_price - product.cost_price) / product.selling_price) * 100
                
                row = [
                    product.id,
                    product.sku,
                    product.name,
                    product.description or '',
                    product.category or '',
                    product.cost_price or 0.0,
                    product.selling_price or 0.0,
                    round(profit_margin, 2),
                    product.stock_level or 0,
                    product.minimum_stock or 0,
                    product.maximum_stock or 0,
                    product.weight or 0.0,
                    product.dimensions or '',
                    product.primary_supplier_id or '',
                    primary_supplier.name if primary_supplier else '',
                    product.backup_supplier_id or '',
                    backup_supplier.name if backup_supplier else '',
                    product.average_rating or 0.0,
                    product.total_sales or 0,
                    product.revenue or 0.0,
                    product.return_rate_percent or 0.0,
                    product.performance_score or 0.0,
                    product.status or 'active',
                    product.created_at.isoformat() if product.created_at else '',
                    product.updated_at.isoformat() if product.updated_at else ''
                ]
                product_data.append(row)
            
            # Clear existing data (except headers)
            self._clear_sheet_data(spreadsheet_id, 'Products')
            
            # Write new data
            if product_data:
                range_name = f"Products!A2:Y{len(product_data) + 1}"
                body = {'values': product_data}
                
                self.service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()
            
            print(f"✅ Synced {len(products)} products to spreadsheet")
            return True
            
        except HttpError as error:
            print(f"Error syncing products: {error}")
            return False
    
    def _clear_sheet_data(self, spreadsheet_id: str, sheet_name: str):
        """Clear all data from a sheet except headers (row 1)"""
        try:
            # Clear from row 2 onwards
            range_name = f"{sheet_name}!A2:Z1000"
            clear_request = {
                'ranges': [range_name]
            }
            
            self.service.spreadsheets().values().batchClear(
                spreadsheetId=spreadsheet_id,
                body=clear_request
            ).execute()
            
        except HttpError as error:
            print(f"Warning: Could not clear sheet {sheet_name}: {error}")
    
    # ===========================================
    # BACKUP SYSTEM OPERATIONS
    # ===========================================
    
    def create_backup_spreadsheet(self) -> Optional[str]:
        """Create comprehensive backup spreadsheet for all data"""
        if self.use_fallback:
            print("📝 Fallback: Would create backup spreadsheet")
            return "fallback_backup_spreadsheet"
        
        if not self.service:
            return None
        
        try:
            # Create backup spreadsheet
            spreadsheet_body = {
                'properties': {
                    'title': f'eBay Optimizer Backup - {datetime.now().strftime("%Y-%m-%d")}',
                    'locale': 'en_US',
                    'timeZone': 'America/New_York'
                }
            }
            
            spreadsheet = self.service.spreadsheets().create(body=spreadsheet_body).execute()
            spreadsheet_id = spreadsheet['spreadsheetId']
            
            # Create backup sheets
            self._create_backup_sheets(spreadsheet_id)
            
            print(f"✅ Created backup spreadsheet: {spreadsheet_id}")
            return spreadsheet_id
            
        except HttpError as error:
            print(f"Error creating backup spreadsheet: {error}")
            return None
    
    def _create_backup_sheets(self, spreadsheet_id: str) -> bool:
        """Create all backup sheets"""
        try:
            # Define backup sheets
            backup_sheets = [
                {'name': 'All_Orders', 'type': 'orders'},
                {'name': 'All_Listings', 'type': 'listings'},
                {'name': 'All_Suppliers', 'type': 'suppliers'},
                {'name': 'All_Products', 'type': 'products'},
                {'name': 'eBay_Accounts', 'type': 'accounts'},
                {'name': 'Performance_Summary', 'type': 'performance'},
                {'name': 'Backup_Info', 'type': 'backup_info'}
            ]
            
            # Delete default sheet
            self._delete_default_sheet(spreadsheet_id)
            
            # Create backup sheets
            requests = []
            for i, sheet_config in enumerate(backup_sheets):
                requests.append({
                    'addSheet': {
                        'properties': {
                            'title': sheet_config['name'],
                            'index': i,
                            'sheetType': 'GRID',
                            'gridProperties': {
                                'rowCount': 5000,  # Larger for backup
                                'columnCount': 30
                            }
                        }
                    }
                })
            
            # Execute batch request
            batch_request_body = {'requests': requests}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=batch_request_body
            ).execute()
            
            # Add headers
            for sheet_config in backup_sheets:
                self._add_sheet_headers(spreadsheet_id, sheet_config['name'], sheet_config['type'])
            
            # Add backup info
            self._add_backup_info(spreadsheet_id)
            
            print(f"✅ Created {len(backup_sheets)} backup sheets")
            return True
            
        except HttpError as error:
            print(f"Error creating backup sheets: {error}")
            return False
    
    def _add_backup_info(self, spreadsheet_id: str):
        """Add backup information to the Backup_Info sheet"""
        try:
            backup_info = [
                ['Backup Created', datetime.now().isoformat()],
                ['System', 'eBay Optimizer Enhanced'],
                ['Version', '2.0.0'],
                ['Type', 'Comprehensive Backup'],
                ['Includes', 'Orders, Listings, Suppliers, Products, Accounts'],
                ['Status', 'Active'],
                ['Contact', 'admin@ebayoptimizer.com']
            ]
            
            range_name = "Backup_Info!A1:B7"
            body = {'values': backup_info}
            
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
        except HttpError as error:
            print(f"Error adding backup info: {error}")
    
    # ===========================================
    # UTILITY METHODS
    # ===========================================
    
    def get_sheet_data(self, spreadsheet_id: str, sheet_name: str, range_limit: str = "Z1000") -> List[List[str]]:
        """Get all data from a specific sheet"""
        if self.use_fallback:
            return self.fallback_data.get(sheet_name.lower(), [])
        
        if not self.service:
            return []
        
        try:
            range_name = f"{sheet_name}!A1:{range_limit}"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            return result.get('values', [])
            
        except HttpError as error:
            print(f"Error getting sheet data: {error}")
            return []
    
    def batch_update_sheet(self, spreadsheet_id: str, updates: List[Dict[str, Any]]) -> bool:
        """Perform batch updates across multiple sheets"""
        if self.use_fallback:
            print(f"📝 Fallback: Would perform {len(updates)} batch updates")
            return True
        
        if not self.service or not updates:
            return False
        
        try:
            batch_request_body = {'requests': updates}
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=batch_request_body
            ).execute()
            
            print(f"✅ Performed {len(updates)} batch updates")
            return True
            
        except HttpError as error:
            print(f"Error in batch update: {error}")
            return False
    
    def share_spreadsheet(self, spreadsheet_id: str, email: str, role: str = 'reader') -> bool:
        """Share spreadsheet with specific user"""
        if self.use_fallback:
            print(f"📝 Fallback: Would share {spreadsheet_id} with {email}")
            return True
        
        try:
            drive_service = build('drive', 'v3', credentials=self.service._http.credentials)
            
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }
            
            drive_service.permissions().create(
                fileId=spreadsheet_id,
                body=permission
            ).execute()
            
            print(f"✅ Shared spreadsheet with {email} as {role}")
            return True
            
        except Exception as error:
            print(f"Error sharing spreadsheet: {error}")
            return False
    
    # ===========================================
    # BACKUP-SPECIFIC OPERATIONS
    # ===========================================
    
    def sync_suppliers_to_backup(self, backup_spreadsheet_id: str, suppliers: List[Supplier]) -> bool:
        """Sync suppliers to backup spreadsheet All_Suppliers sheet"""
        return self.sync_suppliers_to_sheet_by_name(backup_spreadsheet_id, "All_Suppliers", suppliers)
    
    def sync_products_to_backup(self, backup_spreadsheet_id: str, products: List[Product], suppliers_map: Dict[int, Supplier]) -> bool:
        """Sync products to backup spreadsheet All_Products sheet"""
        return self.sync_products_to_sheet_by_name(backup_spreadsheet_id, "All_Products", products, suppliers_map)
    
    def sync_orders_to_backup(self, backup_spreadsheet_id: str, orders: List) -> bool:
        """Sync orders to backup spreadsheet All_Orders sheet"""
        if self.use_fallback:
            print(f"📝 Fallback: Would sync {len(orders)} orders to backup")
            return True
        
        if not self.service:
            return False
        
        try:
            # Prepare order data
            order_data = []
            for order in orders:
                row = [
                    getattr(order, 'id', ''),
                    getattr(order, 'order_number', ''),
                    getattr(order, 'customer_name', ''),
                    getattr(order, 'customer_email', ''),
                    getattr(order, 'product_name', ''),
                    getattr(order, 'product_sku', ''),
                    getattr(order, 'quantity', 0),
                    getattr(order, 'unit_price', 0.0),
                    getattr(order, 'total_price', 0.0),
                    getattr(order, 'order_status', ''),
                    getattr(order, 'payment_status', ''),
                    getattr(order, 'shipping_status', ''),
                    getattr(order, 'order_date', ''),
                    getattr(order, 'ship_date', ''),
                    getattr(order, 'delivery_date', ''),
                    getattr(order, 'tracking_number', ''),
                    getattr(order, 'carrier', ''),
                    getattr(order, 'supplier_id', ''),
                    getattr(order, 'supplier_name', ''),
                    getattr(order, 'cost_price', 0.0),
                    getattr(order, 'profit_margin', 0.0),
                    getattr(order, 'customer_rating', 0),
                    getattr(order, 'notes', ''),
                    getattr(order, 'created_at', ''),
                    getattr(order, 'updated_at', '')
                ]
                order_data.append(row)
            
            # Clear and write data
            self._clear_sheet_data(backup_spreadsheet_id, "All_Orders")
            
            if order_data:
                range_name = f"All_Orders!A2:Y{len(order_data) + 1}"
                body = {'values': order_data}
                
                self.service.spreadsheets().values().update(
                    spreadsheetId=backup_spreadsheet_id,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()
            
            print(f"✅ Synced {len(orders)} orders to backup")
            return True
            
        except Exception as error:
            print(f"Error syncing orders to backup: {error}")
            return False
    
    def sync_listings_to_backup(self, backup_spreadsheet_id: str, listings: List) -> bool:
        """Sync listings to backup spreadsheet All_Listings sheet"""
        if self.use_fallback:
            print(f"📝 Fallback: Would sync {len(listings)} listings to backup")
            return True
        
        if not self.service:
            return False
        
        try:
            # Prepare listing data
            listing_data = []
            for listing in listings:
                row = [
                    getattr(listing, 'id', ''),
                    getattr(listing, 'ebay_item_id', ''),
                    getattr(listing, 'sku', ''),
                    getattr(listing, 'title', ''),
                    getattr(listing, 'description', ''),
                    getattr(listing, 'category', ''),
                    getattr(listing, 'condition', ''),
                    getattr(listing, 'price', 0.0),
                    getattr(listing, 'quantity', 0),
                    getattr(listing, 'status', ''),
                    getattr(listing, 'views', 0),
                    getattr(listing, 'watchers', 0),
                    getattr(listing, 'sold_quantity', 0),
                    getattr(listing, 'revenue', 0.0),
                    getattr(listing, 'performance_score', 0.0),
                    getattr(listing, 'seo_score', 0.0),
                    getattr(listing, 'keywords', ''),
                    getattr(listing, 'primary_supplier', ''),
                    getattr(listing, 'backup_supplier', ''),
                    getattr(listing, 'cost_price', 0.0),
                    getattr(listing, 'profit_margin', 0.0),
                    getattr(listing, 'stock_level', 0),
                    getattr(listing, 'updated_at', ''),
                    getattr(listing, 'created_at', '')
                ]
                listing_data.append(row)
            
            # Clear and write data
            self._clear_sheet_data(backup_spreadsheet_id, "All_Listings")
            
            if listing_data:
                range_name = f"All_Listings!A2:X{len(listing_data) + 1}"
                body = {'values': listing_data}
                
                self.service.spreadsheets().values().update(
                    spreadsheetId=backup_spreadsheet_id,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()
            
            print(f"✅ Synced {len(listings)} listings to backup")
            return True
            
        except Exception as error:
            print(f"Error syncing listings to backup: {error}")
            return False
    
    def sync_accounts_to_backup(self, backup_spreadsheet_id: str, accounts: List) -> bool:
        """Sync eBay accounts to backup spreadsheet eBay_Accounts sheet"""
        if self.use_fallback:
            print(f"📝 Fallback: Would sync {len(accounts)} accounts to backup")
            return True
        
        if not self.service:
            return False
        
        try:
            # Prepare account data
            account_data = []
            for account in accounts:
                row = [
                    getattr(account, 'id', ''),
                    getattr(account, 'email', ''),
                    getattr(account, 'store_name', ''),
                    getattr(account, 'account_type', ''),
                    getattr(account, 'status', ''),
                    getattr(account, 'health_score', 0),
                    getattr(account, 'usage_limit', 0),
                    getattr(account, 'current_listings', 0),
                    getattr(account, 'monthly_revenue', 0.0),
                    getattr(account, 'total_orders', 0),
                    getattr(account, 'success_rate', 0.0),
                    getattr(account, 'last_sync', ''),
                    getattr(account, 'created_at', ''),
                    getattr(account, 'updated_at', '')
                ]
                account_data.append(row)
            
            # Clear and write data
            self._clear_sheet_data(backup_spreadsheet_id, "eBay_Accounts")
            
            if account_data:
                range_name = f"eBay_Accounts!A2:N{len(account_data) + 1}"
                body = {'values': account_data}
                
                self.service.spreadsheets().values().update(
                    spreadsheetId=backup_spreadsheet_id,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()
            
            print(f"✅ Synced {len(accounts)} accounts to backup")
            return True
            
        except Exception as error:
            print(f"Error syncing accounts to backup: {error}")
            return False
    
    def sync_suppliers_to_sheet_by_name(self, spreadsheet_id: str, sheet_name: str, suppliers: List[Supplier]) -> bool:
        """Sync suppliers to a specific sheet by name"""
        if self.use_fallback:
            print(f"📝 Fallback: Would sync {len(suppliers)} suppliers to {sheet_name}")
            return True
        
        if not self.service:
            return False
        
        try:
            # Use the same logic as sync_suppliers_to_sheet but with custom sheet name
            supplier_data = []
            for supplier in suppliers:
                row = [
                    supplier.id,
                    supplier.name,
                    supplier.company_name or '',
                    supplier.contact_person or '',
                    supplier.email or '',
                    supplier.phone or '',
                    supplier.address or '',
                    supplier.country or '',
                    supplier.website or '',
                    supplier.business_type or '',
                    supplier.payment_terms or '',
                    supplier.minimum_order_value or 0,
                    supplier.currency or 'USD',
                    supplier.discount_tier or '',
                    supplier.priority_level or 3,
                    supplier.performance_rating or 0.0,
                    supplier.reliability_score or 0,
                    supplier.total_orders or 0,
                    supplier.successful_orders or 0,
                    supplier.average_delivery_days or 15,
                    0.0,  # quality_rating placeholder
                    0.0,  # cost_efficiency placeholder
                    supplier.status or 'active',
                    supplier.tags or '',
                    supplier.notes or '',
                    supplier.created_at.isoformat() if supplier.created_at else '',
                    supplier.updated_at.isoformat() if supplier.updated_at else ''
                ]
                supplier_data.append(row)
            
            # Clear existing data
            self._clear_sheet_data(spreadsheet_id, sheet_name)
            
            # Write new data
            if supplier_data:
                range_name = f"{sheet_name}!A2:Z{len(supplier_data) + 1}"
                body = {'values': supplier_data}
                
                self.service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()
            
            print(f"✅ Synced {len(suppliers)} suppliers to {sheet_name}")
            return True
            
        except Exception as error:
            print(f"Error syncing suppliers to {sheet_name}: {error}")
            return False
    
    def sync_products_to_sheet_by_name(self, spreadsheet_id: str, sheet_name: str, products: List[Product], suppliers_map: Dict[int, Supplier]) -> bool:
        """Sync products to a specific sheet by name"""
        if self.use_fallback:
            print(f"📝 Fallback: Would sync {len(products)} products to {sheet_name}")
            return True
        
        if not self.service:
            return False
        
        try:
            # Use the same logic as sync_products_to_sheet but with custom sheet name
            product_data = []
            for product in products:
                # Get supplier names
                primary_supplier = suppliers_map.get(product.primary_supplier_id)
                backup_supplier = suppliers_map.get(product.backup_supplier_id)
                
                # Calculate profit margin
                profit_margin = 0.0
                if product.selling_price and product.cost_price:
                    profit_margin = ((product.selling_price - product.cost_price) / product.selling_price) * 100
                
                row = [
                    product.id,
                    product.sku,
                    product.name,
                    product.description or '',
                    product.category or '',
                    product.cost_price or 0.0,
                    product.selling_price or 0.0,
                    round(profit_margin, 2),
                    product.stock_level or 0,
                    product.minimum_stock or 0,
                    product.maximum_stock or 0,
                    product.weight or 0.0,
                    product.dimensions or '',
                    product.primary_supplier_id or '',
                    primary_supplier.name if primary_supplier else '',
                    product.backup_supplier_id or '',
                    backup_supplier.name if backup_supplier else '',
                    product.average_rating or 0.0,
                    product.total_sales or 0,
                    product.revenue or 0.0,
                    product.return_rate_percent or 0.0,
                    product.performance_score or 0.0,
                    product.status or 'active',
                    product.created_at.isoformat() if product.created_at else '',
                    product.updated_at.isoformat() if product.updated_at else ''
                ]
                product_data.append(row)
            
            # Clear existing data
            self._clear_sheet_data(spreadsheet_id, sheet_name)
            
            # Write new data
            if product_data:
                range_name = f"{sheet_name}!A2:Y{len(product_data) + 1}"
                body = {'values': product_data}
                
                self.service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()
            
            print(f"✅ Synced {len(products)} products to {sheet_name}")
            return True
            
        except Exception as error:
            print(f"Error syncing products to {sheet_name}: {error}")
            return False
    
    def update_backup_completion_status(self, backup_spreadsheet_id: str):
        """Update backup completion status in Backup_Info sheet"""
        try:
            completion_info = [
                ['Backup Completed', datetime.now().isoformat()],
                ['Status', 'Completed Successfully'],
                ['Total Records', 'See individual sheets for counts']
            ]
            
            range_name = "Backup_Info!A8:B10"
            body = {'values': completion_info}
            
            self.service.spreadsheets().values().update(
                spreadsheetId=backup_spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
        except Exception as error:
            print(f"Error updating backup completion status: {error}")
    
    def log_backup_error(self, backup_spreadsheet_id: str, error_message: str):
        """Log backup error to Backup_Info sheet"""
        try:
            error_info = [
                ['Backup Error', datetime.now().isoformat()],
                ['Status', 'Failed'],
                ['Error Message', error_message]
            ]
            
            range_name = "Backup_Info!A8:B10"
            body = {'values': error_info}
            
            self.service.spreadsheets().values().update(
                spreadsheetId=backup_spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
        except Exception as error:
            print(f"Error logging backup error: {error}")