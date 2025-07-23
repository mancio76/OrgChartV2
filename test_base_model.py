#!/usr/bin/env python3
"""
Test script for BaseModel functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from dataclasses import dataclass
from datetime import datetime
from models.base import BaseModel, ValidationError, ModelValidationException

@dataclass
class TestModel(BaseModel):
    """Test model for validation"""
    name: str = ""
    email: str = ""
    age: int = 0
    
    def validate(self):
        """Override validation with specific rules"""
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
    print("Testing BaseModel functionality...")
    
    # Test 1: Valid model
    print("\n1. Testing valid model:")
    valid_model = TestModel(name="John Doe", email="john@example.com", age=30)
    valid_model.set_audit_fields()
    
    print(f"Valid model: {valid_model}")
    print(f"Is valid: {valid_model.is_valid()}")
    print(f"Validation errors: {valid_model.validate()}")
    
    # Test 2: to_dict and from_dict
    print("\n2. Testing serialization:")
    model_dict = valid_model.to_dict()
    print(f"Model as dict: {model_dict}")
    
    restored_model = TestModel.from_dict(model_dict)
    print(f"Restored model: {restored_model}")
    
    # Test 3: Invalid model
    print("\n3. Testing invalid model:")
    invalid_model = TestModel(name="", email="invalid-email", age=-5)
    
    print(f"Invalid model: {invalid_model}")
    print(f"Is valid: {invalid_model.is_valid()}")
    errors = invalid_model.validate()
    print(f"Validation errors:")
    for error in errors:
        print(f"  - {error.field}: {error.message} (value: {error.value})")
    
    # Test 4: Validation exception
    print("\n4. Testing validation exception:")
    try:
        invalid_model.validate_and_raise()
    except ModelValidationException as e:
        print(f"Caught validation exception: {e}")
        print(f"Number of errors: {len(e.errors)}")
    
    # Test 5: Audit fields
    print("\n5. Testing audit fields:")
    model = TestModel(name="Jane Doe", email="jane@example.com")
    print(f"Before setting audit fields: created={model.datetime_created}, updated={model.datetime_updated}")
    
    model.set_audit_fields()
    print(f"After setting audit fields: created={model.datetime_created}, updated={model.datetime_updated}")
    
    # Simulate update
    import time
    time.sleep(0.1)  # Small delay to see difference
    model.set_audit_fields(is_update=True)
    print(f"After update: created={model.datetime_created}, updated={model.datetime_updated}")
    
    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    test_base_model()