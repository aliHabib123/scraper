#!/usr/bin/env python3
"""
Database Connection Test Script

Tests the database connection and reports detailed status.
"""

import sys
from sqlalchemy import create_engine, text
from models.base import get_database_url


def test_connection():
    """Test database connection and return status."""
    
    print("="*60)
    print("DATABASE CONNECTION TEST")
    print("="*60)
    
    # Get database URL
    db_url = get_database_url()
    
    # Hide password in display
    if '@' in db_url:
        display_url = db_url.split('@')[0].rsplit(':', 1)[0] + ':****@' + db_url.split('@')[1]
    else:
        display_url = db_url
    
    print(f"\nDatabase URL: {display_url}")
    
    # Detect database type
    if db_url.startswith('mysql'):
        db_type = 'MySQL'
    elif db_url.startswith('postgresql'):
        db_type = 'PostgreSQL'
    else:
        db_type = 'Unknown'
    
    print(f"Database Type: {db_type}")
    print("\n" + "-"*60)
    
    try:
        # Create engine
        print("Creating database engine...")
        engine = create_engine(db_url, echo=False)
        
        # Test connection
        print("Testing connection...")
        with engine.connect() as connection:
            # Execute a simple query
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
            
            # Get database version
            if db_type == 'MySQL':
                version_result = connection.execute(text("SELECT VERSION()"))
                version = version_result.fetchone()[0]
            elif db_type == 'PostgreSQL':
                version_result = connection.execute(text("SELECT version()"))
                version = version_result.fetchone()[0]
            else:
                version = "Unknown"
            
            print(f"✓ Connection successful!")
            print(f"✓ Database version: {version}")
        
        # Check if tables exist
        print("\nChecking tables...")
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if tables:
            print(f"✓ Found {len(tables)} tables: {', '.join(tables)}")
        else:
            print("⚠ No tables found. Run 'python init_db.py' to create them.")
        
        print("\n" + "="*60)
        print("✓ DATABASE CONNECTION TEST PASSED")
        print("="*60 + "\n")
        
        engine.dispose()
        return True
        
    except Exception as e:
        print(f"\n✗ Connection failed!")
        print(f"✗ Error: {str(e)}")
        print("\n" + "="*60)
        print("✗ DATABASE CONNECTION TEST FAILED")
        print("="*60)
        print("\nTroubleshooting tips:")
        print("1. Check if database server is running:")
        if db_type == 'MySQL':
            print("   mysqladmin ping")
        elif db_type == 'PostgreSQL':
            print("   pg_isready")
        print("2. Verify database credentials in DATABASE_URL")
        print("3. Ensure database exists:")
        if db_type == 'MySQL':
            print("   CREATE DATABASE forum_crawler;")
        elif db_type == 'PostgreSQL':
            print("   createdb forum_crawler")
        print("4. Check firewall/network settings\n")
        
        return False


if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
