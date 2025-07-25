#!/usr/bin/env python3
"""
Generate secure secret key for production deployment
Organigramma Web App Security Utility
"""

import secrets
import sys
import argparse

def generate_secret_key(length: int = 64) -> str:
    """Generate a cryptographically secure secret key"""
    return secrets.token_urlsafe(length)

def main():
    parser = argparse.ArgumentParser(
        description="Generate secure secret key for Organigramma Web App"
    )
    parser.add_argument(
        "--length", 
        type=int, 
        default=64,
        help="Length of the secret key (default: 64)"
    )
    parser.add_argument(
        "--format",
        choices=["env", "raw"],
        default="env",
        help="Output format (default: env)"
    )
    
    args = parser.parse_args()
    
    if args.length < 32:
        print("Warning: Secret key length should be at least 32 characters for security", file=sys.stderr)
    
    secret_key = generate_secret_key(args.length)
    
    if args.format == "env":
        print(f"SECRET_KEY={secret_key}")
        print()
        print("Add this line to your .env file for production deployment.")
        print("Keep this key secure and never commit it to version control!")
    else:
        print(secret_key)

if __name__ == "__main__":
    main()