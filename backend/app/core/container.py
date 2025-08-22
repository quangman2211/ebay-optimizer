"""
Dependency Injection Container (Dependency Inversion Principle)
Manages dependencies and enables loose coupling between components
"""

from typing import Dict, Type, Any, TypeVar, Optional, Callable
from abc import ABC, abstractmethod
import inspect

T = TypeVar('T')


class IDependencyContainer(ABC):
    """Interface for dependency injection container"""
    
    @abstractmethod
    def register(self, interface: Type[T], implementation: Type[T], singleton: bool = False) -> None:
        """Register a service implementation"""
        pass
    
    @abstractmethod
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register a specific instance"""
        pass
    
    @abstractmethod
    def get(self, interface: Type[T]) -> T:
        """Get service implementation"""
        pass
    
    @abstractmethod
    def create(self, implementation: Type[T]) -> T:
        """Create instance with dependency injection"""
        pass


class DependencyContainer(IDependencyContainer):
    """
    Simple dependency injection container
    Implements DIP by inverting dependencies and enabling loose coupling
    """
    
    def __init__(self):
        self._services: Dict[Type, Type] = {}
        self._instances: Dict[Type, Any] = {}
        self._singletons: Dict[Type, bool] = {}
        self._factories: Dict[Type, Callable] = {}
    
    def register(self, interface: Type[T], implementation: Type[T], singleton: bool = False) -> None:
        """
        Register a service implementation
        
        Args:
            interface: The interface/abstract class
            implementation: The concrete implementation
            singleton: Whether to create only one instance
        """
        self._services[interface] = implementation
        self._singletons[interface] = singleton
        
        # Clear existing instance if re-registering
        if interface in self._instances:
            del self._instances[interface]
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T], singleton: bool = False) -> None:
        """Register a factory function for creating instances"""
        self._factories[interface] = factory
        self._singletons[interface] = singleton
    
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register a specific instance (always singleton)"""
        self._instances[interface] = instance
        self._singletons[interface] = True
    
    def get(self, interface: Type[T]) -> T:
        """
        Get service implementation with dependency injection
        
        Args:
            interface: The interface to resolve
            
        Returns:
            Instance of the registered implementation
        """
        # Return existing instance if singleton
        if interface in self._instances:
            return self._instances[interface]
        
        # Use factory if registered
        if interface in self._factories:
            instance = self._factories[interface]()
            if self._singletons.get(interface, False):
                self._instances[interface] = instance
            return instance
        
        # Get registered implementation
        if interface not in self._services:
            raise ValueError(f"No implementation registered for {interface}")
        
        implementation = self._services[interface]
        instance = self.create(implementation)
        
        # Store as singleton if needed
        if self._singletons.get(interface, False):
            self._instances[interface] = instance
        
        return instance
    
    def create(self, implementation: Type[T]) -> T:
        """
        Create instance with automatic dependency injection
        
        Args:
            implementation: The class to instantiate
            
        Returns:
            Instance with all dependencies injected
        """
        # Get constructor signature
        signature = inspect.signature(implementation.__init__)
        parameters = signature.parameters
        
        # Skip 'self' parameter
        dependencies = {
            name: param for name, param in parameters.items() 
            if name != 'self'
        }
        
        # Resolve dependencies
        kwargs = {}
        for name, param in dependencies.items():
            param_type = param.annotation
            
            # Skip if no type annotation
            if param_type == inspect.Parameter.empty:
                if param.default != inspect.Parameter.empty:
                    continue  # Use default value
                else:
                    raise ValueError(f"No type annotation for parameter {name} in {implementation}")
            
            # Try to resolve dependency
            try:
                kwargs[name] = self.get(param_type)
            except ValueError:
                # If dependency not registered and has default, use default
                if param.default != inspect.Parameter.empty:
                    continue
                else:
                    raise ValueError(f"Cannot resolve dependency {param_type} for parameter {name}")
        
        return implementation(**kwargs)
    
    def is_registered(self, interface: Type) -> bool:
        """Check if interface is registered"""
        return (interface in self._services or 
                interface in self._instances or 
                interface in self._factories)
    
    def clear(self) -> None:
        """Clear all registrations"""
        self._services.clear()
        self._instances.clear()
        self._singletons.clear()
        self._factories.clear()
    
    def get_registrations(self) -> Dict[str, Any]:
        """Get summary of all registrations"""
        return {
            "services": {str(k): str(v) for k, v in self._services.items()},
            "instances": {str(k): str(type(v)) for k, v in self._instances.items()},
            "factories": {str(k): str(v) for k, v in self._factories.items()},
            "singletons": {str(k): v for k, v in self._singletons.items()}
        }


class ServiceRegistry:
    """
    Global service registry for dependency injection
    Provides easy access to the DI container
    """
    
    _container: Optional[DependencyContainer] = None
    
    @classmethod
    def get_container(cls) -> DependencyContainer:
        """Get the global DI container"""
        if cls._container is None:
            cls._container = DependencyContainer()
        return cls._container
    
    @classmethod
    def register(cls, interface: Type[T], implementation: Type[T], singleton: bool = False) -> None:
        """Register service in global container"""
        cls.get_container().register(interface, implementation, singleton)
    
    @classmethod
    def register_instance(cls, interface: Type[T], instance: T) -> None:
        """Register instance in global container"""
        cls.get_container().register_instance(interface, instance)
    
    @classmethod
    def register_factory(cls, interface: Type[T], factory: Callable[[], T], singleton: bool = False) -> None:
        """Register factory in global container"""
        cls.get_container().register_factory(interface, factory, singleton)
    
    @classmethod
    def get(cls, interface: Type[T]) -> T:
        """Get service from global container"""
        return cls.get_container().get(interface)
    
    @classmethod
    def create(cls, implementation: Type[T]) -> T:
        """Create instance with DI from global container"""
        return cls.get_container().create(implementation)
    
    @classmethod
    def reset(cls) -> None:
        """Reset global container"""
        if cls._container:
            cls._container.clear()
        cls._container = None


def inject(interface: Type[T]) -> Callable[[Callable], Callable]:
    """
    Decorator for dependency injection
    
    Usage:
        @inject(IMyService)
        def my_function(service: IMyService):
            return service.do_something()
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Auto-inject if parameter not provided
            signature = inspect.signature(func)
            param_names = list(signature.parameters.keys())
            
            # Find parameter that needs injection
            for i, param_name in enumerate(param_names):
                param = signature.parameters[param_name]
                if param.annotation == interface:
                    # If not provided in args/kwargs, inject it
                    if (i >= len(args) and param_name not in kwargs):
                        kwargs[param_name] = ServiceRegistry.get(interface)
                    break
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


class ConfigurableService:
    """
    Base class for services that support dependency injection
    """
    
    def __init__(self, container: Optional[DependencyContainer] = None):
        self._container = container or ServiceRegistry.get_container()
    
    def get_service(self, interface: Type[T]) -> T:
        """Get service instance from container"""
        return self._container.get(interface)
    
    def create_instance(self, implementation: Type[T]) -> T:
        """Create instance with dependency injection"""
        return self._container.create(implementation)