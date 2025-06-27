"""
Tests for data validation schemas.
"""
import pytest
from pydantic import ValidationError

from schemas import (
    ProviderData, SnapshotData, QueryRequest,
    validate_snapshot_data, sanitize_file_path
)
from exceptions import DataValidationError


class TestProviderData:
    """Test provider data validation."""
    
    def test_valid_provider_data(self):
        """Test valid provider data passes validation."""
        data = {
            "name": "Test Provider",
            "vote_power": 15.5,
            "vote_power_percentage": "15.5%",
            "fee": 20.0,
            "availability": 99.9,
            "reward_rate": 0.85,
            "address": "0x1234567890123456789012345678901234567890"
        }
        provider = ProviderData(**data)
        assert provider.name == "Test Provider"
        assert provider.vote_power == 15.5
    
    def test_name_sanitization(self):
        """Test that dangerous characters are removed from names."""
        data = {
            "name": "Test<script>alert('xss')</script>Provider",
            "vote_power": 10.0
        }
        provider = ProviderData(**data)
        assert "<script>" not in provider.name
        assert "alert" not in provider.name
    
    def test_invalid_vote_power_percentage(self):
        """Test invalid vote power percentage format."""
        data = {
            "name": "Test Provider",
            "vote_power": 10.0,
            "vote_power_percentage": "invalid%"
        }
        with pytest.raises(ValidationError):
            ProviderData(**data)
    
    def test_invalid_address_format(self):
        """Test invalid Ethereum address format."""
        data = {
            "name": "Test Provider",
            "vote_power": 10.0,
            "address": "0xinvalid"
        }
        with pytest.raises(ValidationError):
            ProviderData(**data)


class TestSnapshotData:
    """Test snapshot data validation."""
    
    def test_valid_snapshot_data(self):
        """Test valid snapshot data passes validation."""
        data = {
            "timestamp": "2025-06-27T12-00-00Z",
            "network": "flare",
            "epoch": 100,
            "providers": [
                {
                    "name": "Provider 1",
                    "vote_power": 15.5
                },
                {
                    "name": "Provider 2",
                    "vote_power": 10.0
                }
            ],
            "total_vote_power": 25.5
        }
        snapshot = SnapshotData(**data)
        assert snapshot.network == "flare"
        assert len(snapshot.providers) == 2
    
    def test_duplicate_provider_names(self):
        """Test that duplicate provider names are rejected."""
        data = {
            "timestamp": "2025-06-27T12-00-00Z",
            "network": "flare",
            "providers": [
                {"name": "Provider 1", "vote_power": 15.5},
                {"name": "Provider 1", "vote_power": 10.0}  # Duplicate
            ]
        }
        with pytest.raises(ValidationError, match="Duplicate provider names"):
            SnapshotData(**data)
    
    def test_invalid_network(self):
        """Test invalid network name."""
        data = {
            "timestamp": "2025-06-27T12-00-00Z",
            "network": "invalid",
            "providers": [{"name": "Provider 1", "vote_power": 15.5}]
        }
        with pytest.raises(ValidationError):
            SnapshotData(**data)
    
    def test_empty_providers_list(self):
        """Test empty providers list is rejected."""
        data = {
            "timestamp": "2025-06-27T12-00-00Z",
            "network": "flare",
            "providers": []
        }
        with pytest.raises(ValidationError):
            SnapshotData(**data)


class TestQueryRequest:
    """Test query request validation."""
    
    def test_valid_query_request(self):
        """Test valid query request passes validation."""
        data = {
            "query": "What is the top provider?",
            "context_limit": 1000
        }
        query = QueryRequest(**data)
        assert query.query == "What is the top provider?"
        assert query.context_limit == 1000
    
    def test_query_sanitization(self):
        """Test that dangerous characters are removed from queries."""
        data = {
            "query": "What is <script>alert('xss')</script> the top provider?"
        }
        query = QueryRequest(**data)
        assert "<script>" not in query.query
        assert "alert" not in query.query
    
    def test_query_too_long(self):
        """Test query length limit."""
        data = {
            "query": "x" * 1001  # Too long
        }
        with pytest.raises(ValidationError):
            QueryRequest(**data)
    
    def test_empty_query_after_sanitization(self):
        """Test empty query after sanitization is rejected."""
        data = {
            "query": "<script></script>"  # Only dangerous characters
        }
        with pytest.raises(ValidationError, match="Query cannot be empty"):
            QueryRequest(**data)


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_sanitize_file_path_valid(self):
        """Test valid file path passes sanitization."""
        path = "docs/snapshots/file.json"
        result = sanitize_file_path(path)
        assert result == path
    
    def test_sanitize_file_path_directory_traversal(self):
        """Test directory traversal attempts are blocked."""
        with pytest.raises(ValueError, match="Dangerous pattern"):
            sanitize_file_path("../../../etc/passwd")
    
    def test_sanitize_file_path_absolute_path(self):
        """Test absolute paths are blocked."""
        with pytest.raises(ValueError, match="Absolute paths not allowed"):
            sanitize_file_path("/etc/passwd")
    
    def test_sanitize_file_path_dangerous_characters(self):
        """Test dangerous characters are removed."""
        path = "file<>name.json"
        result = sanitize_file_path(path)
        assert "<" not in result
        assert ">" not in result
    
    def test_validate_snapshot_data_function(self):
        """Test validate_snapshot_data utility function."""
        data = {
            "timestamp": "2025-06-27T12-00-00Z",
            "network": "flare",
            "providers": [{"name": "Provider 1", "vote_power": 15.5}]
        }
        result = validate_snapshot_data(data)
        assert isinstance(result, SnapshotData)
        assert result.network == "flare"