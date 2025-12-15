# ArcGIS Spatial Validation Toolbox

## Overview
The **ArcGIS Spatial Validation Toolbox** is a Python-based ArcGIS Pro toolbox designed to validate **Land Use Permit (LUP)** and development projects against configurable spatial rules.  
The system automates spatial compliance checks such as setbacks, crossings, containment, and infrastructure conflicts using a rule-driven architecture without modifying enterprise geodatabases.

The toolbox is designed for **ArcGIS Enterprise environments** and supports large multi-user GIS teams working with shared geodatabases.

---

## Key Objectives
- Automate spatial compliance validation for development projects
- Reduce manual GIS review effort and human error
- Centralize validation logic using JSON-based configuration
- Support scalable enterprise GIS workflows
- Enable future AI-assisted spatial validation and decision support

---

## Project Constraints
- No changes to Enterprise Geodatabase schema
- No creation of new databases
- Must work with existing ArcGIS Pro installations
- Rules must be configurable without code changes
- Must support multi-user (24+ users) environments

---

## 🏗️ System Architecture

The toolbox follows a modular architecture:

- **Python Toolbox (.pyt)** provides the ArcGIS Pro user interface
- **Validation Engine** executes spatial rules
- **JSON Configuration** defines validation logic
- **Utility Module** handles reporting, summaries, and helper functions

This separation allows rules to be updated without modifying code and supports long-term maintainability.

---

## 📁 Project Structure

│
├── Toolbox/
│ ├── SpatialValidation.pyt # Main ArcGIS Python Toolbox
│ ├── validation_engine.py # Core spatial validation engine
│ ├── utils.py # Utility and helper functions
│ └── test_data_generator.py # Test data generator
│
├── Config/
│ └── rules_config.json # JSON-based rule definitions
│
├── Templates/
│ └── Validation_Report_Template.xlsx
│
└── README.md


---

## 🚀 Quick Start

### 1. Add Toolbox to ArcGIS Pro
1. Open **ArcGIS Pro**
2. In the **Catalog** pane, right-click **Toolboxes**
3. Select **Add Toolbox**
4. Browse to `Toolbox/SpatialValidation.pyt`

### 2. Run Validation
1. Expand the toolbox → **Validate Project**
2. Enter a **Project ID**
3. Select feature classes to validate
4. Choose the rule configuration file
5. Specify output location
6. Click **Run**

### 3. View Results
- Add the output feature class to your map
- Violations appear as points at violation locations  
- **Red** = Errors (blocking)  
- **Orange** = Warnings (advisory)

---

## 🛠️ Available Tools

| Tool | Description |
|-----|-------------|
| **Validate Project** | Run all active rules against project features |
| **Validate Feature Class** | Validate a single feature class against a specific rule |
| **Configure Rules** | Add, edit, enable, or disable rules |
| **Generate Report** | Export validation results to Excel or CSV |
| **Clear Validation** | Remove validation results for a project |
| **Batch Validate** | Validate multiple projects in a single run |

---

## 📋 Supported Rule Types

| Rule Type | Description | Example Use |
|---------|-------------|-------------|
| `MINIMUM_DISTANCE` | Minimum separation between features | Building setbacks |
| `MAXIMUM_DISTANCE` | Maximum distance to nearest feature | Utility access |
| `INTERSECTION_ANGLE` | Angle at line intersections | Road design |
| `CROSSING_ANGLE` | Angle when utilities cross roads | Utility crossings |
| `CONTAINMENT` | Feature must be inside a polygon | Parcel boundaries |
| `ATTRIBUTE_DISTANCE` | Distance based on attributes | Pipeline diameter |
| `BUFFER_OVERLAP` | Buffered feature overlap | Clearance zones |

---

## 🚦 Severity Levels

Validation results are classified using standardized severity levels:

- **ERROR** – Blocking violation (must be resolved before approval)
- **WARNING** – Advisory issue (requires review and justification)
- **INFO** – Informational notice (no action required)

---

## 📍 Violation Point Feature Class

Validation results are stored as a **point feature class** to support spatial visualization and interactive review in ArcGIS Pro.  
Each point represents the geographic location where a rule violation was detected.

### Attribute Schema

| Field Name | Description |
|-----------|-------------|
| `ProjectID` | Unique project identifier |
| `RuleCode` | Code of the violated rule |
| `RuleName` | Human-readable rule name |
| `Severity` | Violation severity (ERROR, WARNING, INFO) |
| `SourceFC` | Source feature class being validated |
| `SourceOID` | Object ID of the violating feature |
| `TargetFC` | Target feature class used for comparison |
| `TargetOID` | Object ID of the target feature |
| `MeasuredValue` | Calculated spatial measurement |
| `ThresholdValue` | Required threshold value |
| `Message` | Detailed validation message |
| `ValidationDate` | Date and time of validation |
| `ValidatedBy` | Username of the validator |

---

## 📊 Reporting

Validation results can be exported using the **Generate Report** tool.

Supported formats:
- **Excel (.xlsx)** – Formatted tables with summary statistics
- **CSV (.csv)** – Lightweight format for external analysis

---

## 🧪 Testing

### Test Data Generator

The script `test_data_generator.py` creates a sample geodatabase with predefined **pass/fail validation scenarios**.

**Use cases:**
- Tool validation
- Rule verification
- AI model training and evaluation

---

## 📝 Requirements

- ArcGIS Pro 2.9 or later
- Standard license or higher
- Optional: `openpyxl` for Excel report generation

---

## 🤝 Team Deployment

### Shared Network Setup
1. Store the toolbox in a shared network location
2. Each team member adds the toolbox to ArcGIS Pro
3. Shared rule configuration ensures consistent validation
4. Validation results are stored in the enterprise geodatabase

---

## 📄 License

Internal use only.  
Distribution requires GIS management approval.

---

## 🆘 Support

- **Documentation**: Refer to the `Docs/` folder
- **Issues**: Contact the GIS support team
- **Training**: Request training sessions through GIS leadership

---

**Version**: 1.0.0  
**Author**: Spatial Validation Team  
**Last Updated**: 2025
