"""
Custom exceptions for FTSO snapshot application.
"""


class FTSOSnapshotError(Exception):
    """Base exception for FTSO snapshot operations."""
    pass


class WebScrapingError(FTSOSnapshotError):
    """Raised when web scraping operations fail."""
    
    def __init__(self, message: str, url: str = None, status_code: int = None):
        super().__init__(message)
        self.url = url
        self.status_code = status_code
        
    def __str__(self):
        base_msg = super().__str__()
        if self.url:
            base_msg += f" (URL: {self.url})"
        if self.status_code:
            base_msg += f" (Status: {self.status_code})"
        return base_msg


class DataValidationError(FTSOSnapshotError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: str = None, value: str = None):
        super().__init__(message)
        self.field = field
        self.value = value
        
    def __str__(self):
        base_msg = super().__str__()
        if self.field:
            base_msg += f" (Field: {self.field})"
        if self.value:
            base_msg += f" (Value: {self.value})"
        return base_msg


class WebDriverError(FTSOSnapshotError):
    """Raised when WebDriver operations fail."""
    pass


class FileOperationError(FTSOSnapshotError):
    """Raised when file operations fail."""
    
    def __init__(self, message: str, file_path: str = None):
        super().__init__(message)
        self.file_path = file_path
        
    def __str__(self):
        base_msg = super().__str__()
        if self.file_path:
            base_msg += f" (Path: {self.file_path})"
        return base_msg


class RPCError(FTSOSnapshotError):
    """Raised when RPC operations fail."""
    
    def __init__(self, message: str, endpoint: str = None, method: str = None):
        super().__init__(message)
        self.endpoint = endpoint
        self.method = method
        
    def __str__(self):
        base_msg = super().__str__()
        if self.endpoint:
            base_msg += f" (Endpoint: {self.endpoint})"
        if self.method:
            base_msg += f" (Method: {self.method})"
        return base_msg


class NetworkError(FTSOSnapshotError):
    """Raised when network operations fail."""
    
    def __init__(self, message: str, retry_count: int = None):
        super().__init__(message)
        self.retry_count = retry_count
        
    def __str__(self):
        base_msg = super().__str__()
        if self.retry_count is not None:
            base_msg += f" (Retries: {self.retry_count})"
        return base_msg


class ConfigurationError(FTSOSnapshotError):
    """Raised when configuration is invalid or missing."""
    pass