import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import logging
import hashlib
from db_connection import DB2Connection, PostgreSQLConnection

class DataValidator:
    def __init__(self, db2_conn: DB2Connection, pg_conn: PostgreSQLConnection):
        self.db2_conn = db2_conn
        self.pg_conn = pg_conn
        self.logger = logging.getLogger(__name__)
        
    def get_table_row_count(self, table_name: str, schema: str, connection_type: str) -> int:
        """Get row count for a table"""
        if connection_type == 'db2':
            query = f"SELECT COUNT(*) as count FROM {schema}.{table_name}"
            result = self.db2_conn.execute_query(query)
        else:  # postgresql
            query = f"SELECT COUNT(*) as count FROM {schema}.{table_name}"
            result = self.pg_conn.execute_query(query)
            
        if result and len(result) > 0:
            return result[0]['count'] if 'count' in result[0] else result[0]['COUNT']
        return 0
    
    def compare_row_counts(self, table_name: str, db2_schema: str, pg_schema: str = 'public') -> Dict[str, Any]:
        """Compare row counts between DB2 and PostgreSQL"""
        try:
            db2_count = self.get_table_row_count(table_name, db2_schema, 'db2')
            pg_count = self.get_table_row_count(table_name, pg_schema, 'postgresql')
            
            return {
                'table': table_name,
                'db2_count': db2_count,
                'postgresql_count': pg_count,
                'difference': abs(db2_count - pg_count),
                'match': db2_count == pg_count,
                'percentage_diff': abs(db2_count - pg_count) / max(db2_count, 1) * 100 if db2_count > 0 else 0
            }
        except Exception as e:
            self.logger.error(f"Error comparing row counts for {table_name}: {e}")
            return {
                'table': table_name,
                'error': str(e),
                'match': False
            }
    
    def get_table_sample(self, table_name: str, schema: str, connection_type: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get sample data from a table"""
        if connection_type == 'db2':
            query = f"SELECT * FROM {schema}.{table_name} FETCH FIRST {limit} ROWS ONLY"
            return self.db2_conn.execute_query(query) or []
        else:  # postgresql
            query = f"SELECT * FROM {schema}.{table_name} LIMIT {limit}"
            return self.pg_conn.execute_query(query) or []
    
    def calculate_data_checksum(self, table_name: str, schema: str, connection_type: str, columns: List[str] = None) -> str:
        """Calculate checksum for data comparison"""
        try:
            if columns:
                col_list = ', '.join(columns)
            else:
                col_list = '*'
                
            if connection_type == 'db2':
                query = f"""
                SELECT {col_list} 
                FROM {schema}.{table_name} 
                ORDER BY 1
                """
                results = self.db2_conn.execute_query(query)
            else:  # postgresql
                query = f"""
                SELECT {col_list} 
                FROM {schema}.{table_name} 
                ORDER BY 1
                """
                results = self.pg_conn.execute_query(query)
            
            if not results:
                return ""
            
            # Convert results to string for hashing
            data_string = str(sorted([str(row) for row in results]))
            return hashlib.md5(data_string.encode()).hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error calculating checksum for {table_name}: {e}")
            return ""
    
    def compare_data_checksums(self, table_name: str, db2_schema: str, pg_schema: str = 'public', columns: List[str] = None) -> Dict[str, Any]:
        """Compare data checksums between DB2 and PostgreSQL"""
        try:
            db2_checksum = self.calculate_data_checksum(table_name, db2_schema, 'db2', columns)
            pg_checksum = self.calculate_data_checksum(table_name, pg_schema, 'postgresql', columns)
            
            return {
                'table': table_name,
                'db2_checksum': db2_checksum,
                'postgresql_checksum': pg_checksum,
                'match': db2_checksum == pg_checksum and db2_checksum != "",
                'columns_compared': columns or 'all'
            }
        except Exception as e:
            self.logger.error(f"Error comparing checksums for {table_name}: {e}")
            return {
                'table': table_name,
                'error': str(e),
                'match': False
            }
    
    def validate_primary_keys(self, table_name: str, db2_schema: str, pg_schema: str = 'public') -> Dict[str, Any]:
        """Validate primary key constraints"""
        try:
            # Get DB2 primary key
            db2_pk_query = f"""
            SELECT COLNAME 
            FROM SYSCAT.KEYCOLUSE 
            WHERE TABSCHEMA = '{db2_schema.upper()}' 
            AND TABNAME = '{table_name.upper()}'
            ORDER BY COLSEQ
            """
            db2_pk_results = self.db2_conn.execute_query(db2_pk_query) or []
            db2_pk_cols = [row['colname'].lower() for row in db2_pk_results]
            
            # Get PostgreSQL primary key
            pg_pk_query = f"""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = '{pg_schema}.{table_name}'::regclass
            AND i.indisprimary
            ORDER BY a.attnum
            """
            pg_pk_results = self.pg_conn.execute_query(pg_pk_query) or []
            pg_pk_cols = [row['attname'].lower() for row in pg_pk_results]
            
            return {
                'table': table_name,
                'db2_primary_keys': db2_pk_cols,
                'postgresql_primary_keys': pg_pk_cols,
                'match': set(db2_pk_cols) == set(pg_pk_cols)
            }
            
        except Exception as e:
            self.logger.error(f"Error validating primary keys for {table_name}: {e}")
            return {
                'table': table_name,
                'error': str(e),
                'match': False
            }
    
    def validate_data_types_sample(self, table_name: str, db2_schema: str, pg_schema: str = 'public', sample_size: int = 100) -> Dict[str, Any]:
        """Validate data types by checking sample data"""
        try:
            db2_sample = self.get_table_sample(table_name, db2_schema, 'db2', sample_size)
            pg_sample = self.get_table_sample(table_name, pg_schema, 'postgresql', sample_size)
            
            if not db2_sample or not pg_sample:
                return {
                    'table': table_name,
                    'error': 'No sample data available',
                    'validation_passed': False
                }
            
            # Compare column types in sample data
            db2_cols = set(db2_sample[0].keys()) if db2_sample else set()
            pg_cols = set(pg_sample[0].keys()) if pg_sample else set()
            
            type_issues = []
            
            # Check common columns for type compatibility
            common_cols = db2_cols & pg_cols
            for col in common_cols:
                db2_val = db2_sample[0][col] if db2_sample else None
                pg_val = pg_sample[0][col] if pg_sample else None
                
                if db2_val is not None and pg_val is not None:
                    if type(db2_val) != type(pg_val):
                        type_issues.append({
                            'column': col,
                            'db2_type': type(db2_val).__name__,
                            'postgresql_type': type(pg_val).__name__
                        })
            
            return {
                'table': table_name,
                'sample_size': min(len(db2_sample), len(pg_sample)),
                'type_issues': type_issues,
                'validation_passed': len(type_issues) == 0
            }
            
        except Exception as e:
            self.logger.error(f"Error validating data types for {table_name}: {e}")
            return {
                'table': table_name,
                'error': str(e),
                'validation_passed': False
            }
    
    def comprehensive_data_validation(self, tables: List[str], db2_schema: str, pg_schema: str = 'public') -> Dict[str, Any]:
        """Perform comprehensive data validation"""
        self.logger.info(f"Starting comprehensive data validation for {len(tables)} tables")
        
        results = {
            'row_count_comparisons': [],
            'checksum_comparisons': [],
            'primary_key_validations': [],
            'data_type_validations': [],
            'summary': {}
        }
        
        for table in tables:
            self.logger.info(f"Validating table: {table}")
            
            # Row count comparison
            row_count_result = self.compare_row_counts(table, db2_schema, pg_schema)
            results['row_count_comparisons'].append(row_count_result)
            
            # Checksum comparison
            checksum_result = self.compare_data_checksums(table, db2_schema, pg_schema)
            results['checksum_comparisons'].append(checksum_result)
            
            # Primary key validation
            pk_result = self.validate_primary_keys(table, db2_schema, pg_schema)
            results['primary_key_validations'].append(pk_result)
            
            # Data type validation
            dtype_result = self.validate_data_types_sample(table, db2_schema, pg_schema)
            results['data_type_validations'].append(dtype_result)
        
        # Calculate summary
        total_tables = len(tables)
        row_count_matches = sum(1 for r in results['row_count_comparisons'] if r.get('match', False))
        checksum_matches = sum(1 for r in results['checksum_comparisons'] if r.get('match', False))
        pk_matches = sum(1 for r in results['primary_key_validations'] if r.get('match', False))
        dtype_passes = sum(1 for r in results['data_type_validations'] if r.get('validation_passed', False))
        
        results['summary'] = {
            'total_tables': total_tables,
            'row_count_matches': row_count_matches,
            'checksum_matches': checksum_matches,
            'primary_key_matches': pk_matches,
            'data_type_passes': dtype_passes,
            'overall_success_rate': (row_count_matches + checksum_matches + pk_matches + dtype_passes) / (total_tables * 4) * 100
        }
        
        return results