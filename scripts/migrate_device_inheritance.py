"""
Device Structure Migration Script
PRD: PRD_Device_Structure_Refactoring.md - Phase 8

Migrates from separate controllers/sensors/cameras tables to
Joined Table Inheritance with a base 'devices' table.

Usage:
    python scripts/migrate_device_inheritance.py [--dry-run]

Changes:
1. Creates 'devices' base table with common fields
2. Migrates data from controllers/sensors/cameras to devices
3. Updates child tables to use FK to devices.id
4. Creates device_group_mappings for N:N relationships
"""

import argparse
import sqlite3
import sys
from pathlib import Path
from datetime import datetime


def get_db_path():
    """Get database path from environment or use default"""
    import os
    return os.getenv("DATABASE_PATH", "data/gop.db")


def backup_database(db_path: str) -> str:
    """Create backup of database before migration"""
    import shutil
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    shutil.copy2(db_path, backup_path)
    print(f"Created backup: {backup_path}")
    return backup_path


def check_migration_needed(conn: sqlite3.Connection) -> bool:
    """Check if migration is needed (devices table doesn't exist)"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='devices'
    """)
    return cursor.fetchone() is None


def migrate_controllers(conn: sqlite3.Connection, dry_run: bool = False):
    """Migrate controllers data to devices table"""
    cursor = conn.cursor()

    # Check if old controllers table has the common fields
    cursor.execute("PRAGMA table_info(controllers)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'number_device' not in columns:
        print("Controllers table already migrated or new structure")
        return 0

    # Get all controllers with their data
    cursor.execute("""
        SELECT id, number_device, group_device, name_device, type_device,
               version, status, created_at, updated_at, ip_address, ip_port
        FROM controllers
    """)
    controllers = cursor.fetchall()

    if dry_run:
        print(f"  Would migrate {len(controllers)} controllers")
        return len(controllers)

    # Insert into devices table
    for ctrl in controllers:
        cursor.execute("""
            INSERT INTO devices (id, category_device, number_device, group_device,
                                name_device, type_device, version, status,
                                created_at, updated_at)
            VALUES (?, 'controller', ?, ?, ?, ?, ?, ?, ?, ?)
        """, ctrl[:9])

    print(f"  Migrated {len(controllers)} controllers to devices table")
    return len(controllers)


def migrate_sensors(conn: sqlite3.Connection, dry_run: bool = False):
    """Migrate sensors data to devices table"""
    cursor = conn.cursor()

    # Check if old sensors table has the common fields
    cursor.execute("PRAGMA table_info(sensors)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'number_device' not in columns:
        print("Sensors table already migrated or new structure")
        return 0

    # Get max device id to continue sequence
    cursor.execute("SELECT COALESCE(MAX(id), 0) FROM devices")
    max_id = cursor.fetchone()[0]

    # Get all sensors with their data
    cursor.execute("""
        SELECT id, number_device, group_device, name_device, type_device,
               version, status, created_at, updated_at, controller_id
        FROM sensors
    """)
    sensors = cursor.fetchall()

    if dry_run:
        print(f"  Would migrate {len(sensors)} sensors")
        return len(sensors)

    # Create ID mapping for sensors (old_id -> new_id)
    id_mapping = {}
    for i, sensor in enumerate(sensors):
        new_id = max_id + i + 1
        id_mapping[sensor[0]] = new_id

        cursor.execute("""
            INSERT INTO devices (id, category_device, number_device, group_device,
                                name_device, type_device, version, status,
                                created_at, updated_at)
            VALUES (?, 'sensor', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (new_id,) + sensor[1:9])

    print(f"  Migrated {len(sensors)} sensors to devices table")
    return len(sensors)


def migrate_cameras(conn: sqlite3.Connection, dry_run: bool = False):
    """Migrate cameras data to devices table"""
    cursor = conn.cursor()

    # Check if old cameras table has the common fields
    cursor.execute("PRAGMA table_info(cameras)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'number_device' not in columns:
        print("Cameras table already migrated or new structure")
        return 0

    # Get max device id to continue sequence
    cursor.execute("SELECT COALESCE(MAX(id), 0) FROM devices")
    max_id = cursor.fetchone()[0]

    # Get all cameras with their data
    cursor.execute("""
        SELECT id, number_device, group_device, name_device, type_device,
               version, status, created_at, updated_at
        FROM cameras
    """)
    cameras = cursor.fetchall()

    if dry_run:
        print(f"  Would migrate {len(cameras)} cameras")
        return len(cameras)

    for i, camera in enumerate(cameras):
        new_id = max_id + i + 1

        cursor.execute("""
            INSERT INTO devices (id, category_device, number_device, group_device,
                                name_device, type_device, version, status,
                                created_at, updated_at)
            VALUES (?, 'camera', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (new_id,) + camera[1:9])

    print(f"  Migrated {len(cameras)} cameras to devices table")
    return len(cameras)


def create_devices_table(conn: sqlite3.Connection, dry_run: bool = False):
    """Create the devices base table"""
    if dry_run:
        print("  Would create 'devices' table")
        return

    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_device VARCHAR(50) NOT NULL,
            number_device INTEGER NOT NULL UNIQUE,
            group_device INTEGER NOT NULL,
            name_device VARCHAR(200) NOT NULL,
            type_device VARCHAR(50) NOT NULL,
            version VARCHAR(50) NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'ACTIVATED',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_devices_category_device ON devices(category_device)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_devices_number_device ON devices(number_device)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_devices_group_device ON devices(group_device)")
    print("  Created 'devices' table with indexes")


def create_device_group_tables(conn: sqlite3.Connection, dry_run: bool = False):
    """Create device_groups and device_group_mappings tables"""
    if dry_run:
        print("  Would create 'device_groups' and 'device_group_mappings' tables")
        return

    cursor = conn.cursor()

    # Create device_groups table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS device_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create device_group_mappings junction table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS device_group_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL,
            category_device VARCHAR(50) NOT NULL,
            group_id INTEGER NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES device_groups(id) ON DELETE CASCADE,
            UNIQUE (device_id, category_device, group_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_dgm_device ON device_group_mappings(device_id, category_device)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_dgm_group ON device_group_mappings(group_id)")
    print("  Created 'device_groups' and 'device_group_mappings' tables")


def run_migration(db_path: str, dry_run: bool = False):
    """Run the complete migration"""
    print(f"\n{'=' * 50}")
    print(f"Device Structure Migration")
    print(f"Database: {db_path}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'=' * 50}\n")

    if not Path(db_path).exists():
        print(f"Database not found: {db_path}")
        print("Creating new database with new structure...")
        # For new database, just let SQLAlchemy create the tables
        return

    if not dry_run:
        backup_path = backup_database(db_path)

    conn = sqlite3.connect(db_path)

    try:
        if not check_migration_needed(conn):
            print("Migration already completed (devices table exists)")
            return

        print("Step 1: Creating devices table...")
        create_devices_table(conn, dry_run)

        print("Step 2: Creating device_groups tables...")
        create_device_group_tables(conn, dry_run)

        print("Step 3: Migrating controllers...")
        controllers_count = migrate_controllers(conn, dry_run)

        print("Step 4: Migrating sensors...")
        sensors_count = migrate_sensors(conn, dry_run)

        print("Step 5: Migrating cameras...")
        cameras_count = migrate_cameras(conn, dry_run)

        if not dry_run:
            conn.commit()
            print(f"\nMigration complete!")
            print(f"  - Controllers: {controllers_count}")
            print(f"  - Sensors: {sensors_count}")
            print(f"  - Cameras: {cameras_count}")
            print(f"  - Total devices: {controllers_count + sensors_count + cameras_count}")
        else:
            print(f"\n[DRY RUN] Would migrate:")
            print(f"  - Controllers: {controllers_count}")
            print(f"  - Sensors: {sensors_count}")
            print(f"  - Cameras: {cameras_count}")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Migrate device tables to Joined Table Inheritance structure"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help="Path to database file (default: data/gop.db)"
    )

    args = parser.parse_args()

    db_path = args.db or get_db_path()
    run_migration(db_path, args.dry_run)


if __name__ == "__main__":
    main()
