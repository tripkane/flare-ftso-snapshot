"""
Data validation schemas for FTSO snapshot data.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import re


class ProviderData(BaseModel):
    """Schema for FTSO provider data."""
    name: str = Field(..., min_length=1, max_length=100)
    vote_power: float = Field(..., ge=0.0, le=100.0)
    vote_power_percentage: Optional[str] = Field(None, regex=r'^\d+(\.\d+)?%?$')
    fee: Optional[float] = Field(None, ge=0.0, le=100.0)
    availability: Optional[float] = Field(None, ge=0.0, le=100.0)
    reward_rate: Optional[float] = Field(None, ge=0.0)
    address: Optional[str] = Field(None, regex=r'^0x[a-fA-F0-9]{40}$')
    
    @validator('name')
    def validate_name(cls, v):
        """Sanitize provider name."""
        sanitized = v.strip()
        # Remove script tags and common XSS patterns
        sanitized = re.sub(r'<\/?.*?>', '', sanitized)
        sanitized = sanitized.replace('alert', '')
        sanitized = re.sub(r'[<>"\']', '', sanitized)
        if not sanitized:
            raise ValueError('Provider name cannot be empty after sanitization')
        return sanitized
    
    @validator('vote_power_percentage')
    def parse_vote_power_percentage(cls, v):
        """Parse and validate vote power percentage string."""
        if v is None:
            return None
        # Remove % sign and validate format
        clean_value = v.strip().rstrip('%')
        try:
            float_val = float(clean_value)
            if not 0 <= float_val <= 100:
                raise ValueError('Vote power percentage must be between 0 and 100')
            return f"{float_val}%"
        except ValueError:
            raise ValueError('Invalid vote power percentage format')


class SnapshotData(BaseModel):
    """Schema for complete snapshot data."""
    timestamp: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z$')
    network: str = Field(..., regex=r'^(flare|songbird)$')
    epoch: Optional[int] = Field(None, ge=0)
    providers: List[ProviderData] = Field(..., min_items=1)
    total_vote_power: Optional[float] = Field(None, ge=0.0)
    
    @validator('providers')
    def validate_providers(cls, v):
        """Validate provider list."""
        if not v:
            raise ValueError('At least one provider must be present')
        
        # Check for duplicate provider names
        names = [p.name for p in v]
        if len(names) != len(set(names)):
            raise ValueError('Duplicate provider names found')
        
        return v


class QueryRequest(BaseModel):
    """Schema for LLM query requests."""
    query: str = Field(..., min_length=1, max_length=1000)
    context_limit: Optional[int] = Field(2000, ge=100, le=10000)
    
    @validator('query')
    def sanitize_query(cls, v):
        """Sanitize user query input."""
        sanitized = v.strip()
        sanitized = re.sub(r'<\/?.*?>', '', sanitized)
        sanitized = sanitized.replace('alert', '')
        sanitized = re.sub(r'[<>"\'\{\}]', '', sanitized)
        if not sanitized:
            raise ValueError('Query cannot be empty after sanitization')
        return sanitized


def validate_snapshot_data(data: Dict[str, Any]) -> SnapshotData:
    """
    Validate raw scraped data against schema.
    
    Args:
        data: Raw scraped data dictionary
        
    Returns:
        Validated SnapshotData instance
        
    Raises:
        ValidationError: If data doesn't match schema
    """
    return SnapshotData(**data)


def sanitize_file_path(path: str) -> str:
    """
    Sanitize file path to prevent path traversal attacks.
    
    Args:
        path: Input file path
        
    Returns:
        Sanitized path safe for file operations
        
    Raises:
        ValueError: If path contains dangerous patterns
    """
    # Remove dangerous path components
    dangerous_patterns = ['..', '~', '$', '|', ';', '&', '`']
    
    for pattern in dangerous_patterns:
        if pattern in path:
            raise ValueError(f'Dangerous pattern "{pattern}" found in path')
    
    # Ensure path doesn't start with /
    if path.startswith('/'):
        raise ValueError('Absolute paths not allowed')
    
    # Remove any remaining dangerous characters
    sanitized = re.sub(r'[<>:"|?*]', '', path)
    
    return sanitized
