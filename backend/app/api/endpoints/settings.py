from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import os
from pydantic import BaseModel

from app.core.config import settings
from app.services.google_sheets import GoogleSheetsService

router = APIRouter()


class GoogleSheetsConfig(BaseModel):
    spreadsheet_id: str
    listings_sheet_name: str = "Listings"
    orders_sheet_name: str = "Orders"
    sources_sheet_name: str = "Sources"


class SettingsResponse(BaseModel):
    google_sheets: Dict[str, Any]
    project_info: Dict[str, Any]


@router.get("/", response_model=SettingsResponse)
async def get_settings():
    """Get current system settings"""
    try:
        return {
            "google_sheets": {
                "spreadsheet_id": settings.SPREADSHEET_ID or "",
                "listings_sheet_name": settings.SHEET_NAME,
                "orders_sheet_name": getattr(settings, 'ORDERS_SHEET_NAME', 'Orders'),
                "sources_sheet_name": getattr(settings, 'SOURCES_SHEET_NAME', 'Sources'),
                "credentials_path": settings.GOOGLE_SHEETS_CREDENTIALS_PATH,
                "connection_status": _check_google_sheets_connection()
            },
            "project_info": {
                "name": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "environment": os.getenv("ENVIRONMENT", "development")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting settings: {str(e)}")


@router.put("/google-sheets")
async def update_google_sheets_settings(config: GoogleSheetsConfig):
    """Update Google Sheets configuration"""
    try:
        # Update environment variables (runtime)
        os.environ["SPREADSHEET_ID"] = config.spreadsheet_id
        os.environ["SHEET_NAME"] = config.listings_sheet_name
        os.environ["ORDERS_SHEET_NAME"] = config.orders_sheet_name  
        os.environ["SOURCES_SHEET_NAME"] = config.sources_sheet_name
        
        # Update settings object
        settings.SPREADSHEET_ID = config.spreadsheet_id
        settings.SHEET_NAME = config.listings_sheet_name
        settings.ORDERS_SHEET_NAME = config.orders_sheet_name
        settings.SOURCES_SHEET_NAME = config.sources_sheet_name
        
        # Reinitialize Google Sheets service with new config
        from app.services.sync_service import sync_service
        sync_service.sheets_service.spreadsheet_id = config.spreadsheet_id
        sync_service.sheets_service.sheet_name = config.listings_sheet_name
        
        # Test connection with new settings
        connection_status = _test_google_sheets_connection(config.spreadsheet_id)
        
        return {
            "message": "Google Sheets settings updated successfully. Sync service will use new configuration.",
            "connection_status": connection_status,
            "config": {
                "spreadsheet_id": config.spreadsheet_id,
                "listings_sheet_name": config.listings_sheet_name,
                "orders_sheet_name": config.orders_sheet_name,
                "sources_sheet_name": config.sources_sheet_name
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating Google Sheets settings: {str(e)}")


@router.post("/google-sheets/test-connection")
async def test_google_sheets_connection(config: GoogleSheetsConfig):
    """Test Google Sheets connection with provided configuration"""
    try:
        connection_status = _test_google_sheets_connection(config.spreadsheet_id)
        
        return {
            "connection_status": connection_status,
            "message": "Connection test completed",
            "spreadsheet_id": config.spreadsheet_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing connection: {str(e)}")


@router.get("/google-sheets/status")
async def get_google_sheets_status():
    """Get current Google Sheets connection status"""
    try:
        status = _check_google_sheets_connection()
        return {
            "connection_status": status,
            "spreadsheet_id": settings.SPREADSHEET_ID,
            "credentials_available": os.path.exists(settings.GOOGLE_SHEETS_CREDENTIALS_PATH)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking Google Sheets status: {str(e)}")


def _check_google_sheets_connection() -> str:
    """Check current Google Sheets connection status"""
    try:
        print(f"Checking Google Sheets connection...")
        print(f"SPREADSHEET_ID: {settings.SPREADSHEET_ID}")
        
        if not settings.SPREADSHEET_ID:
            print("No spreadsheet ID configured")
            return "disconnected"
        
        if not os.path.exists(settings.GOOGLE_SHEETS_CREDENTIALS_PATH):
            print(f"Credentials file not found: {settings.GOOGLE_SHEETS_CREDENTIALS_PATH}")
            return "error"
        
        print("Creating Google Sheets service...")
        # Create a test service to check connection
        sheets_service = GoogleSheetsService()
        if sheets_service.use_fallback:
            print("Service is in fallback mode")
            return "error"
        
        if sheets_service.service is None:
            print("Service is None")
            return "error"
            
        print("Testing spreadsheet access...")
        # Try to access the spreadsheet
        test_range = f"{settings.SHEET_NAME}!A1:A1"
        result = sheets_service.service.spreadsheets().values().get(
            spreadsheetId=settings.SPREADSHEET_ID,
            range=test_range
        ).execute()
        
        print("Connection test successful")
        return "connected"
    except Exception as e:
        print(f"Google Sheets connection check error: {e}")
        return "error"


def _test_google_sheets_connection(spreadsheet_id: str) -> str:
    """Test Google Sheets connection with specific spreadsheet ID"""
    try:
        if not spreadsheet_id:
            return "error"
        
        if not os.path.exists(settings.GOOGLE_SHEETS_CREDENTIALS_PATH):
            return "error"
        
        # Create a test service
        sheets_service = GoogleSheetsService()
        if sheets_service.use_fallback or sheets_service.service is None:
            return "error"
        
        # Try to access the specific spreadsheet
        test_range = "A1:A1"  # Simple range to test access
        result = sheets_service.service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=test_range
        ).execute()
        
        return "connected"
    except Exception as e:
        print(f"Google Sheets connection test error: {e}")
        return "error"