"""
Database schema migration script to fix missing columns and schema mismatches
"""

import sqlite3
import os
from pathlib import Path
from typing import List, Tuple
from datetime import datetime

from ..config.settings import settings
from ..utils.logging import monitoring_logger


class DatabaseMigration:
    """Handle database schema migrations and fixes"""
    
    def __init__(self):
        self.metrics_db_path = settings.metrics_db_path
        self.conversation_db_path = settings.conversation_db_path
        self.backup_suffix = datetime.now().strftime("_%Y%m%d_%H%M%S.backup")
    
    def backup_databases(self) -> bool:
        """Create backup copies of databases before migration"""
        try:
            # Backup metrics DB
            if os.path.exists(self.metrics_db_path):
                metrics_backup = str(self.metrics_db_path) + self.backup_suffix
                with open(self.metrics_db_path, 'rb') as src, open(metrics_backup, 'wb') as dst:
                    dst.write(src.read())
                monitoring_logger.info(f"Backed up metrics DB to: {metrics_backup}")
            
            # Backup conversation DB  
            if os.path.exists(self.conversation_db_path):
                conv_backup = str(self.conversation_db_path) + self.backup_suffix
                with open(self.conversation_db_path, 'rb') as src, open(conv_backup, 'wb') as dst:
                    dst.write(src.read())
                monitoring_logger.info(f"Backed up conversation DB to: {conv_backup}")
            
            return True
        except Exception as e:
            monitoring_logger.error(f"Failed to backup databases: {e}")
            return False
    
    def get_table_columns(self, db_path: str, table_name: str) -> List[str]:
        """Get current columns in a table"""
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute(f"PRAGMA table_info({table_name})")
                return [row[1] for row in cursor.fetchall()]
        except Exception as e:
            monitoring_logger.warning(f"Could not get columns for {table_name}: {e}")
            return []
    
    def add_missing_columns(self, db_path: str, table_name: str, expected_columns: List[Tuple[str, str]]) -> bool:
        """Add missing columns to existing table"""
        try:
            current_columns = self.get_table_columns(db_path, table_name)
            missing_columns = []
            
            for col_name, col_type in expected_columns:
                if col_name not in current_columns:
                    missing_columns.append((col_name, col_type))
            
            if not missing_columns:
                monitoring_logger.info(f"Table {table_name} schema is up to date")
                return True
            
            with sqlite3.connect(db_path) as conn:
                for col_name, col_type in missing_columns:
                    alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
                    monitoring_logger.info(f"Adding column: {alter_sql}")
                    conn.execute(alter_sql)
                conn.commit()
                
            monitoring_logger.info(f"Added {len(missing_columns)} columns to {table_name}")
            return True
            
        except Exception as e:
            monitoring_logger.error(f"Failed to add columns to {table_name}: {e}")
            return False
    
    def fix_tool_metrics_schema(self) -> bool:
        """Fix the tool_metrics table schema to match code expectations"""
        expected_columns = [
            # Existing columns (should not be added)
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("conversation_id", "TEXT"),
            ("timestamp", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
            ("tool_name", "TEXT"),
            ("execution_time_ms", "REAL"),
            ("success", "BOOLEAN"),
            ("error_message", "TEXT"),
            ("token_count", "INTEGER"),
            
            # Missing columns that need to be added
            ("estimated_tokens", "INTEGER"),
            ("input_params", "TEXT"),
            ("output_preview", "TEXT"),
            ("dax_query", "TEXT"),
            ("retry_count", "INTEGER DEFAULT 0"),
            ("technical_success", "BOOLEAN"),
            ("quality_success", "BOOLEAN"),
            ("quality_score", "REAL"),
            ("quality_issues", "TEXT")
        ]
        
        # Only add the missing columns (from estimated_tokens onwards)
        missing_columns = [
            ("estimated_tokens", "INTEGER"),
            ("input_params", "TEXT"),
            ("output_preview", "TEXT"),
            ("dax_query", "TEXT"),
            ("retry_count", "INTEGER DEFAULT 0"),
            ("technical_success", "BOOLEAN"),
            ("quality_success", "BOOLEAN"),
            ("quality_score", "REAL"),
            ("quality_issues", "TEXT")
        ]
        
        return self.add_missing_columns(self.metrics_db_path, "tool_metrics", missing_columns)
    
    def verify_schema_consistency(self) -> bool:
        """Verify that database schemas match code expectations"""
        try:
            # Check tool_metrics table
            tool_metrics_columns = self.get_table_columns(self.metrics_db_path, "tool_metrics")
            expected_tool_columns = [
                "id", "conversation_id", "timestamp", "tool_name", "execution_time_ms", 
                "success", "error_message", "token_count", "estimated_tokens", 
                "input_params", "output_preview", "dax_query", "retry_count",
                "technical_success", "quality_success", "quality_score", "quality_issues"
            ]
            
            missing_tool_columns = [col for col in expected_tool_columns if col not in tool_metrics_columns]
            
            if missing_tool_columns:
                monitoring_logger.error(f"tool_metrics still missing columns: {missing_tool_columns}")
                return False
            
            monitoring_logger.info("✅ Database schema verification passed")
            return True
            
        except Exception as e:
            monitoring_logger.error(f"Schema verification failed: {e}")
            return False
    
    def run_migration(self) -> bool:
        """Run the complete migration process"""
        try:
            monitoring_logger.info("Starting database schema migration...")
            
            # 1. Backup databases
            if not self.backup_databases():
                monitoring_logger.error("Migration aborted: backup failed")
                return False
            
            # 2. Fix tool_metrics schema
            if not self.fix_tool_metrics_schema():
                monitoring_logger.error("Migration failed: could not fix tool_metrics schema")
                return False
            
            # 3. Verify schemas
            if not self.verify_schema_consistency():
                monitoring_logger.error("Migration failed: schema verification failed")
                return False
            
            monitoring_logger.info("✅ Database migration completed successfully")
            return True
            
        except Exception as e:
            monitoring_logger.error(f"Migration failed with exception: {e}")
            return False


def migrate_database_schema():
    """Main function to run database migration"""
    migration = DatabaseMigration()
    success = migration.run_migration()
    
    if success:
        print("✅ Database schema migration completed successfully!")
        print("The 'estimated_tokens' column has been added to tool_metrics table.")
        print("No more 'table tool_metrics has no column named estimated_tokens' errors should occur.")
    else:
        print("❌ Database migration failed. Check logs for details.")
        
    return success


if __name__ == "__main__":
    migrate_database_schema()