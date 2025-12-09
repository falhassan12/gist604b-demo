"""
Utility Functions for Spatial Validation Toolbox

Helper functions for configuration, reporting, and common operations.
"""

import os
import arcpy
from datetime import datetime


def get_toolbox_dir():
    """Get the directory containing the toolbox"""
    return os.path.dirname(os.path.abspath(__file__))


def get_config_path(filename='rules_config.json'):
    """
    Get path to configuration file
    
    Looks for config in the Config folder relative to the toolbox.
    
    Args:
        filename: Name of configuration file
        
    Returns:
        Full path to configuration file
    """
    toolbox_dir = get_toolbox_dir()
    parent_dir = os.path.dirname(toolbox_dir)
    config_path = os.path.join(parent_dir, 'Config', filename)
    
    if os.path.exists(config_path):
        return config_path
    
    # Fallback to toolbox directory
    return os.path.join(toolbox_dir, filename)


def format_validation_summary(violations):
    """
    Format validation results as summary dictionary
    
    Args:
        violations: List of violation dictionaries
        
    Returns:
        Dictionary with summary statistics
    """
    error_count = sum(1 for v in violations if v['severity'] == 'ERROR')
    warning_count = sum(1 for v in violations if v['severity'] == 'WARNING')
    info_count = sum(1 for v in violations if v['severity'] == 'INFO')
    
    # Group by rule
    by_rule = {}
    for v in violations:
        rule = v['rule_code']
        if rule not in by_rule:
            by_rule[rule] = {'errors': 0, 'warnings': 0, 'info': 0}
        
        if v['severity'] == 'ERROR':
            by_rule[rule]['errors'] += 1
        elif v['severity'] == 'WARNING':
            by_rule[rule]['warnings'] += 1
        else:
            by_rule[rule]['info'] += 1
    
    summary = {
        'total_violations': len(violations),
        'error_count': error_count,
        'warning_count': warning_count,
        'info_count': info_count,
        'by_rule': by_rule,
        'passed': error_count == 0
    }
    
    # Format as string for display
    lines = [
        "",
        "=" * 60,
        "VALIDATION SUMMARY",
        "=" * 60,
        f"Total Violations: {len(violations)}",
        f"  Errors:   {error_count}",
        f"  Warnings: {warning_count}",
        f"  Info:     {info_count}",
        "",
        "By Rule:"
    ]
    
    for rule, counts in by_rule.items():
        lines.append(f"  {rule}: {counts['errors']}E / {counts['warnings']}W")
    
    lines.append("=" * 60)
    
    summary['formatted'] = "\n".join(lines)
    
    return summary


def generate_csv_report(results_table, project_id, output_csv):
    """
    Generate CSV report from validation results
    
    Args:
        results_table: Path to results table/feature class
        project_id: Project ID to filter by (or None for all)
        output_csv: Output CSV file path
    """
    import csv
    
    where_clause = f"ProjectID = '{project_id}'" if project_id else None
    
    fields = [
        'ProjectID', 'RuleCode', 'RuleName', 'Severity',
        'SourceFC', 'SourceOID', 'TargetFC', 'TargetOID',
        'MeasuredValue', 'ThresholdValue', 'Message',
        'ValidationDate', 'ValidatedBy'
    ]
    
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        
        with arcpy.da.SearchCursor(results_table, fields, where_clause) as cursor:
            for row in cursor:
                writer.writerow(row)


def generate_excel_report(results_table, project_id, output_excel, include_summary=True):
    """
    Generate Excel report from validation results
    
    Requires openpyxl library.
    
    Args:
        results_table: Path to results table/feature class
        project_id: Project ID to filter by (or None for all)
        output_excel: Output Excel file path
        include_summary: Whether to include summary sheet
    """
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise ImportError("openpyxl library required for Excel export. Install with: pip install openpyxl")
    
    wb = openpyxl.Workbook()
    
    # Summary sheet
    if include_summary:
        ws_summary = wb.active
        ws_summary.title = "Summary"
        
        # Header styling
        header_font = Font(bold=True, size=14)
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        
        ws_summary['A1'] = "Validation Report"
        ws_summary['A1'].font = Font(bold=True, size=16)
        ws_summary['A3'] = "Project ID"
        ws_summary['B3'] = project_id or "All Projects"
        ws_summary['A4'] = "Report Date"
        ws_summary['B4'] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Query summary stats
        where_clause = f"ProjectID = '{project_id}'" if project_id else None
        
        violations = []
        with arcpy.da.SearchCursor(results_table, ['Severity'], where_clause) as cursor:
            for row in cursor:
                violations.append(row[0])
        
        error_count = violations.count('ERROR')
        warning_count = violations.count('WARNING')
        
        ws_summary['A6'] = "Summary Statistics"
        ws_summary['A6'].font = header_font
        ws_summary['A7'] = "Total Violations"
        ws_summary['B7'] = len(violations)
        ws_summary['A8'] = "Errors"
        ws_summary['B8'] = error_count
        ws_summary['A8'].fill = PatternFill(start_color="FF6B6B", end_color="FF6B6B", fill_type="solid")
        ws_summary['A9'] = "Warnings"
        ws_summary['B9'] = warning_count
        ws_summary['A9'].fill = PatternFill(start_color="FFE66D", end_color="FFE66D", fill_type="solid")
        
        # Status
        ws_summary['A11'] = "Status"
        if error_count == 0:
            ws_summary['B11'] = "PASSED"
            ws_summary['B11'].fill = PatternFill(start_color="4CAF50", end_color="4CAF50", fill_type="solid")
        else:
            ws_summary['B11'] = "FAILED"
            ws_summary['B11'].fill = PatternFill(start_color="FF6B6B", end_color="FF6B6B", fill_type="solid")
        
        # Details sheet
        ws_details = wb.create_sheet("Violations")
    else:
        ws_details = wb.active
        ws_details.title = "Violations"
    
    # Headers
    headers = [
        'Rule Name', 'Severity', 'Source FC', 'Source OID',
        'Target FC', 'Target OID', 'Measured Value', 'Threshold', 'Message'
    ]
    
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    for col, header in enumerate(headers, 1):
        cell = ws_details.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
    
    # Data rows
    fields = [
        'RuleName', 'Severity', 'SourceFC', 'SourceOID',
        'TargetFC', 'TargetOID', 'MeasuredValue', 'ThresholdValue', 'Message'
    ]
    
    error_fill = PatternFill(start_color="FFCCCB", end_color="FFCCCB", fill_type="solid")
    warning_fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")
    
    row_num = 2
    where_clause = f"ProjectID = '{project_id}'" if project_id else None
    
    with arcpy.da.SearchCursor(results_table, fields, where_clause) as cursor:
        for row in cursor:
            for col, value in enumerate(row, 1):
                cell = ws_details.cell(row=row_num, column=col, value=value)
                
                # Color by severity
                if col == 2:  # Severity column
                    if value == 'ERROR':
                        for c in range(1, len(headers) + 1):
                            ws_details.cell(row=row_num, column=c).fill = error_fill
                    elif value == 'WARNING':
                        for c in range(1, len(headers) + 1):
                            ws_details.cell(row=row_num, column=c).fill = warning_fill
            
            row_num += 1
    
    # Auto-size columns
    for col in range(1, len(headers) + 1):
        ws_details.column_dimensions[get_column_letter(col)].width = 15
    
    # Save
    wb.save(output_excel)


def ensure_spatial_indexes(feature_classes):
    """
    Ensure all feature classes have spatial indexes
    
    Args:
        feature_classes: List of feature class paths
        
    Returns:
        List of feature classes that had indexes added
    """
    indexed = []
    
    for fc in feature_classes:
        if not arcpy.Exists(fc):
            continue
            
        desc = arcpy.Describe(fc)
        if not desc.hasSpatialIndex:
            arcpy.AddSpatialIndex_management(fc)
            indexed.append(fc)
    
    return indexed


def validate_rule_config(config_path):
    """
    Validate rule configuration file
    
    Args:
        config_path: Path to JSON configuration file
        
    Returns:
        Tuple of (is_valid, errors_list)
    """
    import json
    
    errors = []
    
    if not os.path.exists(config_path):
        return False, ["Configuration file not found"]
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {str(e)}"]
    
    # Check required sections
    if 'rules' not in config:
        errors.append("Missing 'rules' section")
    
    # Validate each rule
    required_fields = ['rule_code', 'rule_name', 'rule_type', 'source_fc', 'target_fc']
    valid_rule_types = [
        'MINIMUM_DISTANCE', 'MAXIMUM_DISTANCE', 'INTERSECTION_ANGLE',
        'CROSSING_ANGLE', 'CONTAINMENT', 'ATTRIBUTE_DISTANCE', 'BUFFER_OVERLAP'
    ]
    
    for i, rule in enumerate(config.get('rules', [])):
        for field in required_fields:
            if field not in rule:
                errors.append(f"Rule {i+1}: Missing required field '{field}'")
        
        if rule.get('rule_type') not in valid_rule_types:
            errors.append(f"Rule {i+1}: Invalid rule_type '{rule.get('rule_type')}'")
    
    return len(errors) == 0, errors


def create_violation_layer_file(template_fc, output_lyrx, symbology_type='graduated'):
    """
    Create layer file for violation visualization
    
    Note: This requires ArcGIS Pro and may need manual adjustment.
    
    Args:
        template_fc: Feature class to use as template
        output_lyrx: Output layer file path
        symbology_type: 'graduated' or 'unique'
    """
    # This is a placeholder - layer files are typically created manually
    # or through ArcGIS Pro's Python API with a project context
    
    # For now, just document the recommended symbology:
    # 
    # Severity-based symbology:
    #   ERROR:   Red circle, size 12
    #   WARNING: Orange triangle, size 10
    #   INFO:    Blue square, size 8
    #
    # Label expression: [RuleCode]
    
    pass


class ValidationCache:
    """
    Cache for frequently accessed validation data
    
    Improves performance by caching infrastructure features
    that are read multiple times during validation.
    """
    
    def __init__(self, max_size=1000):
        self._cache = {}
        self._max_size = max_size
    
    def get(self, key):
        """Get item from cache"""
        return self._cache.get(key)
    
    def set(self, key, value):
        """Add item to cache"""
        if len(self._cache) >= self._max_size:
            # Simple eviction: remove oldest half
            keys = list(self._cache.keys())
            for k in keys[:len(keys)//2]:
                del self._cache[k]
        
        self._cache[key] = value
    
    def clear(self):
        """Clear the cache"""
        self._cache.clear()
    
    def get_features(self, fc_path, extent=None):
        """
        Get features from cache or load from feature class
        
        Args:
            fc_path: Path to feature class
            extent: Optional extent to filter by
            
        Returns:
            List of (OID, geometry) tuples
        """
        cache_key = (fc_path, str(extent))
        
        cached = self.get(cache_key)
        if cached is not None:
            return cached
        
        features = []
        with arcpy.da.SearchCursor(fc_path, ['OID@', 'SHAPE@']) as cursor:
            for oid, geom in cursor:
                if extent is None or (geom and extent.overlaps(geom.extent)):
                    features.append((oid, geom))
        
        self.set(cache_key, features)
        return features

