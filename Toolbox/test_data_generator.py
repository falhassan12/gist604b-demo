"""
Test Data Generator for Spatial Validation Toolbox

Creates sample feature classes with known validation scenarios
for testing the validation engine.

Usage:
    Run in ArcGIS Pro Python window or as standalone script.
"""

import arcpy
import os
import math

# Web Mercator spatial reference (commonly used)
SR_WEB_MERCATOR = arcpy.SpatialReference(3857)

# UTM Zone 12N (for Arizona/Tucson area)
SR_UTM_12N = arcpy.SpatialReference(32612)


def create_test_geodatabase(output_folder, gdb_name="ValidationTest.gdb"):
    """
    Create a file geodatabase for test data
    
    Args:
        output_folder: Folder to create geodatabase in
        gdb_name: Name of geodatabase
        
    Returns:
        Path to created geodatabase
    """
    gdb_path = os.path.join(output_folder, gdb_name)
    
    if arcpy.Exists(gdb_path):
        print(f"Geodatabase already exists: {gdb_path}")
        return gdb_path
    
    arcpy.CreateFileGDB_management(output_folder, gdb_name)
    print(f"Created geodatabase: {gdb_path}")
    
    return gdb_path


def create_infrastructure_features(gdb_path, spatial_reference=SR_WEB_MERCATOR):
    """
    Create sample infrastructure feature classes (existing features to validate against)
    
    Creates:
        - Roads (polyline)
        - Buildings (polygon)
        - Utilities (polyline)
        - Parcels (polygon)
    """
    
    # Base coordinates (adjust for your area of interest)
    # These are in Web Mercator (meters) - roughly Tucson, AZ area
    base_x = -12345000
    base_y = 3812000
    
    # =========================================
    # ROADS - Existing road network
    # =========================================
    roads_fc = os.path.join(gdb_path, "Roads")
    
    if not arcpy.Exists(roads_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Roads", "POLYLINE",
            spatial_reference=spatial_reference
        )
        arcpy.AddField_management(roads_fc, "RoadName", "TEXT", field_length=100)
        arcpy.AddField_management(roads_fc, "RoadType", "TEXT", field_length=50)
        arcpy.AddField_management(roads_fc, "Width", "DOUBLE")
        
        with arcpy.da.InsertCursor(roads_fc, ['SHAPE@', 'RoadName', 'RoadType', 'Width']) as cursor:
            # Main east-west road
            points1 = [
                arcpy.Point(base_x - 500, base_y),
                arcpy.Point(base_x + 500, base_y)
            ]
            cursor.insertRow([arcpy.Polyline(arcpy.Array(points1), spatial_reference), 
                            "Main Street", "Arterial", 24])
            
            # North-south road (perpendicular)
            points2 = [
                arcpy.Point(base_x, base_y - 500),
                arcpy.Point(base_x, base_y + 500)
            ]
            cursor.insertRow([arcpy.Polyline(arcpy.Array(points2), spatial_reference), 
                            "First Avenue", "Collector", 18])
            
            # Diagonal road (for angle testing)
            points3 = [
                arcpy.Point(base_x + 200, base_y - 300),
                arcpy.Point(base_x + 400, base_y + 300)
            ]
            cursor.insertRow([arcpy.Polyline(arcpy.Array(points3), spatial_reference), 
                            "Diagonal Drive", "Local", 12])
        
        print(f"Created: {roads_fc}")
    
    # =========================================
    # BUILDINGS - Existing buildings
    # =========================================
    buildings_fc = os.path.join(gdb_path, "Buildings")
    
    if not arcpy.Exists(buildings_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Buildings", "POLYGON",
            spatial_reference=spatial_reference
        )
        arcpy.AddField_management(buildings_fc, "BuildingType", "TEXT", field_length=50)
        arcpy.AddField_management(buildings_fc, "Height", "DOUBLE")
        
        with arcpy.da.InsertCursor(buildings_fc, ['SHAPE@', 'BuildingType', 'Height']) as cursor:
            # Building 1 - northeast of intersection
            b1 = create_rectangle(base_x + 50, base_y + 50, 30, 20, spatial_reference)
            cursor.insertRow([b1, "Commercial", 10])
            
            # Building 2 - southwest of intersection
            b2 = create_rectangle(base_x - 80, base_y - 80, 25, 25, spatial_reference)
            cursor.insertRow([b2, "Residential", 5])
            
            # Building 3 - near diagonal road
            b3 = create_rectangle(base_x + 300, base_y + 100, 40, 30, spatial_reference)
            cursor.insertRow([b3, "Industrial", 15])
        
        print(f"Created: {buildings_fc}")
    
    # =========================================
    # UTILITIES - Existing utility lines
    # =========================================
    utilities_fc = os.path.join(gdb_path, "Utilities")
    
    if not arcpy.Exists(utilities_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Utilities", "POLYLINE",
            spatial_reference=spatial_reference
        )
        arcpy.AddField_management(utilities_fc, "UTILITY_TYPE", "TEXT", field_length=50)
        arcpy.AddField_management(utilities_fc, "DIAMETER_INCHES", "DOUBLE")
        
        with arcpy.da.InsertCursor(utilities_fc, ['SHAPE@', 'UTILITY_TYPE', 'DIAMETER_INCHES']) as cursor:
            # Water main along Main Street
            points1 = [
                arcpy.Point(base_x - 400, base_y + 10),
                arcpy.Point(base_x + 400, base_y + 10)
            ]
            cursor.insertRow([arcpy.Polyline(arcpy.Array(points1), spatial_reference), 
                            "Water", 12])
            
            # Sewer main along First Avenue
            points2 = [
                arcpy.Point(base_x + 15, base_y - 400),
                arcpy.Point(base_x + 15, base_y + 400)
            ]
            cursor.insertRow([arcpy.Polyline(arcpy.Array(points2), spatial_reference), 
                            "Sewer", 18])
            
            # Gas pipeline (diagonal)
            points3 = [
                arcpy.Point(base_x - 300, base_y - 200),
                arcpy.Point(base_x + 300, base_y + 200)
            ]
            cursor.insertRow([arcpy.Polyline(arcpy.Array(points3), spatial_reference), 
                            "Pipeline", 8])
        
        print(f"Created: {utilities_fc}")
    
    # =========================================
    # PARCELS - Property boundaries
    # =========================================
    parcels_fc = os.path.join(gdb_path, "Parcels")
    
    if not arcpy.Exists(parcels_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Parcels", "POLYGON",
            spatial_reference=spatial_reference
        )
        arcpy.AddField_management(parcels_fc, "ParcelID", "TEXT", field_length=20)
        arcpy.AddField_management(parcels_fc, "Owner", "TEXT", field_length=100)
        arcpy.AddField_management(parcels_fc, "Zoning", "TEXT", field_length=20)
        
        with arcpy.da.InsertCursor(parcels_fc, ['SHAPE@', 'ParcelID', 'Owner', 'Zoning']) as cursor:
            # Parcel 1 - NE quadrant
            p1 = create_rectangle(base_x + 20, base_y + 20, 200, 200, spatial_reference)
            cursor.insertRow([p1, "P001", "Acme Corp", "C-1"])
            
            # Parcel 2 - NW quadrant
            p2 = create_rectangle(base_x - 220, base_y + 20, 200, 200, spatial_reference)
            cursor.insertRow([p2, "P002", "Smith Family Trust", "R-1"])
            
            # Parcel 3 - SW quadrant
            p3 = create_rectangle(base_x - 220, base_y - 220, 200, 200, spatial_reference)
            cursor.insertRow([p3, "P003", "City of Test", "P"])
            
            # Parcel 4 - SE quadrant
            p4 = create_rectangle(base_x + 20, base_y - 220, 200, 200, spatial_reference)
            cursor.insertRow([p4, "P004", "Jones LLC", "I-1"])
        
        print(f"Created: {parcels_fc}")
    
    return {
        'Roads': roads_fc,
        'Buildings': buildings_fc,
        'Utilities': utilities_fc,
        'Parcels': parcels_fc
    }


def create_proposed_features(gdb_path, project_id="TEST001", spatial_reference=SR_WEB_MERCATOR):
    """
    Create proposed feature classes with various validation scenarios
    
    Creates features that will:
        - PASS validation (correct setbacks, angles, containment)
        - FAIL validation (violations for testing)
    """
    
    base_x = -12345000
    base_y = 3812000
    
    # =========================================
    # PROPOSED ROADS - Test intersection angles
    # =========================================
    proposed_roads_fc = os.path.join(gdb_path, f"ProposedRoads_{project_id}")
    
    if not arcpy.Exists(proposed_roads_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, f"ProposedRoads_{project_id}", "POLYLINE",
            spatial_reference=spatial_reference
        )
        arcpy.AddField_management(proposed_roads_fc, "RoadName", "TEXT", field_length=100)
        arcpy.AddField_management(proposed_roads_fc, "Scenario", "TEXT", field_length=50)
        
        with arcpy.da.InsertCursor(proposed_roads_fc, ['SHAPE@', 'RoadName', 'Scenario']) as cursor:
            # Scenario 1: PASS - Perpendicular intersection (90°)
            points1 = [
                arcpy.Point(base_x + 100, base_y - 100),
                arcpy.Point(base_x + 100, base_y + 100)
            ]
            cursor.insertRow([arcpy.Polyline(arcpy.Array(points1), spatial_reference), 
                            "New Street A", "PASS_PERPENDICULAR"])
            
            # Scenario 2: PASS - 45° angle intersection
            points2 = [
                arcpy.Point(base_x - 200, base_y - 100),
                arcpy.Point(base_x - 100, base_y + 100)
            ]
            cursor.insertRow([arcpy.Polyline(arcpy.Array(points2), spatial_reference), 
                            "New Street B", "PASS_45_DEGREE"])
            
            # Scenario 3: FAIL - Acute angle intersection (~15°)
            points3 = [
                arcpy.Point(base_x - 300, base_y - 50),
                arcpy.Point(base_x - 100, base_y + 20)
            ]
            cursor.insertRow([arcpy.Polyline(arcpy.Array(points3), spatial_reference), 
                            "Bad Street C", "FAIL_ACUTE_ANGLE"])
        
        print(f"Created: {proposed_roads_fc}")
    
    # =========================================
    # PROPOSED BUILDINGS - Test setbacks & containment
    # =========================================
    proposed_buildings_fc = os.path.join(gdb_path, f"ProposedBuildings_{project_id}")
    
    if not arcpy.Exists(proposed_buildings_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, f"ProposedBuildings_{project_id}", "POLYGON",
            spatial_reference=spatial_reference
        )
        arcpy.AddField_management(proposed_buildings_fc, "BuildingName", "TEXT", field_length=100)
        arcpy.AddField_management(proposed_buildings_fc, "Scenario", "TEXT", field_length=50)
        
        with arcpy.da.InsertCursor(proposed_buildings_fc, ['SHAPE@', 'BuildingName', 'Scenario']) as cursor:
            # Scenario 1: PASS - Good setback (25m from road), within parcel
            b1 = create_rectangle(base_x + 80, base_y + 80, 30, 25, spatial_reference)
            cursor.insertRow([b1, "Building A", "PASS_SETBACK_CONTAINMENT"])
            
            # Scenario 2: FAIL - Too close to road (5m setback)
            b2 = create_rectangle(base_x - 150, base_y + 5, 20, 20, spatial_reference)
            cursor.insertRow([b2, "Building B", "FAIL_SETBACK"])
            
            # Scenario 3: FAIL - Outside parcel boundary
            b3 = create_rectangle(base_x + 250, base_y + 250, 25, 25, spatial_reference)
            cursor.insertRow([b3, "Building C", "FAIL_CONTAINMENT"])
            
            # Scenario 4: FAIL - Too close to existing building
            b4 = create_rectangle(base_x + 45, base_y + 45, 15, 15, spatial_reference)
            cursor.insertRow([b4, "Building D", "FAIL_SEPARATION"])
        
        print(f"Created: {proposed_buildings_fc}")
    
    # =========================================
    # PROPOSED UTILITIES - Test crossing angles
    # =========================================
    proposed_utilities_fc = os.path.join(gdb_path, f"ProposedUtilities_{project_id}")
    
    if not arcpy.Exists(proposed_utilities_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, f"ProposedUtilities_{project_id}", "POLYLINE",
            spatial_reference=spatial_reference
        )
        arcpy.AddField_management(proposed_utilities_fc, "UTILITY_TYPE", "TEXT", field_length=50)
        arcpy.AddField_management(proposed_utilities_fc, "DIAMETER_INCHES", "DOUBLE")
        arcpy.AddField_management(proposed_utilities_fc, "Scenario", "TEXT", field_length=50)
        
        with arcpy.da.InsertCursor(proposed_utilities_fc, 
                                    ['SHAPE@', 'UTILITY_TYPE', 'DIAMETER_INCHES', 'Scenario']) as cursor:
            # Scenario 1: PASS - Perpendicular road crossing
            points1 = [
                arcpy.Point(base_x + 150, base_y - 50),
                arcpy.Point(base_x + 150, base_y + 50)
            ]
            cursor.insertRow([arcpy.Polyline(arcpy.Array(points1), spatial_reference), 
                            "Water", 6, "PASS_CROSSING_ANGLE"])
            
            # Scenario 2: WARNING - Shallow road crossing (~30°)
            points2 = [
                arcpy.Point(base_x - 150, base_y - 30),
                arcpy.Point(base_x - 50, base_y + 50)
            ]
            cursor.insertRow([arcpy.Polyline(arcpy.Array(points2), spatial_reference), 
                            "Sewer", 8, "WARN_SHALLOW_CROSSING"])
            
            # Scenario 3: FAIL - Too close to existing pipeline
            points3 = [
                arcpy.Point(base_x - 280, base_y - 190),
                arcpy.Point(base_x + 280, base_y + 190)
            ]
            cursor.insertRow([arcpy.Polyline(arcpy.Array(points3), spatial_reference), 
                            "Pipeline", 12, "FAIL_PIPELINE_SEPARATION"])
        
        print(f"Created: {proposed_utilities_fc}")
    
    return {
        'ProposedRoads': proposed_roads_fc,
        'ProposedBuildings': proposed_buildings_fc,
        'ProposedUtilities': proposed_utilities_fc
    }


def create_rectangle(center_x, center_y, width, height, spatial_reference):
    """
    Create a rectangular polygon geometry
    
    Args:
        center_x: Center X coordinate
        center_y: Center Y coordinate
        width: Rectangle width
        height: Rectangle height
        spatial_reference: Spatial reference for geometry
        
    Returns:
        arcpy.Polygon geometry
    """
    half_w = width / 2
    half_h = height / 2
    
    points = [
        arcpy.Point(center_x - half_w, center_y - half_h),
        arcpy.Point(center_x + half_w, center_y - half_h),
        arcpy.Point(center_x + half_w, center_y + half_h),
        arcpy.Point(center_x - half_w, center_y + half_h),
        arcpy.Point(center_x - half_w, center_y - half_h)  # Close ring
    ]
    
    return arcpy.Polygon(arcpy.Array(points), spatial_reference)


def create_all_test_data(output_folder, project_id="TEST001"):
    """
    Create complete test dataset
    
    Args:
        output_folder: Folder to create geodatabase in
        project_id: Project identifier for proposed features
        
    Returns:
        Dictionary of all created feature classes
    """
    # Create geodatabase
    gdb_path = create_test_geodatabase(output_folder)
    
    # Create infrastructure (existing) features
    infrastructure = create_infrastructure_features(gdb_path)
    
    # Create proposed features
    proposed = create_proposed_features(gdb_path, project_id)
    
    print("\n" + "=" * 60)
    print("TEST DATA CREATION COMPLETE")
    print("=" * 60)
    print(f"\nGeodatabase: {gdb_path}")
    print("\nInfrastructure Feature Classes:")
    for name, path in infrastructure.items():
        print(f"  - {name}")
    print("\nProposed Feature Classes:")
    for name, path in proposed.items():
        print(f"  - {name}")
    print("\nExpected Validation Results:")
    print("  Roads:")
    print("    - New Street A: PASS (perpendicular)")
    print("    - New Street B: PASS (45° angle)")
    print("    - Bad Street C: FAIL (acute angle ~15°)")
    print("  Buildings:")
    print("    - Building A: PASS (good setback & containment)")
    print("    - Building B: FAIL (setback violation)")
    print("    - Building C: FAIL (containment violation)")
    print("    - Building D: FAIL (separation violation)")
    print("  Utilities:")
    print("    - Water Line: PASS (perpendicular crossing)")
    print("    - Sewer Line: WARNING (shallow crossing)")
    print("    - Pipeline: FAIL (separation violation)")
    print("=" * 60)
    
    return {
        'geodatabase': gdb_path,
        'infrastructure': infrastructure,
        'proposed': proposed
    }


# ============================================================================
# MAIN - Run when script is executed directly
# ============================================================================

if __name__ == "__main__":
    import tempfile
    
    # Create test data in temp folder
    output_folder = tempfile.gettempdir()
    print(f"Creating test data in: {output_folder}")
    
    result = create_all_test_data(output_folder, "TEST001")
    
    print(f"\nTo use in ArcGIS Pro:")
    print(f"1. Add connection to: {result['geodatabase']}")
    print(f"2. Run Validate Project tool with Project ID: TEST001")

