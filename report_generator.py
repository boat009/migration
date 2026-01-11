import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
import logging
from tabulate import tabulate
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

class ReportGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def generate_console_report(self, schema_results: Dict[str, Any], data_results: Dict[str, Any]) -> str:
        """Generate colorized console report"""
        report = []
        report.append(f"\n{Fore.CYAN}{'='*80}")
        report.append(f"{Fore.CYAN}DB2 TO POSTGRESQL MIGRATION VALIDATION REPORT")
        report.append(f"{Fore.CYAN}Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        
        # Schema Validation Summary
        report.append(f"\n{Fore.YELLOW}SCHEMA VALIDATION SUMMARY{Style.RESET_ALL}")
        report.append("-" * 40)
        
        if 'summary' in schema_results:
            summary = schema_results['summary']
            report.append(f"Tables Migrated: {Fore.GREEN}{summary['tables_migrated']}{Style.RESET_ALL}")
            report.append(f"Tables Missing: {Fore.RED}{summary['tables_missing']}{Style.RESET_ALL}")
            report.append(f"Tables with Schema Issues: {Fore.YELLOW}{summary['tables_with_schema_issues']}{Style.RESET_ALL}")
        
        # Table Comparison
        if 'table_comparison' in schema_results:
            tc = schema_results['table_comparison']
            report.append(f"\nDB2 Tables: {tc['db2_total']}")
            report.append(f"PostgreSQL Tables: {tc['postgresql_total']}")
            
            if tc['db2_only']:
                report.append(f"\n{Fore.RED}Tables Missing in PostgreSQL:{Style.RESET_ALL}")
                for table in tc['db2_only']:
                    report.append(f"  - {table}")
                    
            if tc['postgresql_only']:
                report.append(f"\n{Fore.YELLOW}Extra Tables in PostgreSQL:{Style.RESET_ALL}")
                for table in tc['postgresql_only']:
                    report.append(f"  - {table}")
        
        # Schema Differences
        if 'schema_differences' in schema_results and schema_results['schema_differences']:
            report.append(f"\n{Fore.YELLOW}SCHEMA DIFFERENCES{Style.RESET_ALL}")
            report.append("-" * 40)
            
            for table_diff in schema_results['schema_differences']:
                report.append(f"\nTable: {Fore.CYAN}{table_diff['table']}{Style.RESET_ALL}")
                
                for diff in table_diff['differences']:
                    if diff['type'] == 'missing_in_postgresql':
                        report.append(f"  {Fore.RED}Missing Column:{Style.RESET_ALL} {diff['column']}")
                    elif diff['type'] == 'missing_in_db2':
                        report.append(f"  {Fore.YELLOW}Extra Column:{Style.RESET_ALL} {diff['column']}")
                    elif diff['type'] == 'data_type_mismatch':
                        report.append(f"  {Fore.YELLOW}Type Mismatch:{Style.RESET_ALL} {diff['column']} (DB2: {diff['db2_type']}, PG: {diff['postgresql_type']})")
        
        # Data Validation Summary
        if data_results:
            report.append(f"\n{Fore.YELLOW}DATA VALIDATION SUMMARY{Style.RESET_ALL}")
            report.append("-" * 40)
            
            if 'summary' in data_results:
                summary = data_results['summary']
                report.append(f"Total Tables Validated: {summary['total_tables']}")
                report.append(f"Row Count Matches: {Fore.GREEN}{summary['row_count_matches']}{Style.RESET_ALL}")
                report.append(f"Checksum Matches: {Fore.GREEN}{summary['checksum_matches']}{Style.RESET_ALL}")
                report.append(f"Primary Key Matches: {Fore.GREEN}{summary['primary_key_matches']}{Style.RESET_ALL}")
                report.append(f"Data Type Validations Passed: {Fore.GREEN}{summary['data_type_passes']}{Style.RESET_ALL}")
                report.append(f"Overall Success Rate: {Fore.GREEN}{summary['overall_success_rate']:.1f}%{Style.RESET_ALL}")
            
            # Row Count Issues
            row_count_issues = [r for r in data_results.get('row_count_comparisons', []) if not r.get('match', False)]
            if row_count_issues:
                report.append(f"\n{Fore.RED}ROW COUNT MISMATCHES{Style.RESET_ALL}")
                report.append("-" * 30)
                
                table_data = []
                for issue in row_count_issues:
                    table_data.append([
                        issue['table'],
                        issue.get('db2_count', 'Error'),
                        issue.get('postgresql_count', 'Error'),
                        issue.get('difference', 'N/A')
                    ])
                
                report.append(tabulate(table_data, headers=['Table', 'DB2 Count', 'PostgreSQL Count', 'Difference'], tablefmt='grid'))
            
            # Checksum Issues
            checksum_issues = [r for r in data_results.get('checksum_comparisons', []) if not r.get('match', False)]
            if checksum_issues:
                report.append(f"\n{Fore.RED}DATA CHECKSUM MISMATCHES{Style.RESET_ALL}")
                report.append("-" * 35)
                
                for issue in checksum_issues:
                    report.append(f"  - {issue['table']}")
        
        report.append(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        
        return '\n'.join(report)
    
    def generate_json_report(self, schema_results: Dict[str, Any], data_results: Dict[str, Any], filename: str = None) -> str:
        """Generate JSON report"""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'schema_validation': schema_results,
            'data_validation': data_results
        }
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"JSON report saved to {filename}")
            
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    def generate_html_report(self, schema_results: Dict[str, Any], data_results: Dict[str, Any], filename: str = None) -> str:
        """Generate HTML report"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>DB2 to PostgreSQL Migration Validation Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
                .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #3498db; }}
                .success {{ color: #27ae60; }}
                .warning {{ color: #f39c12; }}
                .error {{ color: #e74c3c; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .summary-box {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>DB2 to PostgreSQL Migration Validation Report</h1>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """
        
        # Schema Validation Section
        html_content += """
            <div class="section">
                <h2>Schema Validation Results</h2>
        """
        
        if 'summary' in schema_results:
            summary = schema_results['summary']
            html_content += f"""
                <div class="summary-box">
                    <h3>Summary</h3>
                    <p>Tables Migrated: <span class="success">{summary['tables_migrated']}</span></p>
                    <p>Tables Missing: <span class="error">{summary['tables_missing']}</span></p>
                    <p>Tables with Schema Issues: <span class="warning">{summary['tables_with_schema_issues']}</span></p>
                </div>
            """
        
        # Table Comparison
        if 'table_comparison' in schema_results:
            tc = schema_results['table_comparison']
            html_content += f"""
                <h3>Table Comparison</h3>
                <p>DB2 Tables: {tc['db2_total']}</p>
                <p>PostgreSQL Tables: {tc['postgresql_total']}</p>
            """
            
            if tc['db2_only']:
                html_content += """
                    <h4 class="error">Tables Missing in PostgreSQL</h4>
                    <ul>
                """
                for table in tc['db2_only']:
                    html_content += f"<li>{table}</li>"
                html_content += "</ul>"
        
        # Schema Differences
        if 'schema_differences' in schema_results and schema_results['schema_differences']:
            html_content += """
                <h3>Schema Differences</h3>
                <table>
                    <tr><th>Table</th><th>Issue Type</th><th>Column</th><th>Details</th></tr>
            """
            
            for table_diff in schema_results['schema_differences']:
                for diff in table_diff['differences']:
                    issue_type = diff['type'].replace('_', ' ').title()
                    details = ""
                    if diff['type'] == 'data_type_mismatch':
                        details = f"DB2: {diff['db2_type']}, PostgreSQL: {diff['postgresql_type']}"
                    
                    html_content += f"""
                        <tr>
                            <td>{table_diff['table']}</td>
                            <td>{issue_type}</td>
                            <td>{diff['column']}</td>
                            <td>{details}</td>
                        </tr>
                    """
            
            html_content += "</table>"
        
        html_content += "</div>"
        
        # Data Validation Section
        if data_results:
            html_content += """
                <div class="section">
                    <h2>Data Validation Results</h2>
            """
            
            if 'summary' in data_results:
                summary = data_results['summary']
                html_content += f"""
                    <div class="summary-box">
                        <h3>Summary</h3>
                        <p>Total Tables Validated: {summary['total_tables']}</p>
                        <p>Row Count Matches: <span class="success">{summary['row_count_matches']}</span></p>
                        <p>Checksum Matches: <span class="success">{summary['checksum_matches']}</span></p>
                        <p>Primary Key Matches: <span class="success">{summary['primary_key_matches']}</span></p>
                        <p>Data Type Validations Passed: <span class="success">{summary['data_type_passes']}</span></p>
                        <p>Overall Success Rate: <span class="success">{summary['overall_success_rate']:.1f}%</span></p>
                    </div>
                """
            
            # Row Count Issues
            row_count_issues = [r for r in data_results.get('row_count_comparisons', []) if not r.get('match', False)]
            if row_count_issues:
                html_content += """
                    <h3 class="error">Row Count Mismatches</h3>
                    <table>
                        <tr><th>Table</th><th>DB2 Count</th><th>PostgreSQL Count</th><th>Difference</th></tr>
                """
                
                for issue in row_count_issues:
                    html_content += f"""
                        <tr>
                            <td>{issue['table']}</td>
                            <td>{issue.get('db2_count', 'Error')}</td>
                            <td>{issue.get('postgresql_count', 'Error')}</td>
                            <td>{issue.get('difference', 'N/A')}</td>
                        </tr>
                    """
                
                html_content += "</table>"
            
            html_content += "</div>"
        
        html_content += """
            </body>
        </html>
        """
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.logger.info(f"HTML report saved to {filename}")
            
        return html_content
    
    def generate_excel_report(self, schema_results: Dict[str, Any], data_results: Dict[str, Any], filename: str) -> None:
        """Generate Excel report with multiple sheets"""
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = []
            
            if 'summary' in schema_results:
                schema_summary = schema_results['summary']
                summary_data.extend([
                    ['Schema Validation', ''],
                    ['Tables Migrated', schema_summary['tables_migrated']],
                    ['Tables Missing', schema_summary['tables_missing']],
                    ['Tables with Schema Issues', schema_summary['tables_with_schema_issues']],
                    ['', '']
                ])
            
            if 'summary' in data_results:
                data_summary = data_results['summary']
                summary_data.extend([
                    ['Data Validation', ''],
                    ['Total Tables', data_summary['total_tables']],
                    ['Row Count Matches', data_summary['row_count_matches']],
                    ['Checksum Matches', data_summary['checksum_matches']],
                    ['Primary Key Matches', data_summary['primary_key_matches']],
                    ['Data Type Passes', data_summary['data_type_passes']],
                    ['Overall Success Rate (%)', f"{data_summary['overall_success_rate']:.1f}"]
                ])
            
            summary_df = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Schema differences sheet
            if 'schema_differences' in schema_results and schema_results['schema_differences']:
                schema_diff_data = []
                for table_diff in schema_results['schema_differences']:
                    for diff in table_diff['differences']:
                        schema_diff_data.append({
                            'Table': table_diff['table'],
                            'Issue Type': diff['type'],
                            'Column': diff['column'],
                            'DB2 Type': diff.get('db2_type', ''),
                            'PostgreSQL Type': diff.get('postgresql_type', '')
                        })
                
                schema_df = pd.DataFrame(schema_diff_data)
                schema_df.to_excel(writer, sheet_name='Schema Differences', index=False)
            
            # Row count comparison sheet
            if 'row_count_comparisons' in data_results:
                row_count_df = pd.DataFrame(data_results['row_count_comparisons'])
                row_count_df.to_excel(writer, sheet_name='Row Count Comparison', index=False)
            
            # Checksum comparison sheet
            if 'checksum_comparisons' in data_results:
                checksum_df = pd.DataFrame(data_results['checksum_comparisons'])
                checksum_df.to_excel(writer, sheet_name='Checksum Comparison', index=False)
        
        self.logger.info(f"Excel report saved to {filename}")
    
    def generate_all_reports(self, schema_results: Dict[str, Any], data_results: Dict[str, Any], base_filename: str = None) -> Dict[str, str]:
        """Generate all report formats"""
        if not base_filename:
            base_filename = f"migration_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        reports = {}
        
        # Console report
        reports['console'] = self.generate_console_report(schema_results, data_results)
        
        # JSON report
        json_file = f"{base_filename}.json"
        reports['json'] = self.generate_json_report(schema_results, data_results, json_file)
        
        # HTML report
        html_file = f"{base_filename}.html"
        reports['html'] = self.generate_html_report(schema_results, data_results, html_file)
        
        # Excel report
        excel_file = f"{base_filename}.xlsx"
        self.generate_excel_report(schema_results, data_results, excel_file)
        reports['excel'] = excel_file
        
        return reports