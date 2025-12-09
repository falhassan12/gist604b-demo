# ArcGIS Spatial Validation Toolbox

## Project Context
This is an ArcGIS Python Toolbox (.pyt) for validating development projects against configurable spatial rules. Designed for a 24-member team using ArcGIS Enterprise with a shared geodatabase.

## Key Constraints
- Cannot modify enterprise database structure
- Cannot deploy new databases
- Must work with existing ArcGIS Pro installations
- Rules must be configurable without code changes

## Architecture
- **Toolbox**: `Toolbox/SpatialValidation.pyt` - Main Python Toolbox
- **Engine**: `Toolbox/validation_engine.py` - Core validation logic (SpatialValidator class)
- **Config**: `Config/rules_config.json` - JSON-based rule definitions
- **Utils**: `Toolbox/utils.py` - Helper functions

## Rule Types
- MINIMUM_DISTANCE - Setbacks, separations
- MAXIMUM_DISTANCE - Access requirements
- INTERSECTION_ANGLE - Road intersection design
- CROSSING_ANGLE - Utility crossings
- CONTAINMENT - Features within boundaries
- ATTRIBUTE_DISTANCE - Dynamic thresholds based on attributes

## Testing
Use `Toolbox/test_data_generator.py` to create sample geodatabase with known pass/fail scenarios.
