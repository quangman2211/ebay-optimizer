"""
Service Configuration for Dependency Injection
Configures all service dependencies following DIP
"""

from app.core.container import ServiceRegistry
from app.core.interfaces.services import (
    IDataConnectionService, ISheetsDataService, IListingDataService,
    IOrderDataService, IAccountDataService, ISourceDataService,
    IAuthenticationService, IOptimizationService, IAnalyticsService,
    INotificationService, IExportService
)

# Strategy interfaces
from app.core.strategies.optimization_strategies import (
    IOptimizationStrategy, OptimizationType, OptimizationContext
)
from app.core.strategies.export_strategies import (
    IExportStrategy, ExportFormat, ExportContext
)

# Concrete implementations
from app.services.infrastructure.sheets_connection_service import SheetsConnectionService
from app.services.infrastructure.sheets_data_service import SheetsDataService
from app.services.business.sheets_listing_service import SheetsListingService

# Strategy implementations
from app.core.strategies.optimization_strategies import (
    BasicOptimizationStrategy, AdvancedOptimizationStrategy
)
from app.core.strategies.export_strategies import (
    CSVExportStrategy, JSONExportStrategy, XMLExportStrategy, EbayBulkExportStrategy
)

from app.core.optimizer import EbayOptimizer
from app.services.google_sheets import GoogleSheetsService


def configure_infrastructure_services():
    """Configure infrastructure layer services"""
    
    # Data connection services
    ServiceRegistry.register(
        IDataConnectionService, 
        SheetsConnectionService, 
        singleton=True
    )
    
    # Sheets data services
    ServiceRegistry.register(
        ISheetsDataService, 
        SheetsDataService, 
        singleton=True
    )


def configure_business_services():
    """Configure business layer services"""
    
    # Listing services
    ServiceRegistry.register(
        IListingDataService, 
        SheetsListingService, 
        singleton=False  # New instance each time for better isolation
    )
    
    # Legacy Google Sheets service (for backward compatibility)
    ServiceRegistry.register_instance(
        GoogleSheetsService,
        GoogleSheetsService()
    )


def configure_optimization_strategies():
    """Configure optimization strategy services"""
    
    # Register optimization strategies
    def create_basic_strategy():
        return BasicOptimizationStrategy()
    
    def create_advanced_strategy():
        return AdvancedOptimizationStrategy()
    
    # Register strategy factories
    ServiceRegistry.register_factory(
        IOptimizationStrategy,
        create_basic_strategy,
        singleton=False
    )
    
    # Register optimization context
    ServiceRegistry.register(
        OptimizationContext,
        OptimizationContext,
        singleton=True
    )


def configure_export_strategies():
    """Configure export strategy services"""
    
    # Register export strategies
    def create_csv_strategy():
        return CSVExportStrategy()
    
    def create_json_strategy():
        return JSONExportStrategy()
    
    def create_xml_strategy():
        return XMLExportStrategy()
    
    def create_ebay_bulk_strategy():
        return EbayBulkExportStrategy()
    
    # Register strategy factories
    ServiceRegistry.register_factory(
        IExportStrategy,
        create_csv_strategy,
        singleton=False
    )
    
    # Register export context
    ServiceRegistry.register(
        ExportContext,
        ExportContext,
        singleton=True
    )


def configure_core_services():
    """Configure core application services"""
    
    # EbayOptimizer as singleton
    ServiceRegistry.register(
        EbayOptimizer,
        EbayOptimizer,
        singleton=True
    )


def configure_all_services():
    """
    Configure all application services
    This is the main configuration function called at startup
    """
    
    # Clear any existing registrations
    ServiceRegistry.reset()
    
    # Configure services in dependency order
    configure_infrastructure_services()
    configure_business_services()
    configure_optimization_strategies()
    configure_export_strategies()
    configure_core_services()
    
    print("✅ All services configured successfully")
    
    # Return container for inspection
    return ServiceRegistry.get_container()


def get_service_summary():
    """Get summary of all registered services"""
    container = ServiceRegistry.get_container()
    registrations = container.get_registrations()
    
    summary = {
        "total_services": len(registrations["services"]),
        "total_instances": len(registrations["instances"]),
        "total_factories": len(registrations["factories"]),
        "singletons": sum(1 for is_singleton in registrations["singletons"].values() if is_singleton),
        "registrations": registrations
    }
    
    return summary


# Service locator pattern for easy access
class Services:
    """
    Service locator providing easy access to configured services
    Follows DIP by depending on abstractions, not concretions
    """
    
    @staticmethod
    def get_optimization_context() -> OptimizationContext:
        """Get optimization context service"""
        return ServiceRegistry.get(OptimizationContext)
    
    @staticmethod
    def get_export_context() -> ExportContext:
        """Get export context service"""
        return ServiceRegistry.get(ExportContext)
    
    @staticmethod
    def get_optimizer() -> EbayOptimizer:
        """Get eBay optimizer service"""
        return ServiceRegistry.get(EbayOptimizer)
    
    @staticmethod
    def get_sheets_connection() -> IDataConnectionService:
        """Get sheets connection service"""
        return ServiceRegistry.get(IDataConnectionService)
    
    @staticmethod
    def get_sheets_data() -> ISheetsDataService:
        """Get sheets data service"""
        return ServiceRegistry.get(ISheetsDataService)
    
    @staticmethod
    def get_listing_service() -> IListingDataService:
        """Get listing data service"""
        return ServiceRegistry.get(IListingDataService)
    
    @staticmethod
    def get_google_sheets() -> GoogleSheetsService:
        """Get legacy Google Sheets service"""
        return ServiceRegistry.get(GoogleSheetsService)
    
    @staticmethod
    def create_optimization_strategy(strategy_type: OptimizationType) -> IOptimizationStrategy:
        """Create optimization strategy instance"""
        if strategy_type == OptimizationType.BASIC:
            return BasicOptimizationStrategy()
        elif strategy_type == OptimizationType.ADVANCED:
            return AdvancedOptimizationStrategy()
        else:
            raise ValueError(f"Unsupported optimization strategy: {strategy_type}")
    
    @staticmethod
    def create_export_strategy(export_format: ExportFormat) -> IExportStrategy:
        """Create export strategy instance"""
        if export_format == ExportFormat.CSV:
            return CSVExportStrategy()
        elif export_format == ExportFormat.JSON:
            return JSONExportStrategy()
        elif export_format == ExportFormat.XML:
            return XMLExportStrategy()
        elif export_format == ExportFormat.EBAY_BULK:
            return EbayBulkExportStrategy()
        else:
            raise ValueError(f"Unsupported export format: {export_format}")


# Decorator for service injection
def inject_services(func):
    """
    Decorator to inject services into function parameters
    
    Usage:
        @inject_services
        def my_function(optimizer: EbayOptimizer):
            return optimizer.optimize_title("Test")
    """
    import inspect
    from typing import get_type_hints
    
    def wrapper(*args, **kwargs):
        # Get function signature and type hints
        signature = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        # Inject missing parameters
        for param_name, param in signature.parameters.items():
            if param_name in type_hints and param_name not in kwargs:
                param_type = type_hints[param_name]
                
                # Try to get service from registry
                try:
                    service = ServiceRegistry.get(param_type)
                    kwargs[param_name] = service
                except ValueError:
                    # Service not registered, continue without injection
                    pass
        
        return func(*args, **kwargs)
    
    return wrapper