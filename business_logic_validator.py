import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Callable
import logging
from decimal import Decimal
from datetime import datetime
from db_connection import DB2Connection, PostgreSQLConnection

class BusinessLogicValidator:
    def __init__(self, db2_conn: DB2Connection, pg_conn: PostgreSQLConnection, mapping_config: Dict[str, Any]):
        self.db2_conn = db2_conn
        self.pg_conn = pg_conn
        self.mapping_config = mapping_config
        self.logger = logging.getLogger(__name__)
        
    def execute_mapped_query(self, query_config: Dict[str, Any], params: Dict[str, Any] = None) -> Tuple[List[Dict], List[Dict]]:
        """Execute queries on both databases using mapping configuration"""
        db2_query = query_config['db2_query']
        pg_query = query_config['postgresql_query']
        
        if params:
            # Replace parameters in queries
            for key, value in params.items():
                db2_query = db2_query.replace(f"{{{key}}}", str(value))
                pg_query = pg_query.replace(f"{{{key}}}", str(value))
        
        try:
            db2_results = self.db2_conn.execute_query(db2_query) or []
            pg_results = self.pg_conn.execute_query(pg_query) or []
            
            return db2_results, pg_results
        except Exception as e:
            self.logger.error(f"Error executing mapped queries: {e}")
            return [], []
    
    def normalize_value(self, value: Any, data_type: str = None) -> Any:
        """Normalize values for comparison across different database types"""
        if value is None:
            return None
            
        # Handle different data types
        if data_type == 'decimal' or isinstance(value, (Decimal, float)):
            return float(value) if value is not None else None
        elif data_type == 'integer' or isinstance(value, int):
            return int(value) if value is not None else None
        elif data_type == 'string' or isinstance(value, str):
            return str(value).strip() if value is not None else None
        elif data_type == 'date' or isinstance(value, datetime):
            if isinstance(value, str):
                try:
                    return datetime.strptime(value[:10], '%Y-%m-%d').date()
                except:
                    return value
            return value.date() if hasattr(value, 'date') else value
        
        return value
    
    def validate_contract_integrity(self) -> Dict[str, Any]:
        """Validate contract data integrity between DB2 and PostgreSQL"""
        self.logger.info("Validating contract integrity...")
        
        contract_config = self.mapping_config.get('contract_validation', {})
        if not contract_config:
            return {'error': 'Contract validation configuration not found'}
        
        # Get contract summaries from both databases
        db2_contracts, pg_contracts = self.execute_mapped_query(contract_config['contract_summary'])
        
        if not db2_contracts or not pg_contracts:
            return {'error': 'No contract data found in one or both databases'}
        
        # Create mappings for easy lookup
        db2_contract_map = {}
        pg_contract_map = {}
        
        # Map DB2 contracts
        for contract in db2_contracts:
            contract_key = self.normalize_value(contract[contract_config['db2_key_field']], 'string')
            db2_contract_map[contract_key] = {
                'contract_number': contract_key,
                'balance': self.normalize_value(contract[contract_config['db2_balance_field']], 'decimal'),
                'status': self.normalize_value(contract.get(contract_config['db2_status_field']), 'string'),
                'create_date': self.normalize_value(contract.get(contract_config['db2_date_field']), 'date')
            }
        
        # Map PostgreSQL contracts
        for contract in pg_contracts:
            contract_key = self.normalize_value(contract[contract_config['pg_key_field']], 'string')
            pg_contract_map[contract_key] = {
                'contract_number': contract_key,
                'balance': self.normalize_value(contract[contract_config['pg_balance_field']], 'decimal'),
                'status': self.normalize_value(contract.get(contract_config['pg_status_field']), 'string'),
                'create_date': self.normalize_value(contract.get(contract_config['pg_date_field']), 'date')
            }
        
        # Compare contracts
        validation_results = {
            'total_db2_contracts': len(db2_contract_map),
            'total_pg_contracts': len(pg_contract_map),
            'missing_in_postgresql': [],
            'missing_in_db2': [],
            'balance_mismatches': [],
            'status_mismatches': [],
            'date_mismatches': [],
            'perfect_matches': 0
        }
        
        # Check for missing contracts
        db2_keys = set(db2_contract_map.keys())
        pg_keys = set(pg_contract_map.keys())
        
        validation_results['missing_in_postgresql'] = list(db2_keys - pg_keys)
        validation_results['missing_in_db2'] = list(pg_keys - db2_keys)
        
        # Compare common contracts
        common_keys = db2_keys & pg_keys
        tolerance = contract_config.get('balance_tolerance', 0.01)  # Default tolerance for decimal comparison
        
        for contract_key in common_keys:
            db2_contract = db2_contract_map[contract_key]
            pg_contract = pg_contract_map[contract_key]
            
            has_issues = False
            
            # Compare balance
            db2_balance = db2_contract['balance']
            pg_balance = pg_contract['balance']
            
            if db2_balance is not None and pg_balance is not None:
                if abs(float(db2_balance) - float(pg_balance)) > tolerance:
                    validation_results['balance_mismatches'].append({
                        'contract_number': contract_key,
                        'db2_balance': db2_balance,
                        'postgresql_balance': pg_balance,
                        'difference': abs(float(db2_balance) - float(pg_balance))
                    })
                    has_issues = True
            elif db2_balance != pg_balance:  # One is None, other is not
                validation_results['balance_mismatches'].append({
                    'contract_number': contract_key,
                    'db2_balance': db2_balance,
                    'postgresql_balance': pg_balance,
                    'difference': 'NULL_MISMATCH'
                })
                has_issues = True
            
            # Compare status
            if db2_contract['status'] != pg_contract['status']:
                validation_results['status_mismatches'].append({
                    'contract_number': contract_key,
                    'db2_status': db2_contract['status'],
                    'postgresql_status': pg_contract['status']
                })
                has_issues = True
            
            # Compare dates
            if db2_contract['create_date'] != pg_contract['create_date']:
                validation_results['date_mismatches'].append({
                    'contract_number': contract_key,
                    'db2_date': db2_contract['create_date'],
                    'postgresql_date': pg_contract['create_date']
                })
                has_issues = True
            
            if not has_issues:
                validation_results['perfect_matches'] += 1
        
        # Calculate summary statistics
        total_common = len(common_keys)
        validation_results['summary'] = {
            'total_compared': total_common,
            'perfect_matches': validation_results['perfect_matches'],
            'contracts_with_issues': total_common - validation_results['perfect_matches'],
            'success_rate': (validation_results['perfect_matches'] / total_common * 100) if total_common > 0 else 0,
            'migration_completeness': (len(pg_keys) / len(db2_keys) * 100) if len(db2_keys) > 0 else 0
        }
        
        return validation_results
    
    def validate_customer_data(self) -> Dict[str, Any]:
        """Validate customer data integrity"""
        self.logger.info("Validating customer data...")
        
        customer_config = self.mapping_config.get('customer_validation', {})
        if not customer_config:
            return {'error': 'Customer validation configuration not found'}
        
        db2_customers, pg_customers = self.execute_mapped_query(customer_config['customer_summary'])
        
        # Similar logic to contract validation but for customer data
        validation_results = {
            'total_db2_customers': len(db2_customers),
            'total_pg_customers': len(pg_customers),
            'missing_customers': [],
            'data_mismatches': [],
            'perfect_matches': 0
        }
        
        # Create customer maps
        db2_customer_map = {
            self.normalize_value(cust[customer_config['db2_key_field']], 'string'): cust 
            for cust in db2_customers
        }
        
        pg_customer_map = {
            self.normalize_value(cust[customer_config['pg_key_field']], 'string'): cust 
            for cust in pg_customers
        }
        
        # Compare customers
        db2_keys = set(db2_customer_map.keys())
        pg_keys = set(pg_customer_map.keys())
        
        validation_results['missing_customers'] = list(db2_keys - pg_keys)
        common_keys = db2_keys & pg_keys
        
        # Compare customer fields
        compare_fields = customer_config.get('compare_fields', [])
        
        for customer_key in common_keys:
            db2_customer = db2_customer_map[customer_key]
            pg_customer = pg_customer_map[customer_key]
            
            mismatches = []
            
            for field_config in compare_fields:
                db2_field = field_config['db2_field']
                pg_field = field_config['pg_field']
                field_type = field_config.get('type', 'string')
                
                db2_value = self.normalize_value(db2_customer.get(db2_field), field_type)
                pg_value = self.normalize_value(pg_customer.get(pg_field), field_type)
                
                if db2_value != pg_value:
                    mismatches.append({
                        'field': field_config.get('name', db2_field),
                        'db2_value': db2_value,
                        'postgresql_value': pg_value
                    })
            
            if mismatches:
                validation_results['data_mismatches'].append({
                    'customer_id': customer_key,
                    'mismatches': mismatches
                })
            else:
                validation_results['perfect_matches'] += 1
        
        # Calculate summary
        total_common = len(common_keys)
        validation_results['summary'] = {
            'total_compared': total_common,
            'perfect_matches': validation_results['perfect_matches'],
            'customers_with_issues': len(validation_results['data_mismatches']),
            'success_rate': (validation_results['perfect_matches'] / total_common * 100) if total_common > 0 else 0
        }
        
        return validation_results
    
    def validate_aggregated_totals(self) -> Dict[str, Any]:
        """Validate aggregated totals between databases"""
        self.logger.info("Validating aggregated totals...")
        
        aggregate_config = self.mapping_config.get('aggregate_validation', {})
        if not aggregate_config:
            return {'error': 'Aggregate validation configuration not found'}
        
        validation_results = {}
        
        for validation_name, config in aggregate_config.items():
            self.logger.info(f"Validating aggregate: {validation_name}")
            
            db2_result, pg_result = self.execute_mapped_query(config)
            
            if not db2_result or not pg_result:
                validation_results[validation_name] = {
                    'error': 'No data returned from one or both databases'
                }
                continue
            
            # Extract values
            db2_total = self.normalize_value(db2_result[0][config['db2_result_field']], 'decimal')
            pg_total = self.normalize_value(pg_result[0][config['pg_result_field']], 'decimal')
            
            tolerance = config.get('tolerance', 0.01)
            difference = abs(float(db2_total or 0) - float(pg_total or 0)) if db2_total and pg_total else None
            
            validation_results[validation_name] = {
                'db2_total': db2_total,
                'postgresql_total': pg_total,
                'difference': difference,
                'tolerance': tolerance,
                'within_tolerance': difference <= tolerance if difference is not None else False,
                'match': db2_total == pg_total if db2_total is not None and pg_total is not None else False
            }
        
        return validation_results
    
    def run_custom_validation_rules(self) -> Dict[str, Any]:
        """Run custom business validation rules"""
        self.logger.info("Running custom validation rules...")
        
        custom_rules = self.mapping_config.get('custom_rules', {})
        validation_results = {}
        
        for rule_name, rule_config in custom_rules.items():
            self.logger.info(f"Running custom rule: {rule_name}")
            
            try:
                # Execute rule queries
                db2_result, pg_result = self.execute_mapped_query(rule_config)
                
                # Apply rule logic
                rule_type = rule_config.get('type', 'count_match')
                
                if rule_type == 'count_match':
                    db2_count = len(db2_result)
                    pg_count = len(pg_result)
                    
                    validation_results[rule_name] = {
                        'type': 'count_match',
                        'db2_count': db2_count,
                        'postgresql_count': pg_count,
                        'match': db2_count == pg_count,
                        'difference': abs(db2_count - pg_count)
                    }
                
                elif rule_type == 'sum_match':
                    db2_field = rule_config['db2_sum_field']
                    pg_field = rule_config['pg_sum_field']
                    
                    db2_sum = sum(self.normalize_value(row[db2_field], 'decimal') or 0 for row in db2_result)
                    pg_sum = sum(self.normalize_value(row[pg_field], 'decimal') or 0 for row in pg_result)
                    
                    tolerance = rule_config.get('tolerance', 0.01)
                    difference = abs(float(db2_sum) - float(pg_sum))
                    
                    validation_results[rule_name] = {
                        'type': 'sum_match',
                        'db2_sum': db2_sum,
                        'postgresql_sum': pg_sum,
                        'difference': difference,
                        'tolerance': tolerance,
                        'within_tolerance': difference <= tolerance
                    }
                
            except Exception as e:
                self.logger.error(f"Error running custom rule {rule_name}: {e}")
                validation_results[rule_name] = {
                    'error': str(e)
                }
        
        return validation_results
    
    def comprehensive_business_validation(self) -> Dict[str, Any]:
        """Run comprehensive business logic validation"""
        self.logger.info("Starting comprehensive business validation...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'contract_validation': {},
            'customer_validation': {},
            'aggregate_validation': {},
            'custom_rules': {},
            'summary': {}
        }
        
        try:
            # Run contract validation
            if 'contract_validation' in self.mapping_config:
                results['contract_validation'] = self.validate_contract_integrity()
            
            # Run customer validation
            if 'customer_validation' in self.mapping_config:
                results['customer_validation'] = self.validate_customer_data()
            
            # Run aggregate validation
            if 'aggregate_validation' in self.mapping_config:
                results['aggregate_validation'] = self.validate_aggregated_totals()
            
            # Run custom rules
            if 'custom_rules' in self.mapping_config:
                results['custom_rules'] = self.run_custom_validation_rules()
            
            # Calculate overall summary
            total_validations = 0
            passed_validations = 0
            
            # Count contract validation results
            if results['contract_validation'] and 'summary' in results['contract_validation']:
                total_validations += 1
                if results['contract_validation']['summary']['success_rate'] >= 95:  # 95% threshold
                    passed_validations += 1
            
            # Count customer validation results
            if results['customer_validation'] and 'summary' in results['customer_validation']:
                total_validations += 1
                if results['customer_validation']['summary']['success_rate'] >= 95:
                    passed_validations += 1
            
            # Count aggregate validations
            for agg_name, agg_result in results['aggregate_validation'].items():
                if 'error' not in agg_result:
                    total_validations += 1
                    if agg_result.get('within_tolerance', False) or agg_result.get('match', False):
                        passed_validations += 1
            
            # Count custom rules
            for rule_name, rule_result in results['custom_rules'].items():
                if 'error' not in rule_result:
                    total_validations += 1
                    if rule_result.get('match', False) or rule_result.get('within_tolerance', False):
                        passed_validations += 1
            
            results['summary'] = {
                'total_validations': total_validations,
                'passed_validations': passed_validations,
                'overall_success_rate': (passed_validations / total_validations * 100) if total_validations > 0 else 0,
                'validation_status': 'PASSED' if passed_validations == total_validations else 'FAILED'
            }
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive business validation: {e}")
            results['error'] = str(e)
        
        return results