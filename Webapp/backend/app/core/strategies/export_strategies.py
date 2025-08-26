"""
Export Strategy Pattern Implementation
Open/Closed Principle: New export formats can be added without modifying existing code
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import csv
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import io


class ExportFormat(str, Enum):
    """Supported export formats"""
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    XLSX = "xlsx"
    GOOGLE_SHEETS = "google_sheets"
    EBAY_BULK = "ebay_bulk"


class IExportStrategy(ABC):
    """
    Strategy interface for data export
    Following OCP: New export formats can be added without modifying existing code
    """
    
    @abstractmethod
    def export_data(self, data: List[Dict[str, Any]], filename: str = None) -> Union[str, bytes]:
        """Export data in specific format"""
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """Get appropriate file extension"""
        pass
    
    @abstractmethod
    def get_content_type(self) -> str:
        """Get MIME content type"""
        pass
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return format name"""
        pass
    
    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Whether format supports streaming for large datasets"""
        pass


class CSVExportStrategy(IExportStrategy):
    """CSV export strategy with customizable formatting"""
    
    def __init__(self, delimiter: str = ",", include_headers: bool = True):
        self.delimiter = delimiter
        self.include_headers = include_headers
    
    def export_data(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """Export data as CSV"""
        if not data:
            return ""
        
        output = io.StringIO()
        fieldnames = data[0].keys()
        
        writer = csv.DictWriter(
            output, 
            fieldnames=fieldnames, 
            delimiter=self.delimiter,
            quoting=csv.QUOTE_MINIMAL
        )
        
        if self.include_headers:
            writer.writeheader()
        
        for row in data:
            # Clean data for CSV export
            cleaned_row = self._clean_row_for_csv(row)
            writer.writerow(cleaned_row)
        
        return output.getvalue()
    
    def get_file_extension(self) -> str:
        return "csv"
    
    def get_content_type(self) -> str:
        return "text/csv"
    
    @property
    def format_name(self) -> str:
        return "CSV (Comma-Separated Values)"
    
    @property
    def supports_streaming(self) -> bool:
        return True
    
    def _clean_row_for_csv(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Clean row data for CSV export"""
        cleaned = {}
        for key, value in row.items():
            if isinstance(value, (list, dict)):
                # Convert complex types to JSON string
                cleaned[key] = json.dumps(value)
            elif value is None:
                cleaned[key] = ""
            elif isinstance(value, datetime):
                cleaned[key] = value.isoformat()
            else:
                cleaned[key] = str(value)
        return cleaned


class JSONExportStrategy(IExportStrategy):
    """JSON export strategy with formatting options"""
    
    def __init__(self, indent: int = 2, ensure_ascii: bool = False):
        self.indent = indent
        self.ensure_ascii = ensure_ascii
    
    def export_data(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """Export data as JSON"""
        # Create export metadata
        export_data = {
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "total_records": len(data),
                "format": "json",
                "version": "1.0"
            },
            "data": self._clean_data_for_json(data)
        }
        
        return json.dumps(
            export_data,
            indent=self.indent,
            ensure_ascii=self.ensure_ascii,
            default=self._json_serializer
        )
    
    def get_file_extension(self) -> str:
        return "json"
    
    def get_content_type(self) -> str:
        return "application/json"
    
    @property
    def format_name(self) -> str:
        return "JSON (JavaScript Object Notation)"
    
    @property
    def supports_streaming(self) -> bool:
        return False  # JSON typically loaded entirely into memory
    
    def _clean_data_for_json(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean data for JSON export"""
        cleaned_data = []
        for row in data:
            cleaned_row = {}
            for key, value in row.items():
                if isinstance(value, datetime):
                    cleaned_row[key] = value.isoformat()
                else:
                    cleaned_row[key] = value
            cleaned_data.append(cleaned_row)
        return cleaned_data
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for complex objects"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class XMLExportStrategy(IExportStrategy):
    """XML export strategy with customizable structure"""
    
    def __init__(self, root_element: str = "data", item_element: str = "item"):
        self.root_element = root_element
        self.item_element = item_element
    
    def export_data(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """Export data as XML"""
        root = ET.Element(self.root_element)
        
        # Add metadata
        metadata = ET.SubElement(root, "metadata")
        ET.SubElement(metadata, "exported_at").text = datetime.now().isoformat()
        ET.SubElement(metadata, "total_records").text = str(len(data))
        ET.SubElement(metadata, "format").text = "xml"
        
        # Add data
        data_element = ET.SubElement(root, "items")
        
        for row in data:
            item = ET.SubElement(data_element, self.item_element)
            self._add_dict_to_element(item, row)
        
        # Format XML with indentation
        self._indent_xml(root)
        
        return ET.tostring(root, encoding='unicode', xml_declaration=True)
    
    def get_file_extension(self) -> str:
        return "xml"
    
    def get_content_type(self) -> str:
        return "application/xml"
    
    @property
    def format_name(self) -> str:
        return "XML (eXtensible Markup Language)"
    
    @property
    def supports_streaming(self) -> bool:
        return True
    
    def _add_dict_to_element(self, parent: ET.Element, data: Dict[str, Any]):
        """Add dictionary data to XML element"""
        for key, value in data.items():
            # Clean key name for XML
            clean_key = self._clean_xml_key(key)
            
            if isinstance(value, dict):
                sub_element = ET.SubElement(parent, clean_key)
                self._add_dict_to_element(sub_element, value)
            elif isinstance(value, list):
                list_element = ET.SubElement(parent, clean_key)
                for item in value:
                    if isinstance(item, dict):
                        item_element = ET.SubElement(list_element, "item")
                        self._add_dict_to_element(item_element, item)
                    else:
                        item_element = ET.SubElement(list_element, "item")
                        item_element.text = str(item) if item is not None else ""
            else:
                element = ET.SubElement(parent, clean_key)
                if isinstance(value, datetime):
                    element.text = value.isoformat()
                else:
                    element.text = str(value) if value is not None else ""
    
    def _clean_xml_key(self, key: str) -> str:
        """Clean key name for XML element"""
        # Replace invalid XML characters
        import re
        clean_key = re.sub(r'[^\w\-_.]', '_', key)
        
        # Ensure it starts with a letter or underscore
        if clean_key and clean_key[0].isdigit():
            clean_key = f"item_{clean_key}"
        
        return clean_key or "unknown"
    
    def _indent_xml(self, elem: ET.Element, level: int = 0):
        """Add indentation to XML for readability"""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self._indent_xml(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i


class EbayBulkExportStrategy(IExportStrategy):
    """eBay-specific bulk export format"""
    
    def __init__(self):
        # eBay bulk upload required fields
        self.required_fields = [
            "Action(SiteID=US|Country=US|Currency=USD|Version=1197)",
            "Category",
            "StoreCategory",
            "Title",
            "Subtitle",
            "Description",
            "PicURL",
            "Quantity",
            "StartPrice",
            "BuyItNowPrice",
            "ListingDuration",
            "ListingType",
            "PaymentMethods",
            "PayPalEmailAddress",
            "Location",
            "Country",
            "ConditionID"
        ]
    
    def export_data(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """Export data in eBay bulk upload format"""
        if not data:
            return ""
        
        output = io.StringIO()
        
        # eBay uses tab-delimited format
        writer = csv.DictWriter(
            output,
            fieldnames=self.required_fields,
            delimiter='\t',
            quoting=csv.QUOTE_MINIMAL
        )
        
        writer.writeheader()
        
        for row in data:
            ebay_row = self._convert_to_ebay_format(row)
            writer.writerow(ebay_row)
        
        return output.getvalue()
    
    def get_file_extension(self) -> str:
        return "txt"  # eBay uses .txt for bulk uploads
    
    def get_content_type(self) -> str:
        return "text/plain"
    
    @property
    def format_name(self) -> str:
        return "eBay Bulk Upload Format"
    
    @property
    def supports_streaming(self) -> bool:
        return True
    
    def _convert_to_ebay_format(self, listing: Dict[str, Any]) -> Dict[str, str]:
        """Convert listing data to eBay bulk format"""
        
        # Map internal fields to eBay fields
        ebay_row = {}
        
        # Set default eBay action
        ebay_row["Action(SiteID=US|Country=US|Currency=USD|Version=1197)"] = "Add"
        
        # Map basic fields
        ebay_row["Title"] = listing.get("title", "")[:80]  # eBay title limit
        ebay_row["Description"] = self._format_ebay_description(listing.get("description", ""))
        ebay_row["Category"] = self._map_category_to_ebay(listing.get("category", ""))
        ebay_row["Quantity"] = str(listing.get("quantity", 1))
        ebay_row["StartPrice"] = str(listing.get("price", 0.99))
        
        # Set eBay-specific defaults
        ebay_row["ListingType"] = "FixedPriceItem"
        ebay_row["ListingDuration"] = "GTC"  # Good Till Cancelled
        ebay_row["PaymentMethods"] = "PayPal"
        ebay_row["PayPalEmailAddress"] = "seller@example.com"  # Should be configurable
        ebay_row["Location"] = "United States"
        ebay_row["Country"] = "US"
        ebay_row["ConditionID"] = self._map_condition_to_ebay(listing.get("condition", "new"))
        
        # Fill remaining required fields with defaults
        for field in self.required_fields:
            if field not in ebay_row:
                ebay_row[field] = ""
        
        return ebay_row
    
    def _format_ebay_description(self, description: str) -> str:
        """Format description for eBay"""
        if not description:
            return "High quality product with excellent features."
        
        # eBay allows HTML in descriptions
        # Convert markdown-style formatting to basic HTML
        formatted = description.replace("✨", "").replace("📋", "").replace("📝", "")
        formatted = formatted.replace("•", "<li>").replace("\n\n", "<br><br>")
        
        # Wrap in basic HTML structure
        return f"<div>{formatted}</div>"
    
    def _map_category_to_ebay(self, category: str) -> str:
        """Map internal category to eBay category ID"""
        # This would typically map to actual eBay category IDs
        category_map = {
            "electronics": "293",  # Consumer Electronics
            "clothing": "11450",   # Clothing, Shoes & Accessories  
            "home": "11700",       # Home & Garden
            "automotive": "6000",  # eBay Motors
            "collectibles": "1"    # Collectibles
        }
        return category_map.get(category.lower(), "99")  # 99 = Other
    
    def _map_condition_to_ebay(self, condition: str) -> str:
        """Map condition to eBay condition ID"""
        condition_map = {
            "new": "1000",        # New
            "used": "3000",       # Used
            "refurbished": "2000" # Refurbished
        }
        return condition_map.get(condition.lower(), "1000")


class ExportContext:
    """
    Context class for export strategy pattern
    Following OCP: Easy to add new export formats without modifying existing code
    """
    
    def __init__(self, strategy: IExportStrategy = None):
        self._strategy = strategy or CSVExportStrategy()
        self._available_strategies = {
            ExportFormat.CSV: CSVExportStrategy,
            ExportFormat.JSON: JSONExportStrategy,
            ExportFormat.XML: XMLExportStrategy,
            ExportFormat.EBAY_BULK: EbayBulkExportStrategy,
            # Future export formats can be added here
        }
    
    def set_strategy(self, format_type: ExportFormat, **kwargs):
        """Change export strategy at runtime"""
        if format_type in self._available_strategies:
            self._strategy = self._available_strategies[format_type](**kwargs)
        else:
            raise ValueError(f"Export format {format_type} not supported")
    
    def export_data(self, data: List[Dict[str, Any]], filename: str = None) -> Dict[str, Any]:
        """Export data using current strategy"""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.{self._strategy.get_file_extension()}"
        
        exported_content = self._strategy.export_data(data, filename)
        
        return {
            "content": exported_content,
            "filename": filename,
            "content_type": self._strategy.get_content_type(),
            "format_name": self._strategy.format_name,
            "record_count": len(data),
            "supports_streaming": self._strategy.supports_streaming
        }
    
    def get_available_formats(self) -> List[Dict[str, str]]:
        """Get list of available export formats"""
        formats = []
        for format_type, strategy_class in self._available_strategies.items():
            strategy_instance = strategy_class()
            formats.append({
                "format": format_type.value,
                "name": strategy_instance.format_name,
                "extension": strategy_instance.get_file_extension(),
                "content_type": strategy_instance.get_content_type(),
                "supports_streaming": strategy_instance.supports_streaming
            })
        return formats
    
    def validate_data_for_export(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate data before export"""
        if not data:
            return {"valid": False, "error": "No data to export"}
        
        if not isinstance(data, list):
            return {"valid": False, "error": "Data must be a list of dictionaries"}
        
        if not all(isinstance(item, dict) for item in data):
            return {"valid": False, "error": "All data items must be dictionaries"}
        
        # Check for consistent structure
        if len(data) > 1:
            first_keys = set(data[0].keys())
            inconsistent_items = []
            
            for i, item in enumerate(data[1:], 1):
                if set(item.keys()) != first_keys:
                    inconsistent_items.append(i)
            
            if inconsistent_items:
                return {
                    "valid": True,
                    "warning": f"Inconsistent structure detected in items: {inconsistent_items[:5]}",
                    "all_keys": list(set().union(*(item.keys() for item in data)))
                }
        
        return {
            "valid": True,
            "record_count": len(data),
            "fields": list(data[0].keys()) if data else [],
            "estimated_size": self._estimate_export_size(data)
        }
    
    def _estimate_export_size(self, data: List[Dict[str, Any]]) -> str:
        """Estimate export file size"""
        if not data:
            return "0 B"
        
        # Rough estimation based on JSON serialization
        sample_size = len(json.dumps(data[0]))
        total_estimated = sample_size * len(data)
        
        # Add format overhead estimates
        format_multipliers = {
            ExportFormat.CSV: 0.8,
            ExportFormat.JSON: 1.2,
            ExportFormat.XML: 2.5,
            ExportFormat.EBAY_BULK: 0.9
        }
        
        # Get current format type
        current_format = None
        for fmt, strategy_class in self._available_strategies.items():
            if isinstance(self._strategy, strategy_class):
                current_format = fmt
                break
        
        if current_format and current_format in format_multipliers:
            total_estimated *= format_multipliers[current_format]
        
        # Convert to human readable
        if total_estimated < 1024:
            return f"{total_estimated:.0f} B"
        elif total_estimated < 1024 * 1024:
            return f"{total_estimated/1024:.1f} KB"
        elif total_estimated < 1024 * 1024 * 1024:
            return f"{total_estimated/(1024*1024):.1f} MB"
        else:
            return f"{total_estimated/(1024*1024*1024):.1f} GB"