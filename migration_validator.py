#!/usr/bin/env python3
"""
DB2 to PostgreSQL Migration Validation Tool

This script validates the migration from IBM DB2 to PostgreSQL by:
1. Comparing database schemas
2. Validating data integrity
3. Generating comprehensive reports

Usage:
    python migration_validator.py --config config.yaml
    python migration_validator.py --config config.yaml --schema-only
    python migration_validator.py --config config.yaml --data-only
"""

import argparse
import yaml
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List
from db_connection import DB2Connection, PostgreSQLConnection
from schema_validator import SchemaValidator
from data_validator import DataValidator
from report_generator import ReportGenerator

class MigrationValidator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize connections
        self.db2_conn = DB2Connection(config['db2'])
        self.pg_conn = PostgreSQLConnection(config['postgresql'])
        
        # Initialize validators
        self.schema_validator = SchemaValidator(self.db2_conn, self.pg_conn)
        self.data_validator = DataValidator(self.db2_conn, self.pg_conn)
        self.report_generator = ReportGenerator()
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = self.config.get('logging', {}).get('level', 'INFO')
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('migration_validation.log')
            ]
        )
    
    def validate_connections(self) -> bool:
        """Test database connections"""
        self.logger.info("Testing database connections...")
        
        db2_ok = self.db2_conn.test_connection()
        if not db2_ok:
            self.logger.error("Failed to connect to DB2")
            return False
            
        pg_ok = self.pg_conn.test_connection()
        if not pg_ok:
            self.logger.error("Failed to connect to PostgreSQL")
            return False
            
        self.logger.info("Database connections successful")
        return True
    
    def run_schema_validation(self) -> Dict[str, Any]:
        """Run schema validation"""
        self.logger.info("Starting schema validation...")
        
        db2_schema = self.config['validation']['db2_schema']
        pg_schema = self.config['validation'].get('postgresql_schema', 'public')
        
        try:
            schema_results = self.schema_validator.validate_schema_migration(db2_schema, pg_schema)
            self.logger.info("Schema validation completed successfully")
            return schema_results
        except Exception as e:
            self.logger.error(f"Schema validation failed: {e}")
            raise
    
    def run_data_validation(self, tables: List[str] = None) -> Dict[str, Any]:
        """Run data validation"""
        self.logger.info("Starting data validation...")
        
        db2_schema = self.config['validation']['db2_schema']
        pg_schema = self.config['validation'].get('postgresql_schema', 'public')
        
        try:
            if not tables:
                # Get common tables from schema validation
                schema_results = self.run_schema_validation()
                tables = list(schema_results['table_comparison']['common'])
                
            if not tables:
                self.logger.warning("No common tables found for data validation")
                return {}
            
            # Limit tables if specified in config
            max_tables = self.config['validation'].get('max_tables_to_validate')
            if max_tables and len(tables) > max_tables:
                tables = tables[:max_tables]
                self.logger.info(f"Limiting validation to first {max_tables} tables")
            
            data_results = self.data_validator.comprehensive_data_validation(tables, db2_schema, pg_schema)
            self.logger.info("Data validation completed successfully")
            return data_results
        except Exception as e:
            self.logger.error(f"Data validation failed: {e}")
            raise
    
    def generate_reports(self, schema_results: Dict[str, Any], data_results: Dict[str, Any]) -> Dict[str, str]:
        """Generate validation reports"""
        self.logger.info("Generating reports...")
        
        output_dir = Path(self.config.get('output', {}).get('directory', './reports'))
        output_dir.mkdir(exist_ok=True)
        
        base_filename = output_dir / self.config.get('output', {}).get('filename', 'migration_validation')
        
        try:
            reports = self.report_generator.generate_all_reports(schema_results, data_results, str(base_filename))
            
            # Print console report
            if self.config.get('output', {}).get('console', True):
                print(reports['console'])
            
            self.logger.info("Reports generated successfully")
            return reports
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            raise
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete migration validation"""
        self.logger.info("Starting full migration validation...")
        
        # Test connections
        if not self.validate_connections():
            raise Exception("Database connection validation failed")
        
        # Run validations
        schema_results = self.run_schema_validation()
        data_results = self.run_data_validation()
        
        # Generate reports
        reports = self.generate_reports(schema_results, data_results)
        
        # Cleanup connections
        self.cleanup()
        
        self.logger.info("Migration validation completed successfully")
        
        return {
            'schema_results': schema_results,
            'data_results': data_results,
            'reports': reports
        }
    
    def run_schema_only(self) -> Dict[str, Any]:
        """Run only schema validation"""
        self.logger.info("Running schema-only validation...")
        
        if not self.validate_connections():
            raise Exception("Database connection validation failed")
        
        schema_results = self.run_schema_validation()
        reports = self.report_generator.generate_all_reports(schema_results, {})
        
        if self.config.get('output', {}).get('console', True):
            print(reports['console'])
        
        self.cleanup()
        return {'schema_results': schema_results, 'reports': reports}
    
    def run_data_only(self, tables: List[str] = None) -> Dict[str, Any]:
        """Run only data validation"""
        self.logger.info("Running data-only validation...")
        
        if not self.validate_connections():
            raise Exception("Database connection validation failed")
        
        data_results = self.run_data_validation(tables)
        reports = self.report_generator.generate_all_reports({}, data_results)
        
        if self.config.get('output', {}).get('console', True):
            print(reports['console'])
        
        self.cleanup()
        return {'data_results': data_results, 'reports': reports}
    
    def cleanup(self):
        """Close database connections"""
        self.db2_conn.close()
        self.pg_conn.close()
        self.logger.info("Database connections closed")

def load_config(config_file: str) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Error loading config file {config_file}: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='DB2 to PostgreSQL Migration Validator')
    parser.add_argument('--config', '-c', required=True, help='Configuration file (YAML)')
    parser.add_argument('--schema-only', action='store_true', help='Run only schema validation')
    parser.add_argument('--data-only', action='store_true', help='Run only data validation')
    parser.add_argument('--tables', nargs='+', help='Specific tables to validate (for data-only mode)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Adjust log level if verbose
    if args.verbose:
        config.setdefault('logging', {})['level'] = 'DEBUG'
    
    try:
        # Initialize validator
        validator = MigrationValidator(config)
        
        # Run validation based on arguments
        if args.schema_only:
            results = validator.run_schema_only()
        elif args.data_only:
            results = validator.run_data_only(args.tables)
        else:
            results = validator.run_full_validation()
        
        print("\n✅ Migration validation completed successfully!")
        
    except KeyboardInterrupt:
        print("\n❌ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()