# Open WebUI Database Migrator

A Python-based migration tool for transitioning Open WebUI's SQLite database to PostgreSQL. This tool preserves all data while converting database schemas and data types appropriately.

## Overview

Open WebUI uses SQLite as its default database for managing user data, chat histories, file storage, and other core functionalities. This migrator helps you transition to PostgreSQL for improved scalability and concurrent access capabilities.

## Features

- Complete schema migration from SQLite to PostgreSQL
- Automatic data type conversion and mapping
- Preserves existing data integrity
- Handles special cases like arrays and JSON fields
- Safe migration with transaction support
- Detailed logging and debug output
- Skips tables with existing data to prevent duplicates

## Prerequisites

- Python 3.x
- SQLite database from Open WebUI
- PostgreSQL server
- Required Python packages:
  - `psycopg2`
  - `sqlite3` (usually included with Python)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/openwebui-migrator.git
cd openwebui-migrator
```

2. Install dependencies:
```bash
pip install psycopg2
```

## Usage

Run the migration script with your SQLite database path and PostgreSQL connection URL:

```bash
python migrate.py <sqlite_path> <postgres_url>
```

Example:
```bash
python migrate.py /path/to/webui.db "postgresql://user:password@localhost/openwebui"
```

## How It Works

The migrator performs the following steps:

1. Connects to both SQLite and PostgreSQL databases
2. Retrieves table schemas from SQLite
3. Creates corresponding tables in PostgreSQL with appropriate data types
4. Migrates data with proper type conversion
5. Handles special cases like:
   - Reserved keywords in table/column names
   - Array data types
   - JSON/JSONB fields
   - Boolean conversions

## Supported Tables

The migrator handles all core Open WebUI tables including:
- User management (`user`, `auth`, `group`)
- Chat system (`chat`, `message`, `channel`)
- File storage (`file`, `document`)
- Configuration (`config`, `model`)
- And more

## Type Mappings

SQLite to PostgreSQL type conversions:
- `INTEGER` → `INTEGER`
- `REAL` → `DOUBLE PRECISION`
- `TEXT` → `TEXT`
- `BLOB` → `BYTEA`
- `BOOLEAN` → `BOOLEAN`
- `TIMESTAMP` → `TIMESTAMP`
- `JSON` → `JSONB`
- Special handling for array types

## Error Handling

- Transaction-based migration ensures data integrity
- Detailed error logging
- Skips tables with existing data
- Handles SQL reserved keywords
- Safe string escaping for special characters

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

Inspired by [open-webui-starter](https://github.com/iamobservable/open-webui-starter) (Node.js migrator)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and feature requests, please use the GitHub issue tracker.