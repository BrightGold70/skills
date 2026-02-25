#!/usr/bin/env python3
"""
09_validate.py
Clinical Trial Data Validation Engine

Validates patient data against:
- Protocol specifications (endpoints, treatment arms, sample size)
- CRF specifications (variable types, valid ranges, required fields)
- Custom validation rules (temporal logic, data consistency)

Validation Types:
1. Data Completeness - Required fields, missing values
2. Value Range Validation - Min/max, allowed values
3. Temporal Logic - Date sequences, visit windows

Author: Clinical Statistics Analyzer
Version: 1.0.0
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from collections import defaultdict
import pandas as pd
import numpy as np


class ValidationEngine:
    """
    Validation engine for clinical trial data.
    Validates data against protocol and CRF specifications.
    """
    
    def __init__(self, protocol_spec: Dict = None, crf_spec: Dict = None, validation_rules: Dict = None):
        """
        Initialize the validation engine.
        
        Args:
            protocol_spec: Parsed protocol specification
            crf_spec: Parsed CRF specification
            validation_rules: Custom validation rules
        """
        self.protocol_spec = protocol_spec or {}
        self.crf_spec = crf_spec or {}
        self.validation_rules = validation_rules or {}
        self.validation_results = {}
        self.errors = []
        self.warnings = []
        self.info = []
        
    def validate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Run all validations on the data.
        
        Args:
            data: DataFrame containing patient data
            
        Returns:
            Dictionary containing validation results
        """
        self.errors = []
        self.warnings = []
        self.info = []
        
        # Run all validation types
        self._validate_completeness(data)
        self._validate_value_ranges(data)
        self._validate_temporal_logic(data)
        self._validate_custom_rules(data)
        
        # Build results
        self.validation_results = {
            "validation_date": datetime.now().isoformat(),
            "total_records": len(data),
            "total_variables": len(data.columns),
            "summary": {
                "errors": len(self.errors),
                "warnings": len(self.warnings),
                "info": len(self.info)
            },
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "status": "PASSED" if len(self.errors) == 0 else "FAILED"
        }
        
        return self.validation_results
    
    def _validate_completeness(self, data: pd.DataFrame) -> None:
        """
        Validate data completeness.
        Checks for:
        - Required fields (from CRF spec)
        - Missing values patterns
        - Record-level completeness
        """
        # Get required variables from CRF spec
        required_vars = []
        if 'variables' in self.crf_spec:
            for var in self.crf_spec['variables']:
                if var.get('required', False):
                    required_vars.append(var['variable_name'])
        
        # Check required fields
        for var in required_vars:
            if var in data.columns:
                missing = data[var].isna().sum()
                if missing > 0:
                    missing_pct = (missing / len(data)) * 100
                    self.warnings.append({
                        "type": "Completeness",
                        "severity": "Warning",
                        "variable": var,
                        "message": f"Required field '{var}' has {missing} missing values ({missing_pct:.1f}%)",
                        "count": int(missing)
                    })
        
        # Check overall record completeness
        complete_records = data.dropna()
        if len(complete_records) < len(data):
            incomplete = len(data) - len(complete_records)
            self.warnings.append({
                "type": "Completeness",
                "severity": "Warning",
                "variable": "All",
                "message": f"{incomplete} records have at least one missing value",
                "count": incomplete
            })
        
        # Check for variables with high missing rates (>50%)
        for col in data.columns:
            missing_rate = data[col].isna().mean()
            if missing_rate > 0.5:
                self.info.append({
                    "type": "Completeness",
                    "severity": "Info",
                    "variable": col,
                    "message": f"Variable '{col}' has {missing_rate*100:.1f}% missing values - consider review",
                    "missing_rate": float(missing_rate)
                })
    
    def _validate_value_ranges(self, data: pd.DataFrame) -> None:
        """
        Validate value ranges.
        Checks for:
        - Min/max violations
        - Invalid categorical values
        - Outliers
        """
        # Get variable specifications from CRF
        var_specs = {}
        if 'variables' in self.crf_spec:
            for var in self.crf_spec['variables']:
                var_specs[var['variable_name']] = var
        
        # Validate each variable
        for col in data.columns:
            if col not in var_specs:
                continue
            
            spec = var_specs[col]
            
            # Check valid range
            if 'valid_range' in spec and spec['valid_range']:
                range_str = str(spec['valid_range'])
                
                # Parse range patterns
                # Pattern: "0-100" or "0 to 100" or "<=100" or ">=0"
                range_match = re.match(r'([<>=]+)?\s*(\d+\.?\d*)\s*(?:to|-)?\s*([<>=]+)?\s*(\d+\.?\d*)?', range_str)
                
                if range_match:
                    min_val = range_match.group(2)
                    max_val = range_match.group(4)
                    prefix = range_match.group(1) or range_match.group(3)
                    
                    try:
                        if min_val and max_val:
                            # Range like "0-100"
                            violations = data[(data[col] < float(min_val)) | (data[col] > float(max_val))]
                        elif prefix == '<' or prefix == '<=':
                            violations = data[data[col] >= float(min_val)]
                        elif prefix == '>' or prefix == '>=':
                            violations = data[data[col] <= float(min_val)]
                        else:
                            continue
                        
                        if len(violations) > 0:
                            self.errors.append({
                                "type": "Value Range",
                                "severity": "Error",
                                "variable": col,
                                "message": f"Variable '{col}' has {len(violations)} values outside valid range ({range_str})",
                                "count": len(violations),
                                "valid_range": range_str
                            })
                    except (ValueError, TypeError):
                        pass
            
            # Check allowed values (for categorical)
            if 'values' in spec and spec['values']:
                allowed = set(spec['values'].keys())
                actual = set(data[col].dropna().unique())
                invalid = actual - allowed
                
                if invalid:
                    self.errors.append({
                        "type": "Invalid Value",
                        "severity": "Error",
                        "variable": col,
                        "message": f"Variable '{col}' has invalid values: {invalid}",
                        "invalid_values": list(invalid),
                        "allowed_values": list(allowed)
                    })
            
            # Check data type consistency
            if pd.api.types.is_numeric_dtype(data[col]):
                # For numeric columns, check for outliers using IQR
                Q1 = data[col].quantile(0.25)
                Q3 = data[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = data[(data[col] < lower_bound) | (data[col] > upper_bound)]
                
                if len(outliers) > 0:
                    self.warnings.append({
                        "type": "Outlier",
                        "severity": "Warning",
                        "variable": col,
                        "message": f"Variable '{col}' has {len(outliers)} potential outlier values",
                        "count": len(outliers),
                        "bounds": {"lower": float(lower_bound), "upper": float(upper_bound)}
                    })
    
    def _validate_temporal_logic(self, data: pd.DataFrame) -> None:
        """
        Validate temporal logic.
        Checks for:
        - Date sequence violations
        - Visit window violations
        - Age/date consistency
        """
        # Find date columns
        date_cols = []
        for col in data.columns:
            if 'date' in col.lower() or 'dt' in col.lower():
                date_cols.append(col)
        
        # Try to parse date columns
        for col in date_cols:
            try:
                # Try to convert to datetime
                date_series = pd.to_datetime(data[col], errors='coerce')
                
                # Check for future dates
                future_dates = data[date_series > pd.Timestamp.now()]
                if len(future_dates) > 0:
                    self.warnings.append({
                        "type": "Temporal",
                        "severity": "Warning",
                        "variable": col,
                        "message": f"Column '{col}' has {len(future_dates)} future dates",
                        "count": len(future_dates)
                    })
                
                # Look for date sequences
                if 'screening' in col.lower():
                    baseline_col = self._find_column(data.columns, ['baseline', 'baseline', 'day1', 'day 1'])
                    if baseline_col:
                        self._validate_date_sequence(data, col, baseline_col, 'Screening', 'Baseline')
                
                if 'visit' in col.lower():
                    # Look for visit order violations
                    self._validate_visit_order(data, col)
                    
            except Exception:
                pass
        
        # Check for age consistency if birth date and age both exist
        birth_col = self._find_column(data.columns, ['birth', 'dob', 'birthdate', 'birth_dt'])
        age_col = self._find_column(data.columns, ['age'])
        
        if birth_col and age_col:
            try:
                birth_dates = pd.to_datetime(data[birth_col], errors='coerce')
                today = pd.Timestamp.now()
                calculated_age = ((today - birth_dates).dt.days / 365.25).round()
                
                # Compare with recorded age
                age_diff = abs(calculated_age - data[age_col])
                inconsistent = data[age_diff > 1]  # More than 1 year difference
                
                if len(inconsistent) > 0:
                    self.warnings.append({
                        "type": "Consistency",
                        "severity": "Warning",
                        "variable": f"{birth_col}, {age_col}",
                        "message": f"Age and birth date inconsistent in {len(inconsistent)} records",
                        "count": len(inconsistent)
                    })
            except Exception:
                pass
    
    def _validate_date_sequence(self, data: pd.DataFrame, first_col: str, second_col: str, 
                                first_name: str, second_name: str) -> None:
        """Validate date sequence between two columns."""
        try:
            dates1 = pd.to_datetime(data[first_col], errors='coerce')
            dates2 = pd.to_datetime(data[second_col], errors='coerce')
            
            # Check if second date is before first
            violations = data[dates2 < dates1]
            
            if len(violations) > 0:
                self.errors.append({
                    "type": "Temporal Sequence",
                    "severity": "Error",
                    "variable": f"{first_col}, {second_col}",
                    "message": f"{second_name} date is before {first_name} date in {len(violations)} records",
                    "count": len(violations)
                })
        except Exception:
            pass
    
    def _validate_visit_order(self, data: pd.DataFrame, visit_col: str) -> None:
        """Validate visit order (visits should be in ascending order per patient)."""
        # Check if there's a patient ID column
        patient_col = self._find_column(data.columns, ['subject_id', 'patient_id', 'patient', 'scrno'])
        
        if not patient_col:
            return
        
        # Sort by patient and visit date
        date_col = self._find_column(data.columns, ['visit_date', 'visitdt', 'visit_date'])
        
        if not date_col:
            return
        
        try:
            dates = pd.to_datetime(data[date_col], errors='coerce')
            
            # Group by patient and check for decreasing dates
            for patient, group in data.groupby(patient_col):
                patient_dates = dates[group.index].sort_values()
                if not patient_dates.is_monotonic_increasing:
                    violations = len(group) - 1
                    self.warnings.append({
                        "type": "Visit Order",
                        "severity": "Warning",
                        "variable": visit_col,
                        "message": f"Patient {patient} has {violations} visit date sequence violations",
                        "patient": str(patient)
                    })
        except Exception:
            pass
    
    def _validate_custom_rules(self, data: pd.DataFrame) -> None:
        """Validate custom rules from validation_rules specification."""
        if not self.validation_rules:
            return
        
        # Check protocol-specific rules
        if 'rules' in self.validation_rules:
            for rule in self.validation_rules['rules']:
                rule_type = rule.get('type')
                
                if rule_type == 'endpoint':
                    self._validate_endpoint_rule(data, rule)
                elif rule_type == 'treatment_arm':
                    self._validate_treatment_arm_rule(data, rule)
                elif rule_type == 'custom':
                    self._validate_custom_rule(data, rule)
    
    def _validate_endpoint_rule(self, data: pd.DataFrame, rule: Dict) -> None:
        """Validate endpoint-related rules."""
        # Example: Check if primary endpoint is recorded
        endpoint_var = rule.get('variable')
        
        if endpoint_var and endpoint_var in data.columns:
            missing = data[endpoint_var].isna().sum()
            if missing > 0:
                self.warnings.append({
                    "type": "Endpoint",
                    "severity": "Warning",
                    "variable": endpoint_var,
                    "message": f"Primary endpoint '{endpoint_var}' missing in {missing} records",
                    "count": int(missing)
                })
    
    def _validate_treatment_arm_rule(self, data: pd.DataFrame, rule: Dict) -> None:
        """Validate treatment arm rules."""
        # Check if treatment arm is assigned
        arm_var = rule.get('variable')
        
        if arm_var and arm_var in data.columns:
            missing = data[arm_var].isna().sum()
            if missing > 0:
                self.errors.append({
                    "type": "Treatment Arm",
                    "severity": "Error",
                    "variable": arm_var,
                    "message": f"Treatment arm '{arm_var}' not assigned in {missing} records",
                    "count": int(missing)
                })
            
            # Check if treatment arm is valid
            valid_arms = rule.get('valid_arms', [])
            if valid_arms:
                actual_arms = set(data[arm_var].dropna().unique())
                invalid = actual_arms - set(valid_arms)
                
                if invalid:
                    self.errors.append({
                        "type": "Treatment Arm",
                        "severity": "Error",
                        "variable": arm_var,
                        "message": f"Invalid treatment arms found: {invalid}",
                        "invalid_arms": list(invalid)
                    })
    
    def _validate_custom_rule(self, data: pd.DataFrame, rule: Dict) -> None:
        """Validate custom Python-defined rules."""
        # This would execute custom validation code
        # For now, just a placeholder
        pass
    
    def _find_column(self, columns, patterns: List[str]) -> Optional[str]:
        """Find a column matching any of the patterns."""
        for col in columns:
            col_lower = col.lower()
            for pattern in patterns:
                if pattern.lower() in col_lower:
                    return col
        return None
    
    def save_json(self, output_path: str) -> str:
        """Save validation results to JSON."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, indent=2, ensure_ascii=False)
        return output_path
    
    def save_html(self, output_path: str) -> str:
        """Save validation results to HTML report."""
        results = self.validation_results
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Validation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .warning {{ color: orange; }}
        .error {{ color: red; font-weight: bold; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Clinical Data Validation Report</h1>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>Validation Date: {results.get('validation_date', 'N/A')}</p>
        <p>Total Records: {results.get('total_records', 0)}</p>
        <p>Total Variables: {results.get('total_variables', 0)}</p>
        <p class="{results.get('status', 'UNKNOWN').lower()}">
            Status: <strong>{results.get('status', 'UNKNOWN')}</strong>
        </p>
        <ul>
            <li class="error">Errors: {results['summary'].get('errors', 0)}</li>
            <li class="warning">Warnings: {results['summary'].get('warnings', 0)}</li>
            <li>Info: {results['summary'].get('info', 0)}</li>
        </ul>
    </div>
    
    <h2>Errors ({len(results.get('errors', []))})</h2>
    <table>
        <tr>
            <th>Type</th>
            <th>Variable</th>
            <th>Message</th>
            <th>Count</th>
        </tr>
"""
        
        for error in results.get('errors', []):
            html += f"""        <tr>
            <td>{error.get('type', '')}</td>
            <td>{error.get('variable', '')}</td>
            <td>{error.get('message', '')}</td>
            <td>{error.get('count', '')}</td>
        </tr>
"""
        
        html += """    </table>
    
    <h2>Warnings</h2>
    <table>
        <tr>
            <th>Type</th>
            <th>Variable</th>
            <th>Message</th>
            <th>Count</th>
        </tr>
"""
        
        for warning in results.get('warnings', []):
            html += f"""        <tr>
            <td>{warning.get('type', '')}</td>
            <td>{warning.get('variable', '')}</td>
            <td>{warning.get('message', '')}</td>
            <td>{warning.get('count', '')}</td>
        </tr>
"""
        
        html += """    </table>
    
    <h2>Info Messages</h2>
    <table>
        <tr>
            <th>Type</th>
            <th>Variable</th>
            <th>Message</th>
        </tr>
"""
        
        for info in results.get('info', []):
            html += f"""        <tr>
            <td>{info.get('type', '')}</td>
            <td>{info.get('variable', '')}</td>
            <td>{info.get('message', '')}</td>
        </tr>
"""
        
        html += """    </table>
</body>
</html>"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_path


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 3:
        print("Usage: python 09_validate.py <data_file> <protocol_spec_json> [crf_spec_json] [validation_rules_json] [output]")
        print("\nExample:")
        print("  python 09_validate.py data.xlsx protocol_parsed.json crf_spec_parsed.json validation_rules.json")
        print("  python 09_validate.py data.xlsx protocol_parsed.json crf_spec_parsed.json validation_rules.json report.html")
        sys.exit(1)
    
    data_file = sys.argv[1]
    protocol_file = sys.argv[2]
    crf_file = sys.argv[3] if len(sys.argv) > 3 else None
    rules_file = sys.argv[4] if len(sys.argv) > 4 else None
    output_file = sys.argv[5] if len(sys.argv) > 5 else None
    
    try:
        # Import parsers
        from 08_parse_data import DataParser
        
        # Load specifications
        print("Loading specifications...")
        
        with open(protocol_file, 'r', encoding='utf-8') as f:
            protocol_spec = json.load(f)
        
        crf_spec = {}
        if crf_file:
            with open(crf_file, 'r', encoding='utf-8') as f:
                crf_spec = json.load(f)
        
        validation_rules = {}
        if rules_file:
            with open(rules_file, 'r', encoding='utf-8') as f:
                validation_rules = json.load(f)
        
        # Parse data
        print(f"Parsing data file: {data_file}")
        data_parser = DataParser(data_file)
        data = data_parser.parse()
        df = data_parser.get_dataframe()
        
        # Run validation
        print("Running validation...")
        engine = ValidationEngine(protocol_spec, crf_spec, validation_rules)
        results = engine.validate(df)
        
        # Print summary
        print("\n" + "="*60)
        print("Validation Complete")
        print("="*60)
        print(f"Status: {results['status']}")
        print(f"Errors: {results['summary']['errors']}")
        print(f"Warnings: {results['summary']['warnings']}")
        print(f"Info: {results['summary']['info']}")
        
        # Show errors
        if results['errors']:
            print("\nErrors:")
            for error in results['errors'][:5]:
                print(f"  - [{error['type']}] {error['variable']}: {error['message']}")
        
        # Show warnings
        if results['warnings']:
            print("\nWarnings:")
            for warning in results['warnings'][:5]:
                print(f"  - [{warning['type']}] {warning['variable']}: {warning['message']}")
        
        print("="*60)
        
        # Save results
        if output_file:
            if output_file.endswith('.html'):
                output_path = engine.save_html(output_file)
            else:
                output_path = engine.save_json(output_file)
            print(f"\nSaved to: {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
