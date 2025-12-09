# ArcGIS Spatial Validation Toolbox

A Python Toolbox for validating development projects against configurable spatial rules in ArcGIS Pro.

## 🎯 Overview

This toolbox enables teams to validate proposed infrastructure (roads, buildings, utilities) against existing features using configurable spatial rules. Perfect for:

- **Urban Planning**: Ensure setbacks, containment, and separation requirements
- **Infrastructure Projects**: Validate utility crossings, road intersections, and pipeline separations
- **Development Review**: Automated compliance checking against spatial regulations

## 📁 Project Structure

```
├── Toolbox/
│   ├── SpatialValidation.pyt      # Main Python Toolbox
│   ├── validation_engine.py       # Core validation logic
│   └── utils.py                   # Helper functions
├── Config/
│   └── rules_config.json          # Rule definitions
├── Docs/                          # Documentation
├── LayerFiles/                    # Symbology templates
└── Templates/                     # Report templates
```

## 🚀 Quick Start

### 1. Add Toolbox to ArcGIS Pro

1. Open ArcGIS Pro
2. In the Catalog pane, right-click **Toolboxes**
3. Select **Add Toolbox**
4. Browse to `Toolbox/SpatialValidation.pyt`

### 2. Run Validation

1. Expand the toolbox → **Validate Project**
2. Enter a Project ID
3. Select feature classes to validate
4. Choose the rule configuration file
5. Specify output location
6. Click **Run**

### 3. View Results

- Add the output feature class to your map
- Violations appear as points at violation locations
- **Red** = Errors (blocking)
- **Orange** = Warnings (advisory)

## 🛠️ Available Tools

| Tool | Description |
|------|-------------|
| **Validate Project** | Run all active rules against project features |
| **Validate Feature Class** | Quick validation of single FC against specific rule |
| **Configure Rules** | Add, edit, enable/disable rules via GUI |
| **Generate Report** | Export results to Excel/CSV |
| **Clear Validation** | Remove validation results for a project |
| **Batch Validate** | Validate multiple projects at once |

## 📋 Rule Types

| Type | Description | Example Use |
|------|-------------|-------------|
| `MINIMUM_DISTANCE` | Minimum separation between features | Building setbacks |
| `MAXIMUM_DISTANCE` | Maximum distance to nearest feature | Utility access requirements |
| `INTERSECTION_ANGLE` | Angle at line intersections | Road intersection design |
| `CROSSING_ANGLE` | Angle when lines cross | Utility-road crossings |
| `CONTAINMENT` | Features within polygons | Development within parcels |
| `ATTRIBUTE_DISTANCE` | Distance based on attribute values | Pipeline separation by diameter |
| `BUFFER_OVERLAP` | Buffered feature overlap check | Clearance zones |

## ⚙️ Configuration

### Rule Configuration (`Config/rules_config.json`)

```json
{
  "rules": [
    {
      "rule_code": "BUILDING_SETBACK",
      "rule_name": "Building Setback from Roads",
      "description": "Buildings must be at least 15 meters from roads",
      "severity": "ERROR",
      "active": true,
      "source_fc": "ProposedBuildings",
      "target_fc": "Roads",
      "rule_type": "MINIMUM_DISTANCE",
      "parameters": {
        "min_distance_meters": 15
      }
    }
  ]
}
```

### Severity Levels

- **ERROR**: Blocking violation - must be resolved
- **WARNING**: Advisory violation - should be reviewed
- **INFO**: Informational - for documentation

## 📊 Output

### Violation Points Feature Class

Each violation is represented as a point with attributes:

| Field | Description |
|-------|-------------|
| `ProjectID` | Project identifier |
| `RuleCode` | Rule that was violated |
| `RuleName` | Human-readable rule name |
| `Severity` | ERROR, WARNING, or INFO |
| `SourceFC` | Feature class being validated |
| `SourceOID` | Object ID of violating feature |
| `TargetFC` | Feature class compared against |
| `TargetOID` | Object ID of target feature |
| `MeasuredValue` | Actual measured value |
| `ThresholdValue` | Required threshold |
| `Message` | Detailed violation message |
| `ValidationDate` | When validation was run |
| `ValidatedBy` | Username of validator |

## 🔧 Customization

### Adding New Rules

1. Open **Configure Rules** tool
2. Select "Add Rule"
3. Fill in rule parameters
4. Save configuration

### Editing Rules Directly

Edit `Config/rules_config.json`:

```json
{
  "rule_code": "MY_CUSTOM_RULE",
  "rule_name": "My Custom Rule",
  "severity": "ERROR",
  "active": true,
  "source_fc": "MySourceFC",
  "target_fc": "MyTargetFC",
  "rule_type": "MINIMUM_DISTANCE",
  "parameters": {
    "min_distance_meters": 10
  }
}
```

## 🧪 Testing

### With Sample Data

1. Create a file geodatabase for testing
2. Add sample proposed features
3. Add infrastructure features (roads, parcels, etc.)
4. Run validation

### With OpenStreetMap Data

See `Docs/` folder for instructions on loading OSM data for testing.

## 📝 Requirements

- ArcGIS Pro 2.9+ (for Python 3.x support)
- Standard license or higher
- Optional: `openpyxl` for Excel reports

## 🤝 Team Usage

### Shared Network Setup

1. Place toolbox on shared network location
2. Each team member adds toolbox to their ArcGIS Pro
3. Shared rule configuration ensures consistency
4. Validation results stored in enterprise geodatabase

### Recommended Folder Structure

```
\\server\GIS\SpatialValidation\
├── Toolbox/
├── Config/
├── Docs/
├── LayerFiles/
└── Templates/
```

## 📄 License

Internal use only. Contact GIS team for distribution.

## 🆘 Support

- **Documentation**: See `Docs/` folder
- **Issues**: Contact GIS support team
- **Training**: Request training session from GIS team

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Author**: Spatial Validation Team

