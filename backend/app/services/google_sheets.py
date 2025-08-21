import os
from typing import List, Dict, Optional, Any
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
from app.models.listing import Listing, ListingStatus


class GoogleSheetsService:
    def __init__(self):
        self.service = None
        self.spreadsheet_id = settings.SPREADSHEET_ID
        self.sheet_name = settings.SHEET_NAME
        self.use_fallback = False
        self.fallback_data = []
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Sheets API service or fallback mode"""
        # Check if we should use fallback mode
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
                print("✅ Google Sheets service initialized successfully")
            else:
                print(f"Warning: Google Sheets credentials file not found at {settings.GOOGLE_SHEETS_CREDENTIALS_PATH}")
                self._initialize_fallback_mode()
        except Exception as e:
            print(f"Error initializing Google Sheets service: {e}")
            self._initialize_fallback_mode()
    
    def _initialize_fallback_mode(self):
        """Initialize fallback mode with local data"""
        self.use_fallback = True
        fallback_path = os.getenv('FALLBACK_DATA_PATH', 'data/sample_listings.json')
        
        # Try multiple paths to find the data file
        possible_paths = [
            fallback_path,
            os.path.join(os.path.dirname(__file__), '..', '..', '..', fallback_path),
            os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'sample_listings.json'),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        self.fallback_data = json.load(f)
                    print(f"📦 Using fallback data from {path} ({len(self.fallback_data)} listings)")
                    return
                except Exception as e:
                    print(f"Error loading fallback data from {path}: {e}")
        
        # If no file found, use minimal sample data
        print("⚠️ Using minimal fallback data (no sample file found)")
        self.fallback_data = [
            {
                "id": "demo_001",
                "title": "Sample iPhone 15 Pro Max 256GB",
                "description": "This is a demo listing for testing",
                "category": "electronics",
                "price": 999.99,
                "quantity": 1,
                "keywords": ["demo", "sample", "test"],
                "status": "draft",
                "item_specifics": {"brand": "Apple", "condition": "New"},
                "sheet_row": 2,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
    
    def get_all_listings(self, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch all listings from Google Sheets or fallback data"""
        if self.use_fallback:
            return self.fallback_data.copy()
            
        if not self.service or not self.spreadsheet_id:
            return self.fallback_data.copy()
        
        # Use provided sheet name or default
        target_sheet = sheet_name or self.sheet_name
        
        try:
            range_name = f"{target_sheet}!A:T"  # Optimized to 20 columns
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return []
            
            # First row is headers
            headers = values[0]
            listings = []
            
            for row_index, row in enumerate(values[1:], start=2):
                listing_dict = {
                    'sheet_row': row_index
                }
                
                # Map columns to listing fields
                for i, header in enumerate(headers):
                    if i < len(row):
                        value = row[i]
                        
                        # Map header to field name (optimized mapping)
                        field_map = {
                            'Listing ID': 'id',
                            'eBay Item ID': 'item_id',
                            'SKU': 'sku',
                            'Current Title': 'title',
                            'Optimized Title': 'optimized_title',
                            'Description': 'description',
                            'Category': 'category',
                            'Price': 'price',
                            'Quantity': 'quantity',
                            'Condition': 'condition',
                            'Status': 'status',
                            'Keywords': 'keywords',
                            'Item Specifics': 'item_specifics',
                            'Views': 'views',
                            'Watchers': 'watchers',
                            'Sold': 'sold',
                            'Performance Score': 'performance_score',
                            'SEO Score': 'seo_score',
                            'Created': 'created_at',
                            'Last Updated': 'updated_at'
                        }
                        
                        field_name = field_map.get(header, header.lower().replace(' ', '_'))
                        
                        # Parse special fields
                        if field_name in ['price', 'performance_score', 'seo_score'] and value:
                            try:
                                listing_dict[field_name] = float(value.replace('$', '').replace(',', ''))
                            except:
                                listing_dict[field_name] = 0.0
                        elif field_name in ['quantity', 'views', 'watchers', 'sold'] and value:
                            try:
                                listing_dict[field_name] = int(value)
                            except:
                                listing_dict[field_name] = 0
                        elif field_name == 'keywords' and value:
                            listing_dict[field_name] = [k.strip() for k in value.split(',')]
                        elif field_name == 'item_specifics' and value:
                            try:
                                listing_dict[field_name] = json.loads(value)
                            except:
                                listing_dict[field_name] = {}
                        elif field_name == 'status' and value:
                            listing_dict[field_name] = value.lower()
                        else:
                            listing_dict[field_name] = value
                
                # Set defaults for missing fields
                if 'id' not in listing_dict:
                    listing_dict['id'] = f"listing_{row_index}"
                if 'status' not in listing_dict:
                    listing_dict['status'] = ListingStatus.DRAFT
                if 'created_at' not in listing_dict:
                    listing_dict['created_at'] = datetime.now().isoformat()
                if 'updated_at' not in listing_dict:
                    listing_dict['updated_at'] = datetime.now().isoformat()
                    
                listings.append(listing_dict)
            
            return listings
            
        except HttpError as error:
            print(f"An error occurred fetching listings: {error}")
            return []
    
    def update_listing(self, row: int, listing_data: Dict[str, Any]) -> bool:
        """Update a specific listing in Google Sheets or fallback data"""
        if self.use_fallback:
            # Update in fallback data
            for i, listing in enumerate(self.fallback_data):
                if listing.get('sheet_row') == row or listing.get('id') == listing_data.get('id'):
                    self.fallback_data[i] = listing_data
                    return True
            return False
            
        if not self.service or not self.spreadsheet_id:
            return False
        
        try:
            # Prepare values for update
            values = [[
                listing_data.get('id', ''),
                listing_data.get('title', ''),
                listing_data.get('description', ''),
                listing_data.get('category', ''),
                str(listing_data.get('price', '')),
                str(listing_data.get('quantity', '')),
                ','.join(listing_data.get('keywords', [])) if listing_data.get('keywords') else '',
                listing_data.get('status', ListingStatus.DRAFT),
                json.dumps(listing_data.get('item_specifics', {})) if listing_data.get('item_specifics') else '{}',
                datetime.now().isoformat()
            ]]
            
            range_name = f"{self.sheet_name}!A{row}:J{row}"
            
            body = {
                'values': values
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            return True
            
        except HttpError as error:
            print(f"An error occurred updating listing: {error}")
            return False
    
    def add_listing(self, listing_data: Dict[str, Any]) -> bool:
        """Add a new listing to Google Sheets or fallback data"""
        if self.use_fallback:
            # Add to fallback data
            listing_data['sheet_row'] = len(self.fallback_data) + 2  # +2 because row 1 is headers
            self.fallback_data.append(listing_data)
            return True
            
        if not self.service or not self.spreadsheet_id:
            return False
        
        try:
            # Prepare values for append
            values = [[
                listing_data.get('id', f"listing_{datetime.now().timestamp()}"),
                listing_data.get('title', ''),
                listing_data.get('description', ''),
                listing_data.get('category', ''),
                str(listing_data.get('price', '')),
                str(listing_data.get('quantity', '')),
                ','.join(listing_data.get('keywords', [])) if listing_data.get('keywords') else '',
                listing_data.get('status', ListingStatus.DRAFT),
                json.dumps(listing_data.get('item_specifics', {})) if listing_data.get('item_specifics') else '{}',
                datetime.now().isoformat()
            ]]
            
            body = {
                'values': values
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A:J",
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            return True
            
        except HttpError as error:
            print(f"An error occurred adding listing: {error}")
            return False
    
    def batch_update_listings(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Batch update multiple listings"""
        if self.use_fallback:
            # Update in fallback data
            success_count = 0
            for update in updates:
                row = update.get('sheet_row')
                if row:
                    for i, listing in enumerate(self.fallback_data):
                        if listing.get('sheet_row') == row:
                            self.fallback_data[i].update(update)
                            success_count += 1
                            break
            return {'success': success_count, 'failed': len(updates) - success_count}
            
        if not self.service or not self.spreadsheet_id:
            return {'success': 0, 'failed': len(updates)}
        
        success_count = 0
        failed_count = 0
        
        try:
            # Prepare batch update data
            data = []
            for update in updates:
                row = update.get('sheet_row')
                if row:
                    values = [[
                        update.get('id', ''),
                        update.get('title', ''),
                        update.get('description', ''),
                        update.get('category', ''),
                        str(update.get('price', '')),
                        str(update.get('quantity', '')),
                        ','.join(update.get('keywords', [])) if update.get('keywords') else '',
                        update.get('status', ListingStatus.OPTIMIZED),
                        json.dumps(update.get('item_specifics', {})) if update.get('item_specifics') else '{}',
                        datetime.now().isoformat()
                    ]]
                    
                    data.append({
                        'range': f"{self.sheet_name}!A{row}:J{row}",
                        'values': values
                    })
            
            if data:
                body = {
                    'valueInputOption': 'USER_ENTERED',
                    'data': data
                }
                
                result = self.service.spreadsheets().values().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=body
                ).execute()
                
                success_count = len(data)
            
        except HttpError as error:
            print(f"An error occurred in batch update: {error}")
            failed_count = len(updates)
        
        return {
            'success': success_count,
            'failed': failed_count
        }
    
    def create_sheet_if_not_exists(self, sheet_name: Optional[str] = None, sheet_type: str = "listings") -> bool:
        """Create the sheet with headers if it doesn't exist"""
        if not self.service or not self.spreadsheet_id:
            return False
        
        target_sheet = sheet_name or self.sheet_name
        
        try:
            # Check if sheet exists
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheet_exists = any(
                sheet['properties']['title'] == target_sheet 
                for sheet in spreadsheet.get('sheets', [])
            )
            
            if not sheet_exists:
                # Create new sheet
                request_body = {
                    'requests': [{
                        'addSheet': {
                            'properties': {
                                'title': target_sheet
                            }
                        }
                    }]
                }
                
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=request_body
                ).execute()
                
                print(f"✅ Created new sheet: {target_sheet}")
            
            # Get appropriate headers based on sheet type
            headers = self._get_sheet_headers(sheet_type)
            
            # Add headers
            body = {
                'values': [headers]
            }
            
            # Determine range based on header count
            last_column = chr(ord('A') + len(headers) - 1)
            range_name = f"{target_sheet}!A1:{last_column}1"
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            print(f"✅ Headers added to {target_sheet}: {len(headers)} columns")
            return True
            
        except HttpError as error:
            print(f"An error occurred creating sheet {target_sheet}: {error}")
            return False
    
    def _get_sheet_headers(self, sheet_type: str) -> List[str]:
        """Get appropriate headers for different sheet types"""
        if sheet_type == "listings":
            return [
                'Listing ID', 'eBay Item ID', 'SKU', 'Current Title', 'Optimized Title', 
                'Description', 'Category', 'Price', 'Quantity', 'Condition', 'Status', 
                'Keywords', 'Item Specifics', 'Views', 'Watchers', 'Sold', 
                'Performance Score', 'SEO Score', 'Created', 'Last Updated'
            ]
        elif sheet_type == "orders":
            return [
                "Order ID", "Order Number", "Customer Name", "Customer Email", 
                "Product Name", "Price", "Status", "Order Date", 
                "Tracking Number", "Carrier", "Alerts", "Created"
            ]
        elif sheet_type == "sources":
            return [
                "Source ID", "Name", "URL", "Status", 
                "Products Count", "Last Sync", "Created"
            ]
        elif sheet_type == "accounts":
            return [
                "Account ID", "Name", "Type", "Store Name", "Status", 
                "Health Score", "Usage Limit", "Current Listings", "Revenue", "Last Activity"
            ]
        else:
            # Default to listings headers
            return [
                'ID', 'Title', 'Description', 'Category', 'Price', 
                'Quantity', 'Keywords', 'Status', 'Item Specifics', 'Last Updated'
            ]
    
    def create_all_required_sheets(self) -> Dict[str, bool]:
        """Create all required sheets for the application"""
        if not self.service or not self.spreadsheet_id:
            return {"error": "No Google Sheets service available"}
        
        results = {}
        
        # Create Listings sheet (if not exists)
        listings_sheet = getattr(settings, 'SHEET_NAME', 'Listings')
        results['listings'] = self.create_sheet_if_not_exists(listings_sheet, "listings")
        
        # Create Orders sheet
        orders_sheet = getattr(settings, 'ORDERS_SHEET_NAME', 'Orders')
        results['orders'] = self.create_sheet_if_not_exists(orders_sheet, "orders")
        
        # Create Sources sheet
        sources_sheet = getattr(settings, 'SOURCES_SHEET_NAME', 'Sources') 
        results['sources'] = self.create_sheet_if_not_exists(sources_sheet, "sources")
        
        return results
    
    def get_all_orders(self, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch all orders from Google Sheets"""
        target_sheet = sheet_name or getattr(settings, 'ORDERS_SHEET_NAME', 'Orders')
        
        if self.use_fallback:
            # Return mock orders data
            return [
                {
                    "id": "order_001",
                    "customer_name": "John Doe",
                    "product_name": "Sample Product",
                    "amount": 99.99,
                    "status": "completed",
                    "order_date": datetime.now().isoformat(),
                    "sheet_row": 2
                }
            ]
            
        if not self.service or not self.spreadsheet_id:
            return []
        
        try:
            range_name = f"{target_sheet}!A:K"  # Orders may have more columns
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return []
            
            # Parse orders data similar to listings
            headers = values[0]
            orders = []
            
            for row_index, row in enumerate(values[1:], start=2):
                order_dict = {'sheet_row': row_index}
                
                for i, header in enumerate(headers):
                    if i < len(row):
                        value = row[i]
                        field_map = {
                            'ID': 'id',
                            'Customer Name': 'customer_name',
                            'Product Name': 'product_name',
                            'Amount': 'amount',
                            'Status': 'status',
                            'Order Date': 'order_date'
                        }
                        
                        field_name = field_map.get(header, header.lower().replace(' ', '_'))
                        
                        if field_name == 'amount' and value:
                            try:
                                order_dict[field_name] = float(value.replace('$', '').replace(',', ''))
                            except:
                                order_dict[field_name] = 0.0
                        else:
                            order_dict[field_name] = value
                
                if 'id' not in order_dict:
                    order_dict['id'] = f"order_{row_index}"
                    
                orders.append(order_dict)
            
            return orders
            
        except HttpError as error:
            print(f"An error occurred fetching orders: {error}")
            return []
    
    def get_all_sources(self, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch all sources from Google Sheets"""
        target_sheet = sheet_name or getattr(settings, 'SOURCES_SHEET_NAME', 'Sources')
        
        if self.use_fallback:
            # Return mock sources data
            return [
                {
                    "id": "source_001",
                    "name": "Amazon US",
                    "url": "https://amazon.com",
                    "status": "active",
                    "products_count": 150,
                    "last_sync": datetime.now().isoformat(),
                    "sheet_row": 2
                }
            ]
            
        if not self.service or not self.spreadsheet_id:
            return []
        
        try:
            range_name = f"{target_sheet}!A:H"  # Sources have different column structure
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return []
            
            # Parse sources data
            headers = values[0]
            sources = []
            
            for row_index, row in enumerate(values[1:], start=2):
                source_dict = {'sheet_row': row_index}
                
                for i, header in enumerate(headers):
                    if i < len(row):
                        value = row[i]
                        field_map = {
                            'Source ID': 'id',
                            'Name': 'name',
                            'URL': 'website_url',
                            'Status': 'status',
                            'Products Count': 'total_products',
                            'Last Sync': 'last_sync'
                        }
                        
                        field_name = field_map.get(header, header.lower().replace(' ', '_'))
                        
                        if field_name == 'total_products' and value:
                            try:
                                source_dict[field_name] = int(value)
                            except:
                                source_dict[field_name] = 0
                        else:
                            source_dict[field_name] = value
                
                if 'id' not in source_dict:
                    source_dict['id'] = f"source_{row_index}"
                    
                sources.append(source_dict)
            
            return sources
            
        except HttpError as error:
            print(f"An error occurred fetching sources: {error}")
            return []