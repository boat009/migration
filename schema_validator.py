import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import logging
from db_connection import DB2Connection, PostgreSQLConnection

class SchemaValidator:
    def __init__(self, db2_conn: DB2Connection, pg_conn: PostgreSQLConnection):
        self.db2_conn = db2_conn
        self.pg_conn = pg_conn
        self.logger = logging.getLogger(__name__)
        
    def get_db2_tables(self, schema: str = None) -> List[Dict[str, Any]]:
        """Get list of tables from DB2"""
        query = """
        SELECT TABSCHEMA, TABNAME, TYPE, REMARKS
        FROM SYSCAT.TABLES 
        WHERE TYPE IN ('T', 'V')
        """
        if schema:
            query += f" AND TABSCHEMA = '{schema.upper()}'"
        query += " ORDER BY TABSCHEMA, TABNAME"
        
        return self.db2_conn.execute_query(query) or []
    
    def get_postgresql_tables(self, schema: str = 'public') -> List[Dict[str, Any]]:
        """Get list of tables from PostgreSQL"""
        query = """
        SELECT schemaname, tablename, tableowner
        FROM pg_tables 
        WHERE schemaname = %s
        ORDER BY schemaname, tablename
        """
        
        # Convert to format similar to DB2 results
        results = []
        pg_results = self.pg_conn.execute_query(query.replace('%s', f"'{schema}'"))
        
        if pg_results:
            for row in pg_results:
                results.append({
                    'tabschema': row['schemaname'],
                    'tabname': row['tablename'],
                    'type': 'T',  # Table
                    'remarks': None
                })
        
        return results
    
    def get_db2_columns(self, schema: str, table: str) -> List[Dict[str, Any]]:
        """Get column information from DB2"""
        query = f"""
        SELECT 
            COLNAME, 
            TYPENAME, 
            LENGTH, 
            SCALE, 
            NULLS,
            DEFAULT,
            COLNO
        FROM SYSCAT.COLUMNS 
        WHERE TABSCHEMA = '{schema.upper()}' 
        AND TABNAME = '{table.upper()}'
        ORDER BY COLNO
        """
        
        return self.db2_conn.execute_query(query) or []
    
    def get_postgresql_columns(self, schema: str, table: str) -> List[Dict[str, Any]]:
        """Get column information from PostgreSQL"""
        query = f"""
        SELECT 
            column_name, 
            data_type, 
            character_maximum_length, 
            numeric_precision,
            numeric_scale,
            is_nullable,
            column_default,
            ordinal_position
        FROM information_schema.columns 
        WHERE table_schema = '{schema}' 
        AND table_name = '{table}'
        ORDER BY ordinal_position
        """
        
        # Convert to format similar to DB2 results
        results = []
        pg_results = self.pg_conn.execute_query(query)
        
        if pg_results:
            for row in pg_results:
                results.append({
                    'colname': row['column_name'],
                    'typename': row['data_type'],
                    'length': row['character_maximum_length'] or row['numeric_precision'],
                    'scale': row['numeric_scale'],
                    'nulls': 'Y' if row['is_nullable'] == 'YES' else 'N',
                    'default': row['column_default'],
                    'colno': row['ordinal_position']
                })
        
        return results
    
    def get_db2_indexes(self, schema: str, table: str) -> List[Dict[str, Any]]:
        """Get index information from DB2"""
        query = f"""
        SELECT 
            i.INDNAME,
            i.UNIQUERULE,
            ic.COLNAME,
            ic.COLSEQ
        FROM SYSCAT.INDEXES i
        JOIN SYSCAT.INDEXCOLUSE ic ON i.INDNAME = ic.INDNAME
        WHERE i.TABSCHEMA = '{schema.upper()}'
        AND i.TABNAME = '{table.upper()}'
        ORDER BY i.INDNAME, ic.COLSEQ
        """
        
        return self.db2_conn.execute_query(query) or []
    
    def get_postgresql_indexes(self, schema: str, table: str) -> List[Dict[str, Any]]:
        """Get index information from PostgreSQL"""
        query = f"""
        SELECT 
            indexname,
            indexdef
        FROM pg_indexes 
        WHERE schemaname = '{schema}' 
        AND tablename = '{table}'
        """
        
        return self.pg_conn.execute_query(query) or []
    
    def compare_tables(self, db2_schema: str, pg_schema: str = 'public') -> Dict[str, Any]:
        """Compare tables between DB2 and PostgreSQL"""
        db2_tables = {t['tabname'].lower() for t in self.get_db2_tables(db2_schema)}
        pg_tables = {t['tabname'].lower() for t in self.get_postgresql_tables(pg_schema)}
        
        return {
            'db2_only': db2_tables - pg_tables,
            'postgresql_only': pg_tables - db2_tables,
            'common': db2_tables & pg_tables,
            'db2_total': len(db2_tables),
            'postgresql_total': len(pg_tables)
        }
    
    def compare_table_schema(self, table_name: str, db2_schema: str, pg_schema: str = 'public') -> Dict[str, Any]:
        """Compare schema of a specific table"""
        db2_cols = self.get_db2_columns(db2_schema, table_name)
        pg_cols = self.get_postgresql_columns(pg_schema, table_name)
        
        # Create column mappings
        db2_col_map = {col['colname'].lower(): col for col in db2_cols}
        pg_col_map = {col['colname'].lower(): col for col in pg_cols}
        
        db2_col_names = set(db2_col_map.keys())
        pg_col_names = set(pg_col_map.keys())
        
        differences = []
        
        # Check for missing columns
        for col in db2_col_names - pg_col_names:
            differences.append({
                'type': 'missing_in_postgresql',
                'column': col,
                'db2_info': db2_col_map[col]
            })
            
        for col in pg_col_names - db2_col_names:
            differences.append({
                'type': 'missing_in_db2',
                'column': col,
                'postgresql_info': pg_col_map[col]
            })
        
        # Check for data type differences in common columns
        for col in db2_col_names & pg_col_names:
            db2_col = db2_col_map[col]
            pg_col = pg_col_map[col]
            
            if self._normalize_data_type(db2_col['typename']) != self._normalize_data_type(pg_col['typename']):
                differences.append({
                    'type': 'data_type_mismatch',
                    'column': col,
                    'db2_type': db2_col['typename'],
                    'postgresql_type': pg_col['typename']
                })
        
        return {
            'table': table_name,
            'differences': differences,
            'db2_columns': len(db2_cols),
            'postgresql_columns': len(pg_cols)
        }
    
    def _normalize_data_type(self, data_type: str) -> str:
        """Normalize data types for comparison"""
        type_mapping = {
            'INTEGER': 'integer',
            'BIGINT': 'bigint',
            'SMALLINT': 'smallint',
            'DECIMAL': 'numeric',
            'DOUBLE': 'double precision',
            'REAL': 'real',
            'VARCHAR': 'character varying',
            'CHARACTER': 'character',
            'CHAR': 'character',
            'CLOB': 'text',
            'DATE': 'date',
            'TIME': 'time without time zone',
            'TIMESTAMP': 'timestamp without time zone'
        }
        
        return type_mapping.get(data_type.upper(), data_type.lower())
    
    def validate_schema_migration(self, db2_schema: str, pg_schema: str = 'public') -> Dict[str, Any]:
        """Complete schema validation between DB2 and PostgreSQL"""
        self.logger.info(f"Starting schema validation: DB2({db2_schema}) -> PostgreSQL({pg_schema})")
        
        # Compare tables
        table_comparison = self.compare_tables(db2_schema, pg_schema)
        
        # Compare schema for common tables
        table_schema_comparisons = []
        for table in table_comparison['common']:
            schema_comp = self.compare_table_schema(table, db2_schema, pg_schema)
            if schema_comp['differences']:
                table_schema_comparisons.append(schema_comp)
        
        return {
            'table_comparison': table_comparison,
            'schema_differences': table_schema_comparisons,
            'summary': {
                'tables_migrated': len(table_comparison['common']),
                'tables_missing': len(table_comparison['db2_only']),
                'tables_with_schema_issues': len(table_schema_comparisons)
            }
        }