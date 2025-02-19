#!/usr/bin/env python3
import sqlite3
import psycopg2
import sys
from typing import Dict, List, Any

def sqlite_to_pg_type(sqlite_type: str, column_name: str = '') -> str:
    """Convert SQLite type to PostgreSQL type."""
    # Special handling for known columns
    if column_name.lower() == 'scope':
        return 'TEXT[]'
        
    sqlite_type = sqlite_type.upper()
    type_mapping = {
        'INTEGER': 'INTEGER',
        'REAL': 'DOUBLE PRECISION',
        'TEXT': 'TEXT',
        'BLOB': 'BYTEA',
        'BOOLEAN': 'BOOLEAN',
        'TIMESTAMP': 'TIMESTAMP',
        'JSON': 'JSONB',
        'VARCHAR(255)': 'VARCHAR(255)'
    }
    return type_mapping.get(sqlite_type, 'TEXT')

def get_safe_identifier(identifier: str) -> str:
    """Quote identifier if it's a reserved keyword."""
    reserved_keywords = [
        "user",
        "group",
        "order",
        "table",
        "select",
        "where",
        "from",
        "index",
        "constraint"
    ]
    return f'"{identifier}"' if identifier.lower() in reserved_keywords else identifier

def print_pg_column_types(columns: Dict[str, str]) -> None:
    """Print PostgreSQL column types."""
    print("  - columns (POSTGRES)")
    for name, type_ in columns.items():
        print(f"    {name}: {type_}")

def debug_print(msg: str) -> None:
    """Print debug message."""
    print(f"DEBUG: {msg}")

def migrate():
    if len(sys.argv) != 3:
        print("Usage: python migrate.py <sqlite_path> <postgres_url>")
        sys.exit(1)

    sqlite_path = sys.argv[1]
    pg_url = sys.argv[2]

    print(f"Arguments: {sys.argv}")

    # Connect to SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cursor = sqlite_conn.cursor()

    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(pg_url)
    pg_cursor = pg_conn.cursor()

    try:
        # Get all tables from SQLite
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = sqlite_cursor.fetchall()

        for (table_name,) in tables:
            safe_table_name = get_safe_identifier(table_name)
            print(f"table: {table_name} -> {safe_table_name}")

            # Skip migration tables
            if table_name in ('migratehistory', 'alembic_version'):
                print("  - skipping: migration table")
                continue

            # Check if table exists in PostgreSQL
            pg_cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                )
            """, (table_name,))
            table_exists = pg_cursor.fetchone()[0]

            if table_exists:
                pg_cursor.execute(f"SELECT COUNT(*) FROM {safe_table_name}")
                row_count = pg_cursor.fetchone()[0]
                if row_count > 0:
                    print(f"  - skipping table: has {row_count} existing rows")
                    continue

            print("  - migrating")

            # Get PostgreSQL column types
            pg_cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    udt_name
                FROM information_schema.columns 
                WHERE table_name = %s
            """, (table_name,))
            
            pg_column_types = {}
            for col in pg_cursor.fetchall():
                pg_column_types[col[0]] = 'ARRAY' if col[2].startswith('_') else col[1]
            print_pg_column_types(pg_column_types)

            # Get SQLite schema using safe table name
            sqlite_cursor.execute(f'PRAGMA table_info("{table_name}")')
            sqlite_schema = sqlite_cursor.fetchall()
            debug_print(f"SQLite schema for {table_name}: {sqlite_schema}")

            # Create table in PostgreSQL if it doesn't exist
            if not table_exists:
                columns = []
                for col in sqlite_schema:
                    col_name = get_safe_identifier(col[1])
                    col_type = sqlite_to_pg_type(col[2], col[1])
                    columns.append(f"{col_name} {col_type}")
                create_table_sql = f"CREATE TABLE IF NOT EXISTS {safe_table_name} ({', '.join(columns)})"
                debug_print(f"Create table SQL: {create_table_sql}")
                pg_cursor.execute(create_table_sql)

            # Migrate data
            sqlite_cursor.execute(f'SELECT * FROM "{table_name}"')
            rows = sqlite_cursor.fetchall()
            column_names = [description[0] for description in sqlite_cursor.description]

            for row in rows:
                try:
                    columns_sql = ', '.join(map(get_safe_identifier, column_names))
                    values = []
                    
                    for col_name, value in zip(column_names, row):
                        col_type = pg_column_types.get(col_name)
                        
                        if value is None:
                            values.append('NULL')
                        elif col_type == 'boolean':
                            values.append('true' if value == 1 else 'false')
                        elif col_type == 'ARRAY':
                            if not value:
                                values.append('NULL')
                            else:
                                # Handle array values stored as comma-separated strings
                                array_values = [f"'{v.strip().replace(chr(39), chr(39)+chr(39))}'" 
                                              for v in value.split(',')]
                                values.append(f"ARRAY[{','.join(array_values)}]")
                        elif isinstance(value, str):
                            values.append(f"'{value.replace(chr(39), chr(39)+chr(39))}'")
                        else:
                            values.append(str(value))

                    values_sql = ', '.join(values)
                    insert_sql = f"INSERT INTO {safe_table_name} ({columns_sql}) VALUES ({values_sql})"
                    debug_print(f"Insert SQL: {insert_sql}")
                    pg_cursor.execute(insert_sql)

                except Exception as e:
                    debug_print(f"Error processing row in {table_name}: {e}")
                    debug_print(f"Row data: {row}")
                    raise

            pg_conn.commit()
            print(f"Migrated {len(rows)} rows from {table_name}")

        print("Migration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {e}")
        pg_conn.rollback()
        raise
    finally:
        sqlite_cursor.close()
        sqlite_conn.close()
        pg_cursor.close()
        pg_conn.close()

if __name__ == '__main__':
    migrate()