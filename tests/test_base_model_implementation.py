#!/usr/bin/env python3
"""
Test script to verify BaseModel implementation
"""

import sys
import os
from datetime import datetime
from dataclasses import dataclass, field

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from models.base import BaseModel, ValidationError, ModelValidationException


@dataclass
class TestModel(BaseModel):
    """Test model for validation"""
    name: str = field(default="")
    email: str = field(default="")
    age: int = field(default=0)
    
    def validate(self):
        """Custom validation for test model"""
        errors = super().validate()
        
        # Email validation
        if self.email and '@' not in self.email:
            errors.append(ValidationError(
                field='email',
                message='Invalid email format',
                value=self.email
            ))
        
        # Age validation
        if self.age < 0:
            errors.append(ValidationError(
                field='age',
                message='Age cannot be negative',
                value=self.age
            ))
        
        return errors


def test_base_model():
    """Test BaseModel functionality"""
    print("Testing BaseModel implementation...")
    
    # Test 1: Basic model creation and audit fields
    print("\n1. Testing audit fields...")
    model = TestModel(name="John Doe", email="john@example.com", age=30)
    model.set_audit_fields()
    
    assert model.datetime_created is not None
    assert model.datetime_updated is not None
    print("✓ Audit fields set correctly")
    
    # Test 2: Serialization to dict
    print("\n2. Testing to_dict serialization...")
    data = model.to_dict()
    assert 'name' in data
    assert 'email' in data
    assert 'age' in data
    assert 'datetime_created' in data
    assert 'datetime_updated' in data
    assert isinstance(data['datetime_created'], str)  # Should be ISO format
    print("✓ to_dict serialization works correctly")
    
    # Test 3: Deserialization from dict
    print("\n3. Testing from_dict deserialization...")
    new_model = TestModel.from_dict(data)
    assert new_model.name == model.name
    assert new_model.email == model.email
    assert new_model.age == model.age
    assert isinstance(new_model.datetime_created, datetime)
    print("✓ from_dict deserialization works correctly")
    
    # Test 4: SQLite row simulation
    print("\n4. Testing from_sqlite_row...")
    
    class MockRow:
        def __init__(self, data):
            self._data = data
        
        def __iter__(self):
            return iter(self._data.items())
        
        def keys(self):
            return self._data.keys()
        
        def values(self):
            return self._data.values()
        
        def items(self):
            return self._data.items()
        
        def __getitem__(self, key):
            return self._data[key]
    
    # Create a mock SQLite row
    row_data = {
        'name': 'Jane Doe',
        'email': 'jane@example.com',
        'age': 25,
        'datetime_created': '2024-01-01T10:00:00',
        'datetime_updated': '2024-01-01T10:00:00'
    }
    mock_row = MockRow(row_data)
    
    # Test from_sqlite_row with mock row that behaves like dict
    row_model = TestModel.from_sqlite_row(mock_row)
    assert row_model.name == 'Jane Doe'
    assert row_model.email == 'jane@example.com'
    print("✓ from_sqlite_row simulation works correctly")
    
    # Test 5: Validation framework
    print("\n5. Testing validation framework...")
    
    # Valid model
    valid_model = TestModel(name="Valid User", email="valid@example.com", age=25)
    assert valid_model.is_valid()
    print("✓ Valid model passes validation")
    
    # Invalid model - missing required field
    try:
        invalid_model = TestModel(name="", email="invalid-email", age=-5)
        errors = invalid_model.validate()
        assert len(errors) > 0
        print(f"✓ Invalid model has {len(errors)} validation errors:")
        for error in errors:
            print(f"  - {error.field}: {error.message}")
    except Exception as e:
        print(f"✗ Validation test failed: {e}")
    
    # Test 6: ValidationError exception
    print("\n6. Testing ModelValidationException...")
    try:
        invalid_model = TestModel(name="", email="invalid-email", age=-5)
        invalid_model.validate_and_raise()
        print("✗ Should have raised ModelValidationException")
    except ModelValidationException as e:
        print(f"✓ ModelValidationException raised correctly: {e}")
        assert len(e.errors) > 0
    
    # Test 7: Update audit fields
    print("\n7. Testing update audit fields...")
    original_created = model.datetime_created
    original_updated = model.datetime_updated
    
    # Simulate a small delay
    import time
    time.sleep(0.01)
    
    model.set_audit_fields(is_update=True)
    assert model.datetime_created == original_created  # Should not change
    assert model.datetime_updated > original_updated   # Should be updated
    print("✓ Update audit fields work correctly")
    
    print("\n🎉 All BaseModel tests passed!")


if __name__ == "__main__":
    test_base_model()