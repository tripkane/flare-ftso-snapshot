"""
WebDriver resource management with proper cleanup and context managers.
"""
import os
import time
import atexit
import logging
from contextlib import contextmanager
from typing import Optional, Generator

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException

from exceptions import WebDriverError, ConfigurationError

logger = logging.getLogger(__name__)

# Global registry to track active drivers for cleanup
_active_drivers = set()


def _cleanup_all_drivers():
    """Cleanup function called on program exit."""
    global _active_drivers
    for driver in list(_active_drivers):
        try:
            driver.quit()
            logger.info("Cleaned up WebDriver on exit")
        except Exception as e:
            logger.error(f"Error cleaning up WebDriver on exit: {e}")
    _active_drivers.clear()


# Register cleanup function
atexit.register(_cleanup_all_drivers)


class WebDriverManager:
    """Manages WebDriver lifecycle with proper resource cleanup."""
    
    def __init__(self, max_retries: int = 3, retry_delay: int = 5):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.driver: Optional[webdriver.Chrome] = None
        
    def _create_driver_options(self) -> Options:
        """Create Chrome options for headless operation."""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-logging')
        options.add_argument('--silent')
        options.add_argument('--log-level=3')  # Suppress INFO, WARNING, ERROR
        
        # Set binary location if specified
        binary_path = os.getenv('CHROMIUM_BINARY')
        if binary_path:
            if not os.path.exists(binary_path):
                raise ConfigurationError(f"Chromium binary not found: {binary_path}")
            options.binary_location = binary_path
            
        return options
        
    def _create_driver_service(self) -> Service:
        """Create Chrome service with custom driver path if specified."""
        driver_path = os.getenv('CHROMEDRIVER')
        if driver_path:
            if not os.path.exists(driver_path):
                raise ConfigurationError(f"ChromeDriver not found: {driver_path}")
            return Service(driver_path)
        else:
            # Let selenium manage the driver automatically
            return Service()
    
    def create_driver(self) -> webdriver.Chrome:
        """
        Create a new WebDriver instance with retry logic.
        
        Returns:
            Chrome WebDriver instance
            
        Raises:
            WebDriverError: If driver creation fails after retries
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                options = self._create_driver_options()
                service = self._create_driver_service()
                
                driver = webdriver.Chrome(service=service, options=options)
                
                # Test the driver with a simple operation
                driver.set_page_load_timeout(30)
                
                # Register for cleanup
                _active_drivers.add(driver)
                
                logger.info(f"WebDriver created successfully on attempt {attempt + 1}")
                return driver
                
            except WebDriverException as e:
                last_error = e
                logger.warning(f"WebDriver creation attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error creating WebDriver: {e}")
                break
        
        raise WebDriverError(f"Failed to create WebDriver after {self.max_retries} attempts: {last_error}")
    
    def cleanup_driver(self, driver: webdriver.Chrome) -> None:
        """
        Safely cleanup a WebDriver instance.
        
        Args:
            driver: WebDriver instance to cleanup
        """
        if driver is None:
            return
            
        try:
            # Remove from active registry
            _active_drivers.discard(driver)
            
            # Quit the driver
            driver.quit()
            logger.info("WebDriver cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error cleaning up WebDriver: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        self.driver = self.create_driver()
        return self.driver
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        if self.driver:
            self.cleanup_driver(self.driver)
            self.driver = None


@contextmanager
def get_webdriver(max_retries: int = 3, retry_delay: int = 5) -> Generator[webdriver.Chrome, None, None]:
    """
    Context manager for WebDriver with automatic cleanup.
    
    Args:
        max_retries: Maximum retry attempts for driver creation
        retry_delay: Delay between retry attempts in seconds
        
    Yields:
        Chrome WebDriver instance
        
    Example:
        with get_webdriver() as driver:
            driver.get("https://example.com")
            # Driver automatically cleaned up
    """
    manager = WebDriverManager(max_retries=max_retries, retry_delay=retry_delay)
    
    try:
        driver = manager.create_driver()
        yield driver
    finally:
        manager.cleanup_driver(driver)


def init_driver() -> webdriver.Chrome:
    """
    Legacy function for backward compatibility.
    
    WARNING: This function creates a driver without automatic cleanup.
    Use get_webdriver() context manager instead for better resource management.
    
    Returns:
        Chrome WebDriver instance
    """
    logger.warning("init_driver() is deprecated. Use get_webdriver() context manager instead.")
    manager = WebDriverManager()
    return manager.create_driver()