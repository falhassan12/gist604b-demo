"""
Spatial Validation Engine
Core validation logic for the ArcGIS Spatial Validation Toolbox

This module contains the SpatialValidator class which executes
configurable spatial rules against feature classes.
"""

import arcpy
import os
import json
import math
from datetime import datetime
from collections import defaultdict


class SpatialValidator:
    """
    Core spatial validation engine
    
    Validates feature classes against configurable rules defined in JSON.
    Supports various rule types including distance checks, angle validation,
    containment verification, and attribute-based calculations.
    """
    
    def __init__(self, rules_config_path, messages=None, skip_config=False):
        """
        Initialize validator with rule configuration
        
        Args:
            rules_config_path: Path to JSON configuration file
            messages: ArcPy messages object for logging
            skip_config: If True, skip loading config (for ad-hoc validation)
        """
        self.messages = messages or arcpy
        self._infrastructure_cache = {}
        
        if skip_config:
            self.rules = {'rules': [], 'global_settings': {}}
            self.global_settings = {}
        else:
            self.rules = self._load_rules(rules_config_path)
            self.global_settings = self.rules.get('global_settings', {})
    
    def _load_rules(self, config_path):
        """Load rule configuration from JSON"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Rule configuration not found: {config_path}")
            
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self._log(f"Loaded {len(config.get('rules', []))} rules from configuration")
        return config
    
    def _log(self, message, level='message'):
        """Log message using appropriate method"""
        if hasattr(self.messages, 'addMessage'):
            if level == 'warning':
                self.messages.addWarning(message)
            elif level == 'error':
                self.messages.addErrorMessage(message)
            else:
                self.messages.addMessage(message)
        else:
            print(message)
    
    def validate_project(self, project_id, feature_classes, stop_on_error=False):
        """
        Validate all feature classes against applicable rules
        
        Args:
            project_id: Project identifier for tracking
            feature_classes: List of feature class paths to validate
            stop_on_error: If True, stop on first ERROR-level violation
            
        Returns:
            List of violation dictionaries
        """
        all_violations = []
        
        for fc in feature_classes:
            fc_name = os.path.basename(fc)
            
            # Find applicable rules for this feature class
            applicable_rules = [
                r for r in self.rules['rules'] 
                if r.get('active', True) and self._rule_applies_to_fc(r, fc_name)
            ]
            
            self._log(f"\nValidating {fc_name} ({len(applicable_rules)} rules)")
            
            for rule in applicable_rules:
                self._log(f"  ► {rule['rule_name']}")
                
                try:
                    violations = self._execute_rule(fc, rule['target_fc'], rule, project_id)
                    all_violations.extend(violations)
                    
                    if violations:
                        error_count = sum(1 for v in violations if v['severity'] == 'ERROR')
                        warning_count = sum(1 for v in violations if v['severity'] == 'WARNING')
                        self._log(f"    Found {error_count} errors, {warning_count} warnings")
                    else:
                        self._log(f"    ✓ Passed")
                    
                    if stop_on_error and any(v['severity'] == 'ERROR' for v in violations):
                        self._log("Stopping validation due to error", 'warning')
                        return all_violations
                        
                except Exception as e:
                    self._log(f"    ✗ Rule execution failed: {str(e)}", 'warning')
        
        return all_violations
    
    def _rule_applies_to_fc(self, rule, fc_name):
        """Check if a rule applies to a given feature class"""
        source_fc = rule.get('source_fc', '')
        # Match by exact name or by suffix
        return (source_fc.endswith(fc_name) or 
                fc_name.endswith(source_fc.split('.')[-1]) or
                source_fc.split('.')[-1] in fc_name)
    
    def _execute_rule(self, source_fc, target_fc, rule, project_id):
        """
        Execute a single validation rule
        
        Args:
            source_fc: Source feature class path
            target_fc: Target feature class path (for comparison)
            rule: Rule dictionary with type and parameters
            project_id: Project identifier
            
        Returns:
            List of violation dictionaries
        """
        rule_type = rule['rule_type']
        params = rule.get('parameters', {})
        
        # Validate target FC exists
        if not arcpy.Exists(target_fc):
            self._log(f"    Target feature class not found: {target_fc}", 'warning')
            return []
        
        # Dispatch to appropriate validation method
        dispatch = {
            'MINIMUM_DISTANCE': self._check_minimum_distance,
            'MAXIMUM_DISTANCE': self._check_maximum_distance,
            'INTERSECTION_ANGLE': self._check_intersection_angle,
            'CROSSING_ANGLE': self._check_crossing_angle,
            'CONTAINMENT': self._check_containment,
            'ATTRIBUTE_DISTANCE': self._check_attribute_distance,
            'BUFFER_OVERLAP': self._check_buffer_overlap,
        }
        
        handler = dispatch.get(rule_type)
        if handler:
            return handler(source_fc, target_fc, rule, project_id)
        else:
            self._log(f"Unknown rule type: {rule_type}", 'warning')
            return []
    
    def _check_minimum_distance(self, source_fc, target_fc, rule, project_id):
        """
        Check minimum distance between features
        
        Validates that source features maintain at least the specified
        minimum distance from all target features.
        """
        violations = []
        min_distance = rule['parameters']['min_distance_meters']
        
        with arcpy.da.SearchCursor(source_fc, ['OID@', 'SHAPE@']) as source_cursor:
            for source_oid, source_geom in source_cursor:
                if source_geom is None:
                    continue
                
                # Create search buffer for efficiency
                search_buffer = source_geom.buffer(min_distance * 2)
                
                with arcpy.da.SearchCursor(
                    target_fc, 
                    ['OID@', 'SHAPE@'],
                    spatial_reference=source_geom.spatialReference
                ) as target_cursor:
                    
                    for target_oid, target_geom in target_cursor:
                        if target_geom is None:
                            continue
                        
                        # Quick spatial filter
                        if not search_buffer.overlaps(target_geom) and \
                           not search_buffer.contains(target_geom) and \
                           not target_geom.overlaps(search_buffer):
                            continue
                        
                        # Calculate precise distance
                        distance = source_geom.distanceTo(target_geom)
                        
                        if distance < min_distance:
                            violation_point = self._get_midpoint(source_geom, target_geom)
                            
                            violations.append({
                                'project_id': project_id,
                                'rule_code': rule['rule_code'],
                                'rule_name': rule['rule_name'],
                                'severity': rule['severity'],
                                'source_fc': os.path.basename(source_fc),
                                'source_oid': source_oid,
                                'target_fc': os.path.basename(target_fc),
                                'target_oid': target_oid,
                                'measured_value': round(distance, 2),
                                'threshold_value': min_distance,
                                'message': f"Distance {distance:.2f}m is less than required {min_distance}m",
                                'violation_geometry': violation_point
                            })
        
        return violations
    
    def _check_maximum_distance(self, source_fc, target_fc, rule, project_id):
        """
        Check maximum distance between features
        
        Validates that source features are within the specified maximum
        distance from at least one target feature (e.g., access to utilities).
        """
        violations = []
        max_distance = rule['parameters']['max_distance_meters']
        
        with arcpy.da.SearchCursor(source_fc, ['OID@', 'SHAPE@']) as source_cursor:
            for source_oid, source_geom in source_cursor:
                if source_geom is None:
                    continue
                
                min_found_distance = float('inf')
                nearest_target_oid = None
                
                with arcpy.da.SearchCursor(target_fc, ['OID@', 'SHAPE@']) as target_cursor:
                    for target_oid, target_geom in target_cursor:
                        if target_geom is None:
                            continue
                        
                        distance = source_geom.distanceTo(target_geom)
                        if distance < min_found_distance:
                            min_found_distance = distance
                            nearest_target_oid = target_oid
                
                if min_found_distance > max_distance:
                    violations.append({
                        'project_id': project_id,
                        'rule_code': rule['rule_code'],
                        'rule_name': rule['rule_name'],
                        'severity': rule['severity'],
                        'source_fc': os.path.basename(source_fc),
                        'source_oid': source_oid,
                        'target_fc': os.path.basename(target_fc),
                        'target_oid': nearest_target_oid,
                        'measured_value': round(min_found_distance, 2),
                        'threshold_value': max_distance,
                        'message': f"Nearest distance {min_found_distance:.2f}m exceeds maximum {max_distance}m",
                        'violation_geometry': source_geom.centroid if hasattr(source_geom, 'centroid') else source_geom.firstPoint
                    })
        
        return violations
    
    def _check_intersection_angle(self, source_fc, target_fc, rule, project_id):
        """
        Check angles at line intersections
        
        Validates that lines intersect at angles within the specified range.
        """
        violations = []
        min_angle = rule['parameters']['min_angle_degrees']
        max_angle = rule['parameters'].get('max_angle_degrees', 180)
        
        with arcpy.da.SearchCursor(source_fc, ['OID@', 'SHAPE@']) as source_cursor:
            for source_oid, source_geom in source_cursor:
                
                if source_geom is None or source_geom.type != 'polyline':
                    continue
                
                with arcpy.da.SearchCursor(target_fc, ['OID@', 'SHAPE@']) as target_cursor:
                    for target_oid, target_geom in target_cursor:
                        
                        if target_geom is None or target_geom.type != 'polyline':
                            continue
                        
                        if not source_geom.crosses(target_geom) and not source_geom.touches(target_geom):
                            continue
                        
                        # Get intersection point(s)
                        intersection = source_geom.intersect(target_geom, 1)  # 1 = point
                        
                        if intersection.isEmpty:
                            continue
                        
                        # Calculate angle at intersection
                        angle = self._calculate_line_angle(
                            source_geom, 
                            target_geom, 
                            intersection.firstPoint
                        )
                        
                        if angle < min_angle or angle > max_angle:
                            violations.append({
                                'project_id': project_id,
                                'rule_code': rule['rule_code'],
                                'rule_name': rule['rule_name'],
                                'severity': rule['severity'],
                                'source_fc': os.path.basename(source_fc),
                                'source_oid': source_oid,
                                'target_fc': os.path.basename(target_fc),
                                'target_oid': target_oid,
                                'measured_value': round(angle, 1),
                                'threshold_value': f"{min_angle}-{max_angle}",
                                'message': f"Intersection angle {angle:.1f}° outside valid range [{min_angle}°-{max_angle}°]",
                                'violation_geometry': intersection.firstPoint
                            })
        
        return violations
    
    def _check_crossing_angle(self, source_fc, target_fc, rule, project_id):
        """Check angles when lines cross (alias for intersection angle)"""
        return self._check_intersection_angle(source_fc, target_fc, rule, project_id)
    
    def _check_containment(self, source_fc, target_fc, rule, project_id):
        """
        Check if features are contained within target polygons
        
        Validates that source features are completely within (or partially
        within based on containment_type) target polygon features.
        """
        violations = []
        tolerance = rule['parameters'].get('tolerance_meters', 0.5)
        containment_type = rule['parameters'].get('containment_type', 'COMPLETELY_WITHIN')
        
        with arcpy.da.SearchCursor(source_fc, ['OID@', 'SHAPE@']) as source_cursor:
            for source_oid, source_geom in source_cursor:
                if source_geom is None:
                    continue
                
                # Buffer slightly inward to handle edge cases
                if tolerance > 0 and source_geom.type == 'polygon':
                    test_geom = source_geom.buffer(-tolerance)
                else:
                    test_geom = source_geom
                
                # Check if contained in any target polygon
                contained = False
                
                with arcpy.da.SearchCursor(target_fc, ['OID@', 'SHAPE@']) as target_cursor:
                    for target_oid, target_geom in target_cursor:
                        if target_geom is None or target_geom.type != 'polygon':
                            continue
                        
                        if containment_type == 'COMPLETELY_WITHIN':
                            if target_geom.contains(test_geom):
                                contained = True
                                break
                        else:  # PARTIALLY_WITHIN
                            if target_geom.overlaps(test_geom) or target_geom.contains(test_geom):
                                contained = True
                                break
                
                if not contained:
                    centroid = source_geom.centroid if hasattr(source_geom, 'centroid') else source_geom.firstPoint
                    
                    violations.append({
                        'project_id': project_id,
                        'rule_code': rule['rule_code'],
                        'rule_name': rule['rule_name'],
                        'severity': rule['severity'],
                        'source_fc': os.path.basename(source_fc),
                        'source_oid': source_oid,
                        'target_fc': os.path.basename(target_fc),
                        'target_oid': None,
                        'measured_value': 0,
                        'threshold_value': 1,
                        'message': "Feature not contained within required area",
                        'violation_geometry': centroid
                    })
        
        return violations
    
    def _check_attribute_distance(self, source_fc, target_fc, rule, project_id):
        """
        Check distance with thresholds based on attribute values
        
        Calculates required distance dynamically based on an attribute
        field value (e.g., pipe diameter affects required separation).
        """
        violations = []
        base_distance = rule['parameters']['base_distance_meters']
        attribute_field = rule['parameters']['attribute_field']
        multiplier = rule['parameters'].get('multiplier', 1.0)
        where_clause = rule['parameters'].get('where_clause', None)
        
        # Check if attribute field exists
        field_names = [f.name for f in arcpy.ListFields(source_fc)]
        if attribute_field not in field_names:
            self._log(f"Attribute field {attribute_field} not found in {source_fc}", 'warning')
            return violations
        
        fields = ['OID@', 'SHAPE@', attribute_field]
        
        with arcpy.da.SearchCursor(source_fc, fields, where_clause) as source_cursor:
            for source_oid, source_geom, attribute_value in source_cursor:
                if source_geom is None:
                    continue
                
                # Calculate required distance based on attribute
                if attribute_value is None:
                    required_distance = base_distance
                else:
                    required_distance = base_distance + (float(attribute_value) * multiplier)
                
                # Check distances to target features
                search_buffer = source_geom.buffer(required_distance * 2)
                
                with arcpy.da.SearchCursor(target_fc, ['OID@', 'SHAPE@']) as target_cursor:
                    for target_oid, target_geom in target_cursor:
                        if target_geom is None:
                            continue
                        
                        if not search_buffer.overlaps(target_geom) and \
                           not search_buffer.contains(target_geom):
                            continue
                        
                        distance = source_geom.distanceTo(target_geom)
                        
                        if distance < required_distance:
                            violation_point = self._get_midpoint(source_geom, target_geom)
                            
                            violations.append({
                                'project_id': project_id,
                                'rule_code': rule['rule_code'],
                                'rule_name': rule['rule_name'],
                                'severity': rule['severity'],
                                'source_fc': os.path.basename(source_fc),
                                'source_oid': source_oid,
                                'target_fc': os.path.basename(target_fc),
                                'target_oid': target_oid,
                                'measured_value': round(distance, 2),
                                'threshold_value': round(required_distance, 2),
                                'message': f"Distance {distance:.2f}m less than required {required_distance:.2f}m (based on {attribute_field}={attribute_value})",
                                'violation_geometry': violation_point
                            })
        
        return violations
    
    def _check_buffer_overlap(self, source_fc, target_fc, rule, project_id):
        """
        Check if buffered features overlap
        
        Creates buffers around source features and checks for
        overlap with target features.
        """
        violations = []
        buffer_distance = rule['parameters'].get('buffer_distance_meters', 10)
        
        with arcpy.da.SearchCursor(source_fc, ['OID@', 'SHAPE@']) as source_cursor:
            for source_oid, source_geom in source_cursor:
                if source_geom is None:
                    continue
                
                buffered_geom = source_geom.buffer(buffer_distance)
                
                with arcpy.da.SearchCursor(target_fc, ['OID@', 'SHAPE@']) as target_cursor:
                    for target_oid, target_geom in target_cursor:
                        if target_geom is None:
                            continue
                        
                        if buffered_geom.overlaps(target_geom) or buffered_geom.contains(target_geom):
                            violations.append({
                                'project_id': project_id,
                                'rule_code': rule['rule_code'],
                                'rule_name': rule['rule_name'],
                                'severity': rule['severity'],
                                'source_fc': os.path.basename(source_fc),
                                'source_oid': source_oid,
                                'target_fc': os.path.basename(target_fc),
                                'target_oid': target_oid,
                                'measured_value': buffer_distance,
                                'threshold_value': buffer_distance,
                                'message': f"Feature buffer ({buffer_distance}m) overlaps with target",
                                'violation_geometry': source_geom.centroid if hasattr(source_geom, 'centroid') else source_geom.firstPoint
                            })
        
        return violations
    
    def _calculate_line_angle(self, line1, line2, intersection_point):
        """
        Calculate acute angle between two lines at intersection point
        
        Args:
            line1: First polyline geometry
            line2: Second polyline geometry
            intersection_point: Point where lines intersect
            
        Returns:
            Angle in degrees (0-90, always acute)
        """
        try:
            # Get distance along line1 to intersection
            dist1 = line1.measureOnLine(intersection_point)
            
            # Get points slightly before and after intersection on line1
            offset = min(1.0, line1.length * 0.1)  # 1 meter or 10% of length
            point_before_1 = line1.positionAlongLine(max(0, dist1 - offset))
            point_after_1 = line1.positionAlongLine(min(line1.length, dist1 + offset))
            
            # Calculate azimuth for line1
            azimuth1 = math.atan2(
                point_after_1.firstPoint.Y - point_before_1.firstPoint.Y,
                point_after_1.firstPoint.X - point_before_1.firstPoint.X
            )
            
            # Repeat for line2
            dist2 = line2.measureOnLine(intersection_point)
            offset = min(1.0, line2.length * 0.1)
            point_before_2 = line2.positionAlongLine(max(0, dist2 - offset))
            point_after_2 = line2.positionAlongLine(min(line2.length, dist2 + offset))
            
            azimuth2 = math.atan2(
                point_after_2.firstPoint.Y - point_before_2.firstPoint.Y,
                point_after_2.firstPoint.X - point_before_2.firstPoint.X
            )
            
            # Calculate angle between azimuths
            angle_rad = abs(azimuth1 - azimuth2)
            
            # Normalize to acute angle (0-90 degrees)
            angle_deg = math.degrees(angle_rad)
            if angle_deg > 180:
                angle_deg = 360 - angle_deg
            if angle_deg > 90:
                angle_deg = 180 - angle_deg
            
            return angle_deg
            
        except Exception:
            # Fallback to 90 degrees if calculation fails
            return 90.0
    
    def _get_midpoint(self, geom1, geom2):
        """Get midpoint between two geometries"""
        try:
            # Get centroids or first points
            if hasattr(geom1, 'centroid') and geom1.centroid:
                p1 = geom1.centroid
            elif geom1.firstPoint:
                p1 = geom1.firstPoint
            else:
                return None
            
            if hasattr(geom2, 'centroid') and geom2.centroid:
                p2 = geom2.centroid
            elif geom2.firstPoint:
                p2 = geom2.firstPoint
            else:
                return p1
            
            # Calculate midpoint
            mid_x = (p1.X + p2.X) / 2
            mid_y = (p1.Y + p2.Y) / 2
            
            return arcpy.Point(mid_x, mid_y)
            
        except Exception:
            return geom1.firstPoint if geom1.firstPoint else None
    
    def write_results(self, violations, results_table, project_id):
        """
        Write validation results to output table (non-spatial)
        
        Args:
            violations: List of violation dictionaries
            results_table: Output table path
            project_id: Project identifier
        """
        # Create table if it doesn't exist
        if not arcpy.Exists(results_table):
            self._create_results_table(results_table)
        
        # Insert violations
        fields = [
            'ProjectID', 'RuleCode', 'RuleName', 'Severity',
            'SourceFC', 'SourceOID', 'TargetFC', 'TargetOID',
            'MeasuredValue', 'ThresholdValue', 'Message',
            'ValidationDate', 'ValidatedBy'
        ]
        
        with arcpy.da.InsertCursor(results_table, fields) as cursor:
            for v in violations:
                cursor.insertRow([
                    v['project_id'],
                    v['rule_code'],
                    v['rule_name'],
                    v['severity'],
                    v['source_fc'],
                    v['source_oid'],
                    v.get('target_fc'),
                    v.get('target_oid'),
                    v.get('measured_value'),
                    str(v.get('threshold_value', '')),
                    v['message'],
                    datetime.now(),
                    self._get_username()
                ])
        
        self._log(f"\nWrote {len(violations)} violations to {results_table}")
    
    def write_results_as_points(self, violations, output_fc, project_id):
        """
        Write validation results as point feature class
        
        Creates a point feature class with violation locations for
        visualization in ArcGIS Pro.
        
        Args:
            violations: List of violation dictionaries
            output_fc: Output feature class path
            project_id: Project identifier
        """
        # Determine spatial reference from first violation
        sr = arcpy.SpatialReference(3857)  # Default to Web Mercator
        for v in violations:
            if v.get('violation_geometry'):
                # Try to get SR from geometry
                break
        
        # Create feature class
        workspace, fc_name = os.path.split(output_fc)
        
        if arcpy.Exists(output_fc):
            arcpy.Delete_management(output_fc)
        
        arcpy.CreateFeatureclass_management(
            workspace, fc_name, "POINT",
            spatial_reference=sr
        )
        
        # Add fields
        arcpy.AddField_management(output_fc, "ProjectID", "TEXT", field_length=50)
        arcpy.AddField_management(output_fc, "RuleCode", "TEXT", field_length=50)
        arcpy.AddField_management(output_fc, "RuleName", "TEXT", field_length=200)
        arcpy.AddField_management(output_fc, "Severity", "TEXT", field_length=20)
        arcpy.AddField_management(output_fc, "SourceFC", "TEXT", field_length=100)
        arcpy.AddField_management(output_fc, "SourceOID", "LONG")
        arcpy.AddField_management(output_fc, "TargetFC", "TEXT", field_length=100)
        arcpy.AddField_management(output_fc, "TargetOID", "LONG")
        arcpy.AddField_management(output_fc, "MeasuredValue", "DOUBLE")
        arcpy.AddField_management(output_fc, "ThresholdValue", "TEXT", field_length=50)
        arcpy.AddField_management(output_fc, "Message", "TEXT", field_length=500)
        arcpy.AddField_management(output_fc, "ValidationDate", "DATE")
        arcpy.AddField_management(output_fc, "ValidatedBy", "TEXT", field_length=100)
        
        # Insert violations
        fields = [
            'SHAPE@', 'ProjectID', 'RuleCode', 'RuleName', 'Severity',
            'SourceFC', 'SourceOID', 'TargetFC', 'TargetOID',
            'MeasuredValue', 'ThresholdValue', 'Message',
            'ValidationDate', 'ValidatedBy'
        ]
        
        with arcpy.da.InsertCursor(output_fc, fields) as cursor:
            for v in violations:
                geom = v.get('violation_geometry')
                if geom is None:
                    continue
                
                # Convert point to geometry if needed
                if isinstance(geom, arcpy.Point):
                    point_geom = arcpy.PointGeometry(geom, sr)
                else:
                    point_geom = geom
                
                cursor.insertRow([
                    point_geom,
                    v['project_id'],
                    v['rule_code'],
                    v['rule_name'],
                    v['severity'],
                    v['source_fc'],
                    v['source_oid'],
                    v.get('target_fc'),
                    v.get('target_oid'),
                    v.get('measured_value'),
                    str(v.get('threshold_value', '')),
                    v['message'],
                    datetime.now(),
                    self._get_username()
                ])
        
        self._log(f"\nWrote {len(violations)} violation points to {output_fc}")
    
    def _create_results_table(self, table_path):
        """Create validation results table"""
        workspace, table_name = os.path.split(table_path)
        
        arcpy.CreateTable_management(workspace, table_name)
        
        # Add fields
        arcpy.AddField_management(table_path, "ProjectID", "TEXT", field_length=50)
        arcpy.AddField_management(table_path, "RuleCode", "TEXT", field_length=50)
        arcpy.AddField_management(table_path, "RuleName", "TEXT", field_length=200)
        arcpy.AddField_management(table_path, "Severity", "TEXT", field_length=20)
        arcpy.AddField_management(table_path, "SourceFC", "TEXT", field_length=100)
        arcpy.AddField_management(table_path, "SourceOID", "LONG")
        arcpy.AddField_management(table_path, "TargetFC", "TEXT", field_length=100)
        arcpy.AddField_management(table_path, "TargetOID", "LONG")
        arcpy.AddField_management(table_path, "MeasuredValue", "DOUBLE")
        arcpy.AddField_management(table_path, "ThresholdValue", "TEXT", field_length=50)
        arcpy.AddField_management(table_path, "Message", "TEXT", field_length=500)
        arcpy.AddField_management(table_path, "ValidationDate", "DATE")
        arcpy.AddField_management(table_path, "ValidatedBy", "TEXT", field_length=100)
    
    def _get_username(self):
        """Get current username"""
        try:
            return os.environ.get('USERNAME', os.environ.get('USER', 'unknown'))
        except Exception:
            return 'unknown'

