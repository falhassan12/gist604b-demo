"""
ArcGIS Spatial Validation Toolbox
Validates development projects against configurable spatial rules

Author: Spatial Validation Team
Version: 1.0.0
"""

import arcpy
import os
import sys

# Add toolbox directory to path for imports
toolbox_dir = os.path.dirname(os.path.abspath(__file__))
if toolbox_dir not in sys.path:
    sys.path.insert(0, toolbox_dir)

from validation_engine import SpatialValidator
from utils import get_config_path, format_validation_summary


class Toolbox(object):
    """ArcGIS Python Toolbox for Spatial Validation"""
    
    def __init__(self):
        """Define the toolbox properties"""
        self.label = "Spatial Validation Toolbox"
        self.alias = "spatialvalidation"
        self.description = "Validate project features against configurable spatial rules"
        
        # List of tool classes
        self.tools = [
            ValidateProject,
            ValidateFeatureClass,
            ConfigureRules,
            GenerateReport,
            ClearValidation,
            BatchValidate
        ]


class ValidateProject(object):
    """Main validation tool - runs all active rules against a project"""
    
    def __init__(self):
        self.label = "Validate Project"
        self.description = "Validate project features against spatial rules"
        self.canRunInBackground = True
        self.category = "Validation"
        
    def getParameterInfo(self):
        """Define parameter definitions"""
        
        # Project ID parameter
        param0 = arcpy.Parameter(
            displayName="Project ID",
            name="project_id",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        
        # Feature classes to validate (multivalue)
        param1 = arcpy.Parameter(
            displayName="Feature Classes to Validate",
            name="feature_classes",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input",
            multiValue=True
        )
        
        # Rule configuration file
        param2 = arcpy.Parameter(
            displayName="Rule Configuration File",
            name="rules_config",
            datatype="DEFile",
            parameterType="Required",
            direction="Input"
        )
        param2.filter.list = ['json']
        # Set default to Config folder
        param2.value = get_config_path('rules_config.json')
        
        # Output validation results table
        param3 = arcpy.Parameter(
            displayName="Validation Results Output",
            name="results_table",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output"
        )
        
        # Stop on first error (optional)
        param4 = arcpy.Parameter(
            displayName="Stop on First Error",
            name="stop_on_error",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
        )
        param4.value = False
        
        # Create violation points (optional)
        param5 = arcpy.Parameter(
            displayName="Create Violation Points",
            name="create_violation_points",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
        )
        param5.value = True
        
        return [param0, param1, param2, param3, param4, param5]
    
    def isLicensed(self):
        """Check if tool is licensed to execute"""
        return True
    
    def updateParameters(self, parameters):
        """Modify parameters before validation"""
        return
    
    def updateMessages(self, parameters):
        """Modify messages created by validation"""
        return
        
    def execute(self, parameters, messages):
        """Execute the validation"""
        
        project_id = parameters[0].valueAsText
        feature_classes = parameters[1].valueAsText.split(';')
        rules_config_path = parameters[2].valueAsText
        results_output = parameters[3].valueAsText
        stop_on_error = parameters[4].value
        create_violation_points = parameters[5].value
        
        messages.addMessage(f"{'='*60}")
        messages.addMessage(f"Starting validation for Project: {project_id}")
        messages.addMessage(f"{'='*60}")
        messages.addMessage(f"Feature classes: {len(feature_classes)}")
        messages.addMessage(f"Rules config: {rules_config_path}")
        
        try:
            # Load rule configuration and create validator
            validator = SpatialValidator(rules_config_path, messages)
            
            # Run validation
            violations = validator.validate_project(
                project_id, 
                feature_classes,
                stop_on_error
            )
            
            # Write results
            if create_violation_points:
                validator.write_results_as_points(violations, results_output, project_id)
            else:
                validator.write_results(violations, results_output, project_id)
            
            # Display summary
            summary = format_validation_summary(violations)
            messages.addMessage(summary)
            
            if summary['error_count'] > 0:
                messages.addWarning(f"Project has {summary['error_count']} blocking errors")
            else:
                messages.addMessage("✓ Project passed validation!")
                
        except Exception as e:
            messages.addErrorMessage(f"Validation failed: {str(e)}")
            raise arcpy.ExecuteError
        
        return


class ValidateFeatureClass(object):
    """Validate a single feature class against specific rules"""
    
    def __init__(self):
        self.label = "Validate Feature Class"
        self.description = "Validate a single feature class against selected rules"
        self.canRunInBackground = True
        self.category = "Validation"
        
    def getParameterInfo(self):
        """Define parameter definitions"""
        
        # Feature class to validate
        param0 = arcpy.Parameter(
            displayName="Feature Class to Validate",
            name="feature_class",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
        )
        
        # Target feature class (for comparison)
        param1 = arcpy.Parameter(
            displayName="Target Feature Class",
            name="target_fc",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
        )
        
        # Rule type
        param2 = arcpy.Parameter(
            displayName="Validation Rule Type",
            name="rule_type",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        param2.filter.type = "ValueList"
        param2.filter.list = [
            "MINIMUM_DISTANCE",
            "MAXIMUM_DISTANCE", 
            "INTERSECTION_ANGLE",
            "CROSSING_ANGLE",
            "CONTAINMENT",
            "BUFFER_OVERLAP",
            "ATTRIBUTE_DISTANCE"
        ]
        
        # Threshold value
        param3 = arcpy.Parameter(
            displayName="Threshold Value",
            name="threshold_value",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input"
        )
        
        # Output
        param4 = arcpy.Parameter(
            displayName="Output Violations",
            name="output_fc",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output"
        )
        
        return [param0, param1, param2, param3, param4]
        
    def execute(self, parameters, messages):
        """Execute single feature class validation"""
        
        source_fc = parameters[0].valueAsText
        target_fc = parameters[1].valueAsText
        rule_type = parameters[2].valueAsText
        threshold = parameters[3].value
        output_fc = parameters[4].valueAsText
        
        messages.addMessage(f"Validating: {os.path.basename(source_fc)}")
        messages.addMessage(f"Against: {os.path.basename(target_fc)}")
        messages.addMessage(f"Rule: {rule_type} (threshold: {threshold})")
        
        try:
            # Create ad-hoc rule
            rule = {
                'rule_code': f'ADHOC_{rule_type}',
                'rule_name': f'Ad-hoc {rule_type} Check',
                'severity': 'ERROR',
                'rule_type': rule_type,
                'parameters': self._build_params(rule_type, threshold)
            }
            
            validator = SpatialValidator(None, messages, skip_config=True)
            violations = validator._execute_rule(source_fc, target_fc, rule, 'ADHOC')
            
            validator.write_results_as_points(violations, output_fc, 'ADHOC')
            
            messages.addMessage(f"\nFound {len(violations)} violations")
            
        except Exception as e:
            messages.addErrorMessage(f"Validation failed: {str(e)}")
            raise arcpy.ExecuteError
        
        return
    
    def _build_params(self, rule_type, threshold):
        """Build parameter dict based on rule type"""
        if rule_type == 'MINIMUM_DISTANCE':
            return {'min_distance_meters': threshold}
        elif rule_type == 'MAXIMUM_DISTANCE':
            return {'max_distance_meters': threshold}
        elif rule_type in ['INTERSECTION_ANGLE', 'CROSSING_ANGLE']:
            return {'min_angle_degrees': threshold}
        elif rule_type == 'CONTAINMENT':
            return {'tolerance_meters': threshold}
        else:
            return {'threshold': threshold}


class ConfigureRules(object):
    """Tool to add/edit rules via GUI"""
    
    def __init__(self):
        self.label = "Configure Rules"
        self.description = "Add or modify validation rules"
        self.canRunInBackground = False
        self.category = "Configuration"
        
    def getParameterInfo(self):
        """Define parameters for rule configuration"""
        
        param0 = arcpy.Parameter(
            displayName="Rule Configuration File",
            name="rules_config",
            datatype="DEFile",
            parameterType="Required",
            direction="Input"
        )
        param0.filter.list = ['json']
        param0.value = get_config_path('rules_config.json')
        
        param1 = arcpy.Parameter(
            displayName="Action",
            name="action",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        param1.filter.type = "ValueList"
        param1.filter.list = ["Add Rule", "Edit Rule", "Disable Rule", "Enable Rule", "Delete Rule"]
        
        param2 = arcpy.Parameter(
            displayName="Rule Code (for Edit/Disable/Enable/Delete)",
            name="rule_code",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
        )
        
        # New rule parameters
        param3 = arcpy.Parameter(
            displayName="New Rule Name",
            name="new_rule_name",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
        )
        
        param4 = arcpy.Parameter(
            displayName="New Rule Code",
            name="new_rule_code",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
        )
        
        param5 = arcpy.Parameter(
            displayName="Rule Type",
            name="rule_type",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
        )
        param5.filter.type = "ValueList"
        param5.filter.list = [
            "MINIMUM_DISTANCE",
            "MAXIMUM_DISTANCE",
            "INTERSECTION_ANGLE",
            "CROSSING_ANGLE",
            "CONTAINMENT",
            "ATTRIBUTE_DISTANCE"
        ]
        
        param6 = arcpy.Parameter(
            displayName="Source Feature Class",
            name="source_fc",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
        )
        
        param7 = arcpy.Parameter(
            displayName="Target Feature Class",
            name="target_fc",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
        )
        
        param8 = arcpy.Parameter(
            displayName="Severity",
            name="severity",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
        )
        param8.filter.type = "ValueList"
        param8.filter.list = ["ERROR", "WARNING", "INFO"]
        param8.value = "ERROR"
        
        param9 = arcpy.Parameter(
            displayName="Threshold Value",
            name="threshold_value",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input"
        )
        
        return [param0, param1, param2, param3, param4, param5, param6, param7, param8, param9]
    
    def updateParameters(self, parameters):
        """Update parameters based on action selection"""
        action = parameters[1].valueAsText
        
        # Show/hide parameters based on action
        if action == "Add Rule":
            parameters[2].enabled = False
            for i in range(3, 10):
                parameters[i].enabled = True
        elif action in ["Edit Rule", "Disable Rule", "Enable Rule", "Delete Rule"]:
            parameters[2].enabled = True
            if action == "Edit Rule":
                for i in range(3, 10):
                    parameters[i].enabled = True
            else:
                for i in range(3, 10):
                    parameters[i].enabled = False
        
        return
        
    def execute(self, parameters, messages):
        """Execute rule configuration"""
        import json
        from datetime import datetime
        
        rules_config_path = parameters[0].valueAsText
        action = parameters[1].valueAsText
        rule_code = parameters[2].valueAsText
        
        # Load existing config
        with open(rules_config_path, 'r') as f:
            config = json.load(f)
        
        if action == "Add Rule":
            new_rule = {
                "rule_code": parameters[4].valueAsText,
                "rule_name": parameters[3].valueAsText,
                "description": "",
                "severity": parameters[8].valueAsText,
                "active": True,
                "source_fc": parameters[6].valueAsText,
                "target_fc": parameters[7].valueAsText,
                "rule_type": parameters[5].valueAsText,
                "parameters": self._build_params(parameters[5].valueAsText, parameters[9].value)
            }
            config["rules"].append(new_rule)
            messages.addMessage(f"Added rule: {new_rule['rule_name']}")
            
        elif action == "Disable Rule":
            for rule in config["rules"]:
                if rule["rule_code"] == rule_code:
                    rule["active"] = False
                    messages.addMessage(f"Disabled rule: {rule_code}")
                    break
                    
        elif action == "Enable Rule":
            for rule in config["rules"]:
                if rule["rule_code"] == rule_code:
                    rule["active"] = True
                    messages.addMessage(f"Enabled rule: {rule_code}")
                    break
                    
        elif action == "Delete Rule":
            config["rules"] = [r for r in config["rules"] if r["rule_code"] != rule_code]
            messages.addMessage(f"Deleted rule: {rule_code}")
        
        # Backup existing config
        backup_path = rules_config_path.replace('.json', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(rules_config_path, 'r') as f:
            backup_content = f.read()
        with open(backup_path, 'w') as f:
            f.write(backup_content)
        messages.addMessage(f"Backup created: {backup_path}")
        
        # Write updated config
        with open(rules_config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        messages.addMessage(f"Configuration updated: {rules_config_path}")
        
        return
    
    def _build_params(self, rule_type, threshold):
        """Build parameter dict based on rule type"""
        if rule_type == 'MINIMUM_DISTANCE':
            return {'min_distance_meters': threshold}
        elif rule_type == 'MAXIMUM_DISTANCE':
            return {'max_distance_meters': threshold}
        elif rule_type in ['INTERSECTION_ANGLE', 'CROSSING_ANGLE']:
            return {'min_angle_degrees': threshold, 'max_angle_degrees': 150}
        elif rule_type == 'CONTAINMENT':
            return {'containment_type': 'COMPLETELY_WITHIN', 'tolerance_meters': threshold}
        else:
            return {'threshold': threshold}


class GenerateReport(object):
    """Generate validation report for a project"""
    
    def __init__(self):
        self.label = "Generate Validation Report"
        self.description = "Create Excel report of validation results"
        self.canRunInBackground = False
        self.category = "Reporting"
        
    def getParameterInfo(self):
        """Define parameters"""
        
        param0 = arcpy.Parameter(
            displayName="Validation Results",
            name="results_table",
            datatype="DETable",
            parameterType="Required",
            direction="Input"
        )
        
        param1 = arcpy.Parameter(
            displayName="Project ID (leave blank for all)",
            name="project_id",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
        )
        
        param2 = arcpy.Parameter(
            displayName="Output Report",
            name="output_report",
            datatype="DEFile",
            parameterType="Required",
            direction="Output"
        )
        param2.filter.list = ['xlsx', 'csv']
        
        param3 = arcpy.Parameter(
            displayName="Include Summary Statistics",
            name="include_summary",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
        )
        param3.value = True
        
        return [param0, param1, param2, param3]
        
    def execute(self, parameters, messages):
        """Generate report"""
        from utils import generate_excel_report, generate_csv_report
        
        results_table = parameters[0].valueAsText
        project_id = parameters[1].valueAsText
        output_report = parameters[2].valueAsText
        include_summary = parameters[3].value
        
        messages.addMessage(f"Generating report for: {project_id or 'All Projects'}")
        
        try:
            if output_report.lower().endswith('.xlsx'):
                generate_excel_report(results_table, project_id, output_report, include_summary)
            else:
                generate_csv_report(results_table, project_id, output_report)
                
            messages.addMessage(f"Report saved to: {output_report}")
            
        except ImportError:
            messages.addWarning("openpyxl not available - using CSV format")
            csv_path = output_report.replace('.xlsx', '.csv')
            generate_csv_report(results_table, project_id, csv_path)
            messages.addMessage(f"Report saved to: {csv_path}")
            
        except Exception as e:
            messages.addErrorMessage(f"Report generation failed: {str(e)}")
            raise arcpy.ExecuteError
        
        return


class ClearValidation(object):
    """Clear validation results for a project"""
    
    def __init__(self):
        self.label = "Clear Validation Results"
        self.description = "Remove validation results for a project"
        self.canRunInBackground = False
        self.category = "Utilities"
        
    def getParameterInfo(self):
        """Define parameters"""
        
        param0 = arcpy.Parameter(
            displayName="Validation Results Table",
            name="results_table",
            datatype="DETable",
            parameterType="Required",
            direction="Input"
        )
        
        param1 = arcpy.Parameter(
            displayName="Project ID",
            name="project_id",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        
        param2 = arcpy.Parameter(
            displayName="Confirm Deletion",
            name="confirm",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input"
        )
        param2.value = False
        
        return [param0, param1, param2]
        
    def execute(self, parameters, messages):
        """Clear validation results"""
        results_table = parameters[0].valueAsText
        project_id = parameters[1].valueAsText
        confirm = parameters[2].value
        
        if not confirm:
            messages.addWarning("Deletion not confirmed. Check 'Confirm Deletion' to proceed.")
            return
        
        where_clause = f"ProjectID = '{project_id}'"
        
        deleted_count = 0
        with arcpy.da.UpdateCursor(results_table, ['OBJECTID'], where_clause) as cursor:
            for row in cursor:
                cursor.deleteRow()
                deleted_count += 1
        
        messages.addMessage(f"Deleted {deleted_count} validation results for Project: {project_id}")
        
        return


class BatchValidate(object):
    """Validate multiple projects in batch"""
    
    def __init__(self):
        self.label = "Batch Validate Projects"
        self.description = "Validate multiple projects at once"
        self.canRunInBackground = True
        self.category = "Validation"
        
    def getParameterInfo(self):
        """Define parameters"""
        
        param0 = arcpy.Parameter(
            displayName="Project IDs (comma-separated)",
            name="project_ids",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        
        param1 = arcpy.Parameter(
            displayName="Workspace",
            name="workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input"
        )
        
        param2 = arcpy.Parameter(
            displayName="Feature Class Name Pattern",
            name="fc_pattern",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        param2.value = "Proposed{FeatureType}_{ProjectID}"
        
        param3 = arcpy.Parameter(
            displayName="Feature Types to Validate",
            name="feature_types",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=True
        )
        param3.filter.type = "ValueList"
        param3.filter.list = ["Roads", "Buildings", "Utilities", "Parcels"]
        param3.value = ["Roads", "Buildings", "Utilities"]
        
        param4 = arcpy.Parameter(
            displayName="Rule Configuration File",
            name="rules_config",
            datatype="DEFile",
            parameterType="Required",
            direction="Input"
        )
        param4.filter.list = ['json']
        param4.value = get_config_path('rules_config.json')
        
        param5 = arcpy.Parameter(
            displayName="Output Workspace",
            name="output_workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input"
        )
        
        return [param0, param1, param2, param3, param4, param5]
        
    def execute(self, parameters, messages):
        """Execute batch validation"""
        
        project_ids = [p.strip() for p in parameters[0].valueAsText.split(',')]
        workspace = parameters[1].valueAsText
        fc_pattern = parameters[2].valueAsText
        feature_types = parameters[3].valueAsText.split(';')
        rules_config_path = parameters[4].valueAsText
        output_workspace = parameters[5].valueAsText
        
        messages.addMessage(f"Batch validating {len(project_ids)} projects...")
        
        validator = SpatialValidator(rules_config_path, messages)
        
        for project_id in project_ids:
            messages.addMessage(f"\n{'='*60}")
            messages.addMessage(f"Validating Project: {project_id}")
            messages.addMessage(f"{'='*60}")
            
            # Build feature class paths
            feature_classes = []
            for feature_type in feature_types:
                fc_name = fc_pattern.format(
                    FeatureType=feature_type,
                    ProjectID=project_id
                )
                fc_path = os.path.join(workspace, fc_name)
                
                if arcpy.Exists(fc_path):
                    feature_classes.append(fc_path)
                else:
                    messages.addWarning(f"Feature class not found: {fc_name}")
            
            if not feature_classes:
                messages.addWarning(f"No feature classes found for project {project_id}")
                continue
            
            # Run validation
            violations = validator.validate_project(
                project_id,
                feature_classes,
                False
            )
            
            # Write results
            output_fc = os.path.join(output_workspace, f"Validation_{project_id}")
            validator.write_results_as_points(violations, output_fc, project_id)
            
            # Summary
            error_count = sum(1 for v in violations if v['severity'] == 'ERROR')
            warning_count = sum(1 for v in violations if v['severity'] == 'WARNING')
            
            messages.addMessage(f"Results: {error_count} errors, {warning_count} warnings")
        
        messages.addMessage(f"\n{'='*60}")
        messages.addMessage("Batch validation complete!")
        
        return

