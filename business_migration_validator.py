#!/usr/bin/env python3
"""
Business Logic Migration Validator

ตรวจสอบการ migrate ข้อมูลโดยใช้ business logic แทนการเปรียบเทียบ schema ตรง ๆ
เหมาะสำหรับกรณีที่ table และ column ชื่อไม่เหมือนกัน แต่ต้องการตรวจสอบความถูกต้องของข้อมูล

Usage:
    python business_migration_validator.py --config config.yaml --mapping business_mapping.yaml
    python business_migration_validator.py --config config.yaml --mapping business_mapping.yaml --contracts-only
    python business_migration_validator.py --config config.yaml --mapping business_mapping.yaml --aggregates-only
"""

import argparse
import yaml
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List
from db_connection import DB2Connection, PostgreSQLConnection
from business_logic_validator import BusinessLogicValidator
from report_generator import ReportGenerator

class BusinessMigrationValidator:
    def __init__(self, config: Dict[str, Any], mapping_config: Dict[str, Any]):
        self.config = config
        self.mapping_config = mapping_config
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize connections
        self.db2_conn = DB2Connection(config['db2'])
        self.pg_conn = PostgreSQLConnection(config['postgresql'])
        
        # Initialize business logic validator
        self.business_validator = BusinessLogicValidator(self.db2_conn, self.pg_conn, mapping_config)
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
                logging.FileHandler('business_migration_validation.log')
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
    
    def run_contract_validation(self) -> Dict[str, Any]:
        """Run contract validation only"""
        self.logger.info("Running contract validation...")
        
        try:
            contract_results = self.business_validator.validate_contract_integrity()
            self.logger.info("Contract validation completed")
            return contract_results
        except Exception as e:
            self.logger.error(f"Contract validation failed: {e}")
            raise
    
    def run_customer_validation(self) -> Dict[str, Any]:
        """Run customer validation only"""
        self.logger.info("Running customer validation...")
        
        try:
            customer_results = self.business_validator.validate_customer_data()
            self.logger.info("Customer validation completed")
            return customer_results
        except Exception as e:
            self.logger.error(f"Customer validation failed: {e}")
            raise
    
    def run_aggregate_validation(self) -> Dict[str, Any]:
        """Run aggregate validation only"""
        self.logger.info("Running aggregate validation...")
        
        try:
            aggregate_results = self.business_validator.validate_aggregated_totals()
            self.logger.info("Aggregate validation completed")
            return aggregate_results
        except Exception as e:
            self.logger.error(f"Aggregate validation failed: {e}")
            raise
    
    def run_custom_rules(self) -> Dict[str, Any]:
        """Run custom business rules only"""
        self.logger.info("Running custom business rules...")
        
        try:
            custom_results = self.business_validator.run_custom_validation_rules()
            self.logger.info("Custom rules validation completed")
            return custom_results
        except Exception as e:
            self.logger.error(f"Custom rules validation failed: {e}")
            raise
    
    def generate_business_report(self, results: Dict[str, Any]) -> Dict[str, str]:
        """Generate business validation report"""
        self.logger.info("Generating business validation reports...")
        
        output_dir = Path(self.config.get('output', {}).get('directory', './reports'))
        output_dir.mkdir(exist_ok=True)
        
        base_filename = output_dir / 'business_validation'
        
        try:
            # Generate console report
            console_report = self.generate_console_business_report(results)
            
            # Save JSON report
            json_file = f"{base_filename}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
            # Generate HTML report
            html_report = self.generate_html_business_report(results)
            html_file = f"{base_filename}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_report)
            
            # Generate Excel report
            self.generate_excel_business_report(results, f"{base_filename}.xlsx")
            
            # Print console report
            if self.config.get('output', {}).get('console', True):
                print(console_report)
            
            self.logger.info("Business validation reports generated successfully")
            return {
                'console': console_report,
                'json': json_file,
                'html': html_file,
                'excel': f"{base_filename}.xlsx"
            }
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            raise
    
    def generate_console_business_report(self, results: Dict[str, Any]) -> str:
        """Generate console report for business validation"""
        from colorama import Fore, Style, init
        init(autoreset=True)
        
        report = []
        report.append(f"\n{Fore.CYAN}{'='*80}")
        report.append(f"{Fore.CYAN}BUSINESS LOGIC MIGRATION VALIDATION REPORT")
        report.append(f"{Fore.CYAN}Generated: {results.get('timestamp', 'N/A')}")
        report.append(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        
        # Overall Summary
        if 'summary' in results:
            summary = results['summary']
            report.append(f"\n{Fore.YELLOW}OVERALL SUMMARY{Style.RESET_ALL}")
            report.append("-" * 40)
            report.append(f"Total Validations: {summary['total_validations']}")
            report.append(f"Passed Validations: {Fore.GREEN}{summary['passed_validations']}{Style.RESET_ALL}")
            report.append(f"Overall Success Rate: {Fore.GREEN if summary['overall_success_rate'] >= 95 else Fore.RED}{summary['overall_success_rate']:.1f}%{Style.RESET_ALL}")
            report.append(f"Validation Status: {Fore.GREEN if summary['validation_status'] == 'PASSED' else Fore.RED}{summary['validation_status']}{Style.RESET_ALL}")
        
        # Contract Validation
        if 'contract_validation' in results and results['contract_validation']:
            contract_data = results['contract_validation']
            report.append(f"\n{Fore.YELLOW}CONTRACT VALIDATION{Style.RESET_ALL}")
            report.append("-" * 40)
            
            if 'summary' in contract_data:
                summary = contract_data['summary']
                report.append(f"Total Contracts Compared: {summary['total_compared']}")
                report.append(f"Perfect Matches: {Fore.GREEN}{summary['perfect_matches']}{Style.RESET_ALL}")
                report.append(f"Success Rate: {Fore.GREEN if summary['success_rate'] >= 95 else Fore.RED}{summary['success_rate']:.1f}%{Style.RESET_ALL}")
                report.append(f"Migration Completeness: {summary['migration_completeness']:.1f}%")
            
            # Balance mismatches
            if contract_data.get('balance_mismatches'):
                report.append(f"\n{Fore.RED}Balance Mismatches ({len(contract_data['balance_mismatches'])}):{Style.RESET_ALL}")
                for mismatch in contract_data['balance_mismatches'][:5]:  # Show first 5
                    report.append(f"  Contract {mismatch['contract_number']}: DB2={mismatch['db2_balance']}, PG={mismatch['postgresql_balance']}")
                if len(contract_data['balance_mismatches']) > 5:
                    report.append(f"  ... and {len(contract_data['balance_mismatches']) - 5} more")
            
            # Missing contracts
            if contract_data.get('missing_in_postgresql'):
                report.append(f"\n{Fore.RED}Missing in PostgreSQL ({len(contract_data['missing_in_postgresql'])}):{Style.RESET_ALL}")
                for contract in contract_data['missing_in_postgresql'][:5]:
                    report.append(f"  - {contract}")
        
        # Customer Validation
        if 'customer_validation' in results and results['customer_validation']:
            customer_data = results['customer_validation']
            report.append(f"\n{Fore.YELLOW}CUSTOMER VALIDATION{Style.RESET_ALL}")
            report.append("-" * 40)
            
            if 'summary' in customer_data:
                summary = customer_data['summary']
                report.append(f"Total Customers Compared: {summary['total_compared']}")
                report.append(f"Perfect Matches: {Fore.GREEN}{summary['perfect_matches']}{Style.RESET_ALL}")
                report.append(f"Success Rate: {Fore.GREEN if summary['success_rate'] >= 95 else Fore.RED}{summary['success_rate']:.1f}%{Style.RESET_ALL}")
        
        # Aggregate Validation
        if 'aggregate_validation' in results and results['aggregate_validation']:
            report.append(f"\n{Fore.YELLOW}AGGREGATE VALIDATION{Style.RESET_ALL}")
            report.append("-" * 40)
            
            for agg_name, agg_data in results['aggregate_validation'].items():
                if 'error' in agg_data:
                    report.append(f"{agg_name}: {Fore.RED}ERROR - {agg_data['error']}{Style.RESET_ALL}")
                else:
                    status = Fore.GREEN + "PASS" if agg_data.get('within_tolerance', agg_data.get('match', False)) else Fore.RED + "FAIL"
                    report.append(f"{agg_name}: {status}{Style.RESET_ALL}")
                    if 'difference' in agg_data and agg_data['difference'] is not None:
                        report.append(f"  DB2: {agg_data.get('db2_total', 'N/A')}, PG: {agg_data.get('postgresql_total', 'N/A')}, Diff: {agg_data['difference']}")
        
        # Custom Rules
        if 'custom_rules' in results and results['custom_rules']:
            report.append(f"\n{Fore.YELLOW}CUSTOM BUSINESS RULES{Style.RESET_ALL}")
            report.append("-" * 40)
            
            for rule_name, rule_data in results['custom_rules'].items():
                if 'error' in rule_data:
                    report.append(f"{rule_name}: {Fore.RED}ERROR - {rule_data['error']}{Style.RESET_ALL}")
                else:
                    status = Fore.GREEN + "PASS" if rule_data.get('match', rule_data.get('within_tolerance', False)) else Fore.RED + "FAIL"
                    report.append(f"{rule_name}: {status}{Style.RESET_ALL}")
        
        report.append(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        
        return '\n'.join(report)
    
    def generate_html_business_report(self, results: Dict[str, Any]) -> str:
        """Generate HTML report for business validation"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Business Logic Migration Validation Report</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px; }}
                .section {{ margin: 20px 0; padding: 20px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .success {{ color: #27ae60; font-weight: bold; }}
                .warning {{ color: #f39c12; font-weight: bold; }}
                .error {{ color: #e74c3c; font-weight: bold; }}
                table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f8f9fa; font-weight: bold; }}
                .summary-box {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 20px; border-radius: 10px; margin: 15px 0; }}
                .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
                .metric-value {{ font-size: 24px; font-weight: bold; }}
                .metric-label {{ font-size: 12px; opacity: 0.9; }}
                .status-pass {{ background-color: #d4edda; color: #155724; padding: 5px 10px; border-radius: 5px; }}
                .status-fail {{ background-color: #f8d7da; color: #721c24; padding: 5px 10px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏦 Business Logic Migration Validation Report</h1>
                <p>Generated: {results.get('timestamp', 'N/A')}</p>
            </div>
        """
        
        # Overall Summary Section
        if 'summary' in results:
            summary = results['summary']
            html_content += f"""
            <div class="section">
                <h2>📊 Overall Summary</h2>
                <div class="summary-box">
                    <div class="metric">
                        <div class="metric-value">{summary['total_validations']}</div>
                        <div class="metric-label">Total Validations</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{summary['passed_validations']}</div>
                        <div class="metric-label">Passed</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{summary['overall_success_rate']:.1f}%</div>
                        <div class="metric-label">Success Rate</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value {'success' if summary['validation_status'] == 'PASSED' else 'error'}">{summary['validation_status']}</div>
                        <div class="metric-label">Status</div>
                    </div>
                </div>
            </div>
            """
        
        # Contract Validation Section
        if 'contract_validation' in results and results['contract_validation']:
            contract_data = results['contract_validation']
            html_content += """
            <div class="section">
                <h2>📋 Contract Validation</h2>
            """
            
            if 'summary' in contract_data:
                summary = contract_data['summary']
                html_content += f"""
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>Total Contracts Compared</td><td>{summary['total_compared']}</td></tr>
                    <tr><td>Perfect Matches</td><td><span class="success">{summary['perfect_matches']}</span></td></tr>
                    <tr><td>Contracts with Issues</td><td><span class="{'warning' if summary['contracts_with_issues'] > 0 else 'success'}">{summary['contracts_with_issues']}</span></td></tr>
                    <tr><td>Success Rate</td><td><span class="{'success' if summary['success_rate'] >= 95 else 'error'}">{summary['success_rate']:.1f}%</span></td></tr>
                    <tr><td>Migration Completeness</td><td>{summary['migration_completeness']:.1f}%</td></tr>
                </table>
                """
            
            # Balance Mismatches Table
            if contract_data.get('balance_mismatches'):
                html_content += f"""
                <h3>💰 Balance Mismatches ({len(contract_data['balance_mismatches'])})</h3>
                <table>
                    <tr><th>Contract Number</th><th>DB2 Balance</th><th>PostgreSQL Balance</th><th>Difference</th></tr>
                """
                
                for mismatch in contract_data['balance_mismatches'][:20]:  # Show first 20
                    html_content += f"""
                    <tr>
                        <td>{mismatch['contract_number']}</td>
                        <td>{mismatch['db2_balance']}</td>
                        <td>{mismatch['postgresql_balance']}</td>
                        <td><span class="error">{mismatch['difference']}</span></td>
                    </tr>
                    """
                
                html_content += "</table>"
            
            html_content += "</div>"
        
        # Customer Validation Section
        if 'customer_validation' in results and results['customer_validation']:
            customer_data = results['customer_validation']
            html_content += """
            <div class="section">
                <h2>👥 Customer Validation</h2>
            """
            
            if 'summary' in customer_data:
                summary = customer_data['summary']
                html_content += f"""
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>Total Customers Compared</td><td>{summary['total_compared']}</td></tr>
                    <tr><td>Perfect Matches</td><td><span class="success">{summary['perfect_matches']}</span></td></tr>
                    <tr><td>Customers with Issues</td><td><span class="{'warning' if summary['customers_with_issues'] > 0 else 'success'}">{summary['customers_with_issues']}</span></td></tr>
                    <tr><td>Success Rate</td><td><span class="{'success' if summary['success_rate'] >= 95 else 'error'}">{summary['success_rate']:.1f}%</span></td></tr>
                </table>
                """
            
            html_content += "</div>"
        
        # Aggregate Validation Section
        if 'aggregate_validation' in results and results['aggregate_validation']:
            html_content += """
            <div class="section">
                <h2>📈 Aggregate Validation</h2>
                <table>
                    <tr><th>Validation</th><th>DB2 Total</th><th>PostgreSQL Total</th><th>Difference</th><th>Status</th></tr>
            """
            
            for agg_name, agg_data in results['aggregate_validation'].items():
                if 'error' in agg_data:
                    status = f'<span class="status-fail">ERROR</span>'
                    db2_total = 'N/A'
                    pg_total = 'N/A'
                    difference = agg_data['error']
                else:
                    status_ok = agg_data.get('within_tolerance', agg_data.get('match', False))
                    status = f'<span class="status-{"pass" if status_ok else "fail"}">{"PASS" if status_ok else "FAIL"}</span>'
                    db2_total = agg_data.get('db2_total', 'N/A')
                    pg_total = agg_data.get('postgresql_total', 'N/A')
                    difference = agg_data.get('difference', 'N/A')
                
                html_content += f"""
                <tr>
                    <td>{agg_name.replace('_', ' ').title()}</td>
                    <td>{db2_total}</td>
                    <td>{pg_total}</td>
                    <td>{difference}</td>
                    <td>{status}</td>
                </tr>
                """
            
            html_content += "</table></div>"
        
        # Custom Rules Section
        if 'custom_rules' in results and results['custom_rules']:
            html_content += """
            <div class="section">
                <h2>⚙️ Custom Business Rules</h2>
                <table>
                    <tr><th>Rule Name</th><th>Type</th><th>Result</th><th>Status</th></tr>
            """
            
            for rule_name, rule_data in results['custom_rules'].items():
                if 'error' in rule_data:
                    status = f'<span class="status-fail">ERROR</span>'
                    result = rule_data['error']
                    rule_type = 'N/A'
                else:
                    status_ok = rule_data.get('match', rule_data.get('within_tolerance', False))
                    status = f'<span class="status-{"pass" if status_ok else "fail"}">{"PASS" if status_ok else "FAIL"}</span>'
                    rule_type = rule_data.get('type', 'custom')
                    
                    if rule_type == 'count_match':
                        result = f"DB2: {rule_data.get('db2_count', 'N/A')}, PG: {rule_data.get('postgresql_count', 'N/A')}"
                    elif rule_type == 'sum_match':
                        result = f"DB2: {rule_data.get('db2_sum', 'N/A')}, PG: {rule_data.get('postgresql_sum', 'N/A')}"
                    else:
                        result = "Custom validation"
                
                html_content += f"""
                <tr>
                    <td>{rule_name.replace('_', ' ').title()}</td>
                    <td>{rule_type}</td>
                    <td>{result}</td>
                    <td>{status}</td>
                </tr>
                """
            
            html_content += "</table></div>"
        
        html_content += "</body></html>"
        return html_content
    
    def generate_excel_business_report(self, results: Dict[str, Any], filename: str) -> None:
        """Generate Excel report for business validation"""
        import pandas as pd
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = []
            
            if 'summary' in results:
                summary = results['summary']
                summary_data = [
                    ['Overall Summary', ''],
                    ['Total Validations', summary['total_validations']],
                    ['Passed Validations', summary['passed_validations']],
                    ['Overall Success Rate (%)', f"{summary['overall_success_rate']:.1f}"],
                    ['Validation Status', summary['validation_status']],
                ]
            
            summary_df = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Contract validation details
            if 'contract_validation' in results and results['contract_validation']:
                contract_data = results['contract_validation']
                
                # Balance mismatches
                if contract_data.get('balance_mismatches'):
                    balance_df = pd.DataFrame(contract_data['balance_mismatches'])
                    balance_df.to_excel(writer, sheet_name='Balance Mismatches', index=False)
                
                # Missing contracts
                if contract_data.get('missing_in_postgresql'):
                    missing_df = pd.DataFrame(contract_data['missing_in_postgresql'], columns=['Missing Contracts'])
                    missing_df.to_excel(writer, sheet_name='Missing Contracts', index=False)
            
            # Aggregate validation
            if 'aggregate_validation' in results and results['aggregate_validation']:
                agg_data = []
                for name, data in results['aggregate_validation'].items():
                    agg_data.append({
                        'Validation': name,
                        'DB2 Total': data.get('db2_total', 'N/A'),
                        'PostgreSQL Total': data.get('postgresql_total', 'N/A'),
                        'Difference': data.get('difference', 'N/A'),
                        'Status': 'PASS' if data.get('within_tolerance', data.get('match', False)) else 'FAIL'
                    })
                
                if agg_data:
                    agg_df = pd.DataFrame(agg_data)
                    agg_df.to_excel(writer, sheet_name='Aggregate Validation', index=False)
        
        self.logger.info(f"Excel business report saved to {filename}")
    
    def run_full_business_validation(self) -> Dict[str, Any]:
        """Run complete business logic validation"""
        self.logger.info("Starting full business logic validation...")
        
        # Test connections
        if not self.validate_connections():
            raise Exception("Database connection validation failed")
        
        # Run business validation
        results = self.business_validator.comprehensive_business_validation()
        
        # Generate reports
        reports = self.generate_business_report(results)
        
        # Cleanup connections
        self.cleanup()
        
        self.logger.info("Business logic validation completed successfully")
        
        return {
            'validation_results': results,
            'reports': reports
        }
    
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
    parser = argparse.ArgumentParser(description='Business Logic Migration Validator')
    parser.add_argument('--config', '-c', required=True, help='Database configuration file (YAML)')
    parser.add_argument('--mapping', '-m', required=True, help='Business mapping configuration file (YAML)')
    parser.add_argument('--contracts-only', action='store_true', help='Run only contract validation')
    parser.add_argument('--customers-only', action='store_true', help='Run only customer validation')
    parser.add_argument('--aggregates-only', action='store_true', help='Run only aggregate validation')
    parser.add_argument('--custom-only', action='store_true', help='Run only custom rules validation')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Load configurations
    config = load_config(args.config)
    mapping_config = load_config(args.mapping)
    
    # Adjust log level if verbose
    if args.verbose:
        config.setdefault('logging', {})['level'] = 'DEBUG'
    
    try:
        # Initialize validator
        validator = BusinessMigrationValidator(config, mapping_config)
        
        # Run validation based on arguments
        if args.contracts_only:
            contract_results = validator.run_contract_validation()
            results = {'contract_validation': contract_results}
            reports = validator.generate_business_report(results)
        elif args.customers_only:
            customer_results = validator.run_customer_validation()
            results = {'customer_validation': customer_results}
            reports = validator.generate_business_report(results)
        elif args.aggregates_only:
            aggregate_results = validator.run_aggregate_validation()
            results = {'aggregate_validation': aggregate_results}
            reports = validator.generate_business_report(results)
        elif args.custom_only:
            custom_results = validator.run_custom_rules()
            results = {'custom_rules': custom_results}
            reports = validator.generate_business_report(results)
        else:
            # Run full validation
            full_results = validator.run_full_business_validation()
            results = full_results['validation_results']
            reports = full_results['reports']
        
        print("\n✅ Business logic validation completed successfully!")
        
        # Show summary
        if 'summary' in results:
            summary = results['summary']
            print(f"\n📊 Summary:")
            print(f"   Success Rate: {summary['overall_success_rate']:.1f}%")
            print(f"   Status: {summary['validation_status']}")
        
    except KeyboardInterrupt:
        print("\n❌ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()