# LUP_TestData.py
# ---------------------------------------------------------------------------
# Test Data Generator for LUP Spatial Validation (Aramco-style)
#
# Creates a file geodatabase with infrastructure + proposed LUP sites
# designed to trigger PASS / WARNING / ERROR cases for rules_config.json
#
# Usage:
#   - Run this script in ArcGIS Pro Python window
#   - أو كـ standalone script مع ArcPy متثبت
# ---------------------------------------------------------------------------

import arcpy
import os
import tempfile

# نستخدم Web Mercator (متر، سهل نحسب المسافات)
SR_WEB_MERCATOR = arcpy.SpatialReference(3857)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_rectangle(center_x, center_y, width, height, spatial_reference):
    """Create a rectangular polygon geometry centered at (x,y)."""
    half_w = width / 2.0
    half_h = height / 2.0

    points = [
        arcpy.Point(center_x - half_w, center_y - half_h),
        arcpy.Point(center_x + half_w, center_y - half_h),
        arcpy.Point(center_x + half_w, center_y + half_h),
        arcpy.Point(center_x - half_w, center_y + half_h),
        arcpy.Point(center_x - half_w, center_y - half_h)  # close ring
    ]
    return arcpy.Polygon(arcpy.Array(points), spatial_reference)


# ---------------------------------------------------------------------------
# إنشاء الـ GDB
# ---------------------------------------------------------------------------

def create_lup_geodatabase(output_folder, gdb_name="LUP_ValidationTest.gdb"):
    gdb_path = os.path.join(output_folder, gdb_name)

    if arcpy.Exists(gdb_path):
        print(f"Geodatabase already exists: {gdb_path}")
        return gdb_path

    arcpy.CreateFileGDB_management(output_folder, gdb_name)
    print(f"Created geodatabase: {gdb_path}")
    return gdb_path


# ---------------------------------------------------------------------------
# إنشاء طبقات البنية التحتية (Infrastructure)
# ---------------------------------------------------------------------------

def create_lup_infrastructure_features(gdb_path, spatial_reference=SR_WEB_MERCATOR):
    """
    Creates infrastructure feature classes needed by rules_config.json:
    - Company_Reservation (polygon)
    - Released_Areas (polygon)
    - Disputed_Areas (polygon)
    - Five_KM_Influence_Zone (polygon)
    - Pipelines (polyline)
    - Pipeline_ROW (polygon)
    - Flowlines (polyline)
    - Powerline_OHTL (polyline)
    - Powerline_ROW (polygon)
    - Fiber_Optic_Cable (polyline)
    - Communication_Cable (polyline)
    - Roads (polyline)
    - Highways (polyline)
    - Wells (point)
    - Hazard_Zones (polygon)
    - Environmental_Buffers (polygon)
    - GOSP_Facilities (polygon)
    - Gas_Plants (polygon)
    - Substations (polygon)
    - Pump_Stations (polygon)
    - Schools (polygon)
    - Hospitals (polygon)
    - Industrial_Facilities (polygon)
    - ResidentialAreas (polygon)
    - Utilities (polyline)
    - ROW_Corridors (polygon)
    - Voltage_Influence_Zone (polygon)
    - Airport_Protection_Zones (polygon)
    """

    base_x = -12345000  # موقع افتراضي
    base_y = 3812000

    # =============================== Company_Reservation =====================
    fc = os.path.join(gdb_path, "Company_Reservation")
    if not arcpy.Exists(fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Company_Reservation", "POLYGON",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(fc, ["SHAPE@"]) as cur:
            poly = create_rectangle(base_x, base_y, 2000, 2000, spatial_reference)
            cur.insertRow([poly])
        print(f"Created: {fc}")

    # =============================== Released_Areas ==========================
    fc = os.path.join(gdb_path, "Released_Areas")
    if not arcpy.Exists(fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Released_Areas", "POLYGON",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(fc, ["SHAPE@"]) as cur:
            poly = create_rectangle(base_x + 900, base_y + 900, 600, 600, spatial_reference)
            cur.insertRow([poly])
        print(f"Created: {fc}")

    # =============================== Disputed_Areas ==========================
    fc = os.path.join(gdb_path, "Disputed_Areas")
    if not arcpy.Exists(fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Disputed_Areas", "POLYGON",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(fc, ["SHAPE@"]) as cur:
            poly = create_rectangle(base_x - 900, base_y + 900, 500, 500, spatial_reference)
            cur.insertRow([poly])
        print(f"Created: {fc}")

    # =============================== Five_KM_Influence_Zone ==================
    fc = os.path.join(gdb_path, "Five_KM_Influence_Zone")
    if not arcpy.Exists(fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Five_KM_Influence_Zone", "POLYGON",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(fc, ["SHAPE@"]) as cur:
            # مستطيل كبير يمثل نطاق 5 كم تقريباً
            poly = create_rectangle(base_x, base_y, 10000, 10000, spatial_reference)
            cur.insertRow([poly])
        print(f"Created: {fc}")

    # =============================== Roads ===================================
    roads_fc = os.path.join(gdb_path, "Roads")
    if not arcpy.Exists(roads_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Roads", "POLYLINE",
            spatial_reference=spatial_reference
        )
        arcpy.AddField_management(roads_fc, "RoadName", "TEXT", field_length=100)
        with arcpy.da.InsertCursor(roads_fc, ["SHAPE@", "RoadName"]) as cur:
            # طريق رئيسي شرق-غرب
            pts = [
                arcpy.Point(base_x - 1000, base_y),
                arcpy.Point(base_x + 1000, base_y)
            ]
            cur.insertRow([arcpy.Polyline(arcpy.Array(pts), spatial_reference), "Main Road"])
        print(f"Created: {roads_fc}")

    # =============================== Highways ================================
    hw_fc = os.path.join(gdb_path, "Highways")
    if not arcpy.Exists(hw_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Highways", "POLYLINE",
            spatial_reference=spatial_reference
        )
        arcpy.AddField_management(hw_fc, "HwyName", "TEXT", field_length=100)
        with arcpy.da.InsertCursor(hw_fc, ["SHAPE@", "HwyName"]) as cur:
            pts = [
                arcpy.Point(base_x - 1500, base_y - 800),
                arcpy.Point(base_x + 1500, base_y - 800)
            ]
            cur.insertRow([arcpy.Polyline(arcpy.Array(pts), spatial_reference), "HWY-1"])
        print(f"Created: {hw_fc}")

    # =============================== Pipelines ===============================
    pipe_fc = os.path.join(gdb_path, "Pipelines")
    if not arcpy.Exists(pipe_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Pipelines", "POLYLINE",
            spatial_reference=spatial_reference
        )
        arcpy.AddField_management(pipe_fc, "DIAMETER_INCHES", "DOUBLE")
        with arcpy.da.InsertCursor(pipe_fc, ["SHAPE@", "DIAMETER_INCHES"]) as cur:
            pts = [
                arcpy.Point(base_x - 1000, base_y + 400),
                arcpy.Point(base_x + 1000, base_y + 400)
            ]
            cur.insertRow([arcpy.Polyline(arcpy.Array(pts), spatial_reference), 30])
        print(f"Created: {pipe_fc}")

    # =============================== Pipeline_ROW ============================
    row_fc = os.path.join(gdb_path, "Pipeline_ROW")
    if not arcpy.Exists(row_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Pipeline_ROW", "POLYGON",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(row_fc, ["SHAPE@"]) as cur:
            poly = create_rectangle(base_x, base_y + 400, 2100, 80, spatial_reference)  # ROW ~40m each side
            cur.insertRow([poly])
        print(f"Created: {row_fc}")

    # =============================== Flowlines ===============================
    flow_fc = os.path.join(gdb_path, "Flowlines")
    if not arcpy.Exists(flow_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Flowlines", "POLYLINE",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(flow_fc, ["SHAPE@"]) as cur:
            pts = [
                arcpy.Point(base_x - 800, base_y + 200),
                arcpy.Point(base_x + 800, base_y + 200)
            ]
            cur.insertRow([arcpy.Polyline(arcpy.Array(pts), spatial_reference)])
        print(f"Created: {flow_fc}")

    # =============================== Powerline_OHTL ==========================
    pl_fc = os.path.join(gdb_path, "Powerline_OHTL")
    if not arcpy.Exists(pl_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Powerline_OHTL", "POLYLINE",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(pl_fc, ["SHAPE@"]) as cur:
            pts = [
                arcpy.Point(base_x - 1000, base_y + 800),
                arcpy.Point(base_x + 1000, base_y + 800)
            ]
            cur.insertRow([arcpy.Polyline(arcpy.Array(pts), spatial_reference)])
        print(f"Created: {pl_fc}")

    # =============================== Powerline_ROW ===========================
    pl_row_fc = os.path.join(gdb_path, "Powerline_ROW")
    if not arcpy.Exists(pl_row_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Powerline_ROW", "POLYGON",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(pl_row_fc, ["SHAPE@"]) as cur:
            poly = create_rectangle(base_x, base_y + 800, 2100, 100, spatial_reference)
            cur.insertRow([poly])
        print(f"Created: {pl_row_fc}")

    # =============================== Fiber_Optic_Cable =======================
    fc = os.path.join(gdb_path, "Fiber_Optic_Cable")
    if not arcpy.Exists(fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Fiber_Optic_Cable", "POLYLINE",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(fc, ["SHAPE@"]) as cur:
            pts = [
                arcpy.Point(base_x - 800, base_y - 200),
                arcpy.Point(base_x + 800, base_y - 200)
            ]
            cur.insertRow([arcpy.Polyline(arcpy.Array(pts), spatial_reference)])
        print(f"Created: {fc}")

    # =============================== Communication_Cable =====================
    fc = os.path.join(gdb_path, "Communication_Cable")
    if not arcpy.Exists(fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Communication_Cable", "POLYLINE",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(fc, ["SHAPE@"]) as cur:
            pts = [
                arcpy.Point(base_x - 800, base_y - 250),
                arcpy.Point(base_x + 800, base_y - 250)
            ]
            cur.insertRow([arcpy.Polyline(arcpy.Array(pts), spatial_reference)])
        print(f"Created: {fc}")

    # =============================== Wells (نقطة) ============================
    wells_fc = os.path.join(gdb_path, "Wells")
    if not arcpy.Exists(wells_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Wells", "POINT",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(wells_fc, ["SHAPE@"]) as cur:
            cur.insertRow([arcpy.Point(base_x + 500, base_y + 100)])
        print(f"Created: {wells_fc}")

    # =============================== Hazard_Zones ============================
    hz_fc = os.path.join(gdb_path, "Hazard_Zones")
    if not arcpy.Exists(hz_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Hazard_Zones", "POLYGON",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(hz_fc, ["SHAPE@"]) as cur:
            poly = create_rectangle(base_x - 500, base_y - 300, 400, 400, spatial_reference)
            cur.insertRow([poly])
        print(f"Created: {hz_fc}")

    # =============================== Environmental_Buffers ===================
    env_fc = os.path.join(gdb_path, "Environmental_Buffers")
    if not arcpy.Exists(env_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Environmental_Buffers", "POLYGON",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(env_fc, ["SHAPE@"]) as cur:
            poly = create_rectangle(base_x + 600, base_y - 400, 600, 400, spatial_reference)
            cur.insertRow([poly])
        print(f"Created: {env_fc}")

    # =============================== GOSP_Facilities =========================
    gosp_fc = os.path.join(gdb_path, "GOSP_Facilities")
    if not arcpy.Exists(gosp_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "GOSP_Facilities", "POLYGON",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(gosp_fc, ["SHAPE@"]) as cur:
            poly = create_rectangle(base_x - 800, base_y + 300, 200, 200, spatial_reference)
            cur.insertRow([poly])
        print(f"Created: {gosp_fc}")

    # =============================== Gas_Plants ==============================
    gas_fc = os.path.join(gdb_path, "Gas_Plants")
    if not arcpy.Exists(gas_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Gas_Plants", "POLYGON",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(gas_fc, ["SHAPE@"]) as cur:
            poly = create_rectangle(base_x + 900, base_y + 300, 250, 250, spatial_reference)
            cur.insertRow([poly])
        print(f"Created: {gas_fc}")

    # =============================== Substations =============================
    sub_fc = os.path.join(gdb_path, "Substations")
    if not arcpy.Exists(sub_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Substations", "POLYGON",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(sub_fc, ["SHAPE@"]) as cur:
            poly = create_rectangle(base_x + 200, base_y + 600, 150, 150, spatial_reference)
            cur.insertRow([poly])
        print(f"Created: {sub_fc}")

    # =============================== Pump_Stations ===========================
    pump_fc = os.path.join(gdb_path, "Pump_Stations")
    if not arcpy.Exists(pump_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Pump_Stations", "POLYGON",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(pump_fc, ["SHAPE@"]) as cur:
            poly = create_rectangle(base_x - 200, base_y + 600, 150, 150, spatial_reference)
            cur.insertRow([poly])
        print(f"Created: {pump_fc}")

    # =============================== Schools =================================
    sch_fc = os.path.join(gdb_path, "Schools")
    if not arcpy.Exists(sch_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Schools", "POLYGON",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(sch_fc, ["SHAPE@"]) as cur:
            poly = create_rectangle(base_x + 600, base_y + 50, 150, 150, spatial_reference)
            cur.insertRow([poly])
        print(f"Created: {sch_fc}")

    # =============================== Hospitals ===============================
    hosp_fc = os.path.join(gdb_path, "Hospitals")
    if not arcpy.Exists(hosp_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Hospitals", "POLYGON",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(hosp_fc, ["SHAPE@"]) as cur:
            poly = create_rectangle(base_x + 600, base_y - 150, 150, 150, spatial_reference)
            cur.insertRow([poly])
        print(f"Created: {hosp_fc}")

    # =============================== Industrial_Facilities ===================
    ind_fc = os.path.join(gdb_path, "Industrial_Facilities")
    if not arcpy.Exists(ind_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Industrial_Facilities", "POLYGON",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(ind_fc, ["SHAPE@"]) as cur:
            poly = create_rectangle(base_x - 600, base_y + 50, 200, 200, spatial_reference)
            cur.insertRow([poly])
        print(f"Created: {ind_fc}")

    # =============================== ResidentialAreas ========================
    res_fc = os.path.join(gdb_path, "ResidentialAreas")
    if not arcpy.Exists(res_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "ResidentialAreas", "POLYGON",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(res_fc, ["SHAPE@"]) as cur:
            poly = create_rectangle(base_x - 600, base_y - 50, 250, 250, spatial_reference)
            cur.insertRow([poly])
        print(f"Created: {res_fc}")

    # =============================== Utilities (Generic) =====================
    util_fc = os.path.join(gdb_path, "Utilities")
    if not arcpy.Exists(util_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Utilities", "POLYLINE",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(util_fc, ["SHAPE@"]) as cur:
            pts = [
                arcpy.Point(base_x - 1000, base_y + 100),
                arcpy.Point(base_x + 1000, base_y + 100)
            ]
            cur.insertRow([arcpy.Polyline(arcpy.Array(pts), spatial_reference)])
        print(f"Created: {util_fc}")

    # =============================== ROW_Corridors ===========================
    rowc_fc = os.path.join(gdb_path, "ROW_Corridors")
    if not arcpy.Exists(rowc_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "ROW_Corridors", "POLYGON",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(rowc_fc, ["SHAPE@"]) as cur:
            poly = create_rectangle(base_x, base_y - 600, 2000, 150, spatial_reference)
            cur.insertRow([poly])
        print(f"Created: {rowc_fc}")

    # =============================== Voltage_Influence_Zone ==================
    volt_fc = os.path.join(gdb_path, "Voltage_Influence_Zone")
    if not arcpy.Exists(volt_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Voltage_Influence_Zone", "POLYGON",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(volt_fc, ["SHAPE@"]) as cur:
            poly = create_rectangle(base_x + 200, base_y + 800, 600, 300, spatial_reference)
            cur.insertRow([poly])
        print(f"Created: {volt_fc}")

    # =============================== Airport_Protection_Zones ================
    ap_fc = os.path.join(gdb_path, "Airport_Protection_Zones")
    if not arcpy.Exists(ap_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Airport_Protection_Zones", "POLYGON",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(ap_fc, ["SHAPE@"]) as cur:
            poly = create_rectangle(base_x + 1500, base_y + 1500, 800, 400, spatial_reference)
            cur.insertRow([poly])
        print(f"Created: {ap_fc}")

    # =============================== Existing_Buildings ======================
    bld_fc = os.path.join(gdb_path, "Existing_Buildings")
    if not arcpy.Exists(bld_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Existing_Buildings", "POLYGON",
            spatial_reference=spatial_reference
        )
        with arcpy.da.InsertCursor(bld_fc, ["SHAPE@"]) as cur:
            poly = create_rectangle(base_x + 100, base_y + 50, 80, 60, spatial_reference)
            cur.insertRow([poly])
        print(f"Created: {bld_fc}")

    return {
        "Company_Reservation": os.path.join(gdb_path, "Company_Reservation"),
        "Released_Areas": os.path.join(gdb_path, "Released_Areas"),
        "Disputed_Areas": os.path.join(gdb_path, "Disputed_Areas"),
        "Five_KM_Influence_Zone": os.path.join(gdb_path, "Five_KM_Influence_Zone"),
        "Roads": roads_fc,
        "Highways": hw_fc,
        "Pipelines": pipe_fc,
        "Pipeline_ROW": row_fc,
        "Flowlines": flow_fc,
        "Powerline_OHTL": pl_fc,
        "Powerline_ROW": pl_row_fc,
        "Fiber_Optic_Cable": os.path.join(gdb_path, "Fiber_Optic_Cable"),
        "Communication_Cable": os.path.join(gdb_path, "Communication_Cable"),
        "Wells": wells_fc,
        "Hazard_Zones": hz_fc,
        "Environmental_Buffers": env_fc,
        "GOSP_Facilities": gosp_fc,
        "Gas_Plants": gas_fc,
        "Substations": sub_fc,
        "Pump_Stations": pump_fc,
        "Schools": sch_fc,
        "Hospitals": hosp_fc,
        "Industrial_Facilities": ind_fc,
        "ResidentialAreas": res_fc,
        "Utilities": util_fc,
        "ROW_Corridors": rowc_fc,
        "Voltage_Influence_Zone": volt_fc,
        "Airport_Protection_Zones": ap_fc,
        "Existing_Buildings": bld_fc
    }


# ---------------------------------------------------------------------------
# إنشاء الطبقات المقترحة (Proposed_Sites + Temporary_Use_Areas)
# ---------------------------------------------------------------------------

def create_lup_proposed_features(gdb_path, project_id="LUP001", spatial_reference=SR_WEB_MERCATOR):
    """
    Creates:
      - Proposed_Sites (POLYGON) with USE_TYPE, OCCUPANCY, Scenario
      - Temporary_Use_Areas (POLYGON) مع OCCUPANCY
    مواقع مختارة بحيث:
      - بعضها PASS
      - بعضها FAIL Pipeline / Wells / Hazard / School / Hospital / Voltage / ROW
    """

    base_x = -12345000
    base_y = 3812000

    # =============================== Proposed_Sites ==========================
    prop_fc = os.path.join(gdb_path, "Proposed_Sites")
    if not arcpy.Exists(prop_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Proposed_Sites", "POLYGON",
            spatial_reference=spatial_reference
        )
        arcpy.AddField_management(prop_fc, "ProjectID", "TEXT", field_length=20)
        arcpy.AddField_management(prop_fc, "USE_TYPE", "TEXT", field_length=50)
        arcpy.AddField_management(prop_fc, "OCCUPANCY", "LONG")
        arcpy.AddField_management(prop_fc, "Scenario", "TEXT", field_length=80)

        with arcpy.da.InsertCursor(prop_fc, ["SHAPE@", "ProjectID", "USE_TYPE", "OCCUPANCY", "Scenario"]) as cur:
            # 1) PASS عام: داخل Company_Reservation، بعيد عن كل شيء
            s1 = create_rectangle(base_x - 200, base_y + 200, 100, 100, spatial_reference)
            cur.insertRow([s1, project_id, "Industrial", 20, "PASS_GENERAL"])

            # 2) FAIL Pipeline distance (<30m) & ROW overlap
            s2 = create_rectangle(base_x, base_y + 400, 60, 60, spatial_reference)
            cur.insertRow([s2, project_id, "Industrial", 30, "FAIL_PIPELINE_CLEARANCE"])

            # 3) FAIL Well distance (<60m)
            s3 = create_rectangle(base_x + 500, base_y + 120, 60, 60, spatial_reference)
            cur.insertRow([s3, project_id, "Residential", 50, "FAIL_WELL_BUFFER"])

            # 4) FAIL Hazard zone overlap
            s4 = create_rectangle(base_x - 500, base_y - 300, 100, 100, spatial_reference)
            cur.insertRow([s4, project_id, "Industrial", 40, "FAIL_HAZARD_ZONE"])

            # 5) FAIL Environmental buffer overlap
            s5 = create_rectangle(base_x + 600, base_y - 400, 80, 80, spatial_reference)
            cur.insertRow([s5, project_id, "Industrial", 35, "FAIL_ENV_BUFFER"])

            # 6) WARNING School buffer (Industrial قريب من مدرسة)
            s6 = create_rectangle(base_x + 500, base_y + 80, 80, 80, spatial_reference)
            cur.insertRow([s6, project_id, "Industrial", 60, "WARN_SCHOOL_BUFFER"])

            # 7) WARNING Hospital buffer (HighRisk قريب من مستشفى)
            s7 = create_rectangle(base_x + 500, base_y - 150, 80, 80, spatial_reference)
            cur.insertRow([s7, project_id, "HighRisk", 60, "WARN_HOSPITAL_BUFFER"])

            # 8) INFO داخل Five_KM_Influence_Zone لكن خارج Company_Reservation
            s8 = create_rectangle(base_x + 3500, base_y + 3500, 100, 100, spatial_reference)
            cur.insertRow([s8, project_id, "Industrial", 10, "INFO_5KM_ZONE"])

            # 9) FAIL Voltage influence zone لـ USE_TYPE = Residential
            s9 = create_rectangle(base_x + 200, base_y + 800, 80, 80, spatial_reference)
            cur.insertRow([s9, project_id, "Residential", 30, "FAIL_VOLTAGE_ZONE"])

            # 10) FAIL ROW_Corridors (داخل ممر ROW)
            s10 = create_rectangle(base_x, base_y - 600, 150, 100, spatial_reference)
            cur.insertRow([s10, project_id, "Industrial", 25, "FAIL_ROW_CORRIDOR"])

        print(f"Created: {prop_fc}")

    # =============================== Temporary_Use_Areas =====================
    temp_fc = os.path.join(gdb_path, "Temporary_Use_Areas")
    if not arcpy.Exists(temp_fc):
        arcpy.CreateFeatureclass_management(
            gdb_path, "Temporary_Use_Areas", "POLYGON",
            spatial_reference=spatial_reference
        )
        arcpy.AddField_management(temp_fc, "ProjectID", "TEXT", field_length=20)
        arcpy.AddField_management(temp_fc, "OCCUPANCY", "LONG")
        arcpy.AddField_management(temp_fc, "Scenario", "TEXT", field_length=80)

        with arcpy.da.InsertCursor(temp_fc, ["SHAPE@", "ProjectID", "OCCUPANCY", "Scenario"]) as cur:
            # Camp قريب من ResidentialAreas، Occupancy كبير → FAIL / WARNING
            c1 = create_rectangle(base_x - 600, base_y - 50, 120, 120, spatial_reference)
            cur.insertRow([c1, project_id, 80, "FAIL_TEMP_CAMP_NEAR_RESIDENTIAL"])

            # Camp بعيد (PASS)
            c2 = create_rectangle(base_x - 2000, base_y - 2000, 120, 120, spatial_reference)
            cur.insertRow([c2, project_id, 40, "PASS_TEMP_CAMP_FAR"])

        print(f"Created: {temp_fc}")

    return {
        "Proposed_Sites": os.path.join(gdb_path, "Proposed_Sites"),
        "Temporary_Use_Areas": os.path.join(gdb_path, "Temporary_Use_Areas")
    }


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def create_all_lup_test_data(output_folder=None, project_id="LUP001"):
    if output_folder is None:
        output_folder = tempfile.gettempdir()

    print(f"Creating LUP test data in folder: {output_folder}")

    gdb_path = create_lup_geodatabase(output_folder)
    infra = create_lup_infrastructure_features(gdb_path)
    proposed = create_lup_proposed_features(gdb_path, project_id)

    print("\n" + "=" * 60)
    print("LUP TEST DATA CREATION COMPLETE")
    print("=" * 60)
    print(f"\nGeodatabase: {gdb_path}")
    print("\nInfrastructure Feature Classes:")
    for name, path in infra.items():
        print(f"  - {name}: {path}")
    print("\nProposed Feature Classes:")
    for name, path in proposed.items():
        print(f"  - {name}: {path}")
    print("\nYou can now:")
    print("  1) Add this GDB to ArcGIS Pro")
    print("  2) Use 'Validate Project' with:")
    print(f"       Project ID = {project_id}")
    print("       Feature Classes to Validate = Proposed_Sites, Temporary_Use_Areas (and others if needed)")
    print("  3) Use rules_config.json you already built.")
    print("=" * 60)

    return {
        "geodatabase": gdb_path,
        "infrastructure": infra,
        "proposed": proposed
    }
if __name__ == "__main__":
    create_all_lup_test_data()
