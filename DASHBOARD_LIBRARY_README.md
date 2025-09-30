# Grafana Dashboard Library

A comprehensive Python library for parsing, updating, and constructing Grafana dashboard JSON configurations. This library provides a high-level, object-oriented interface for working with Grafana dashboards programmatically.

## Features

- 🔍 **Parse existing dashboard JSON** with robust error handling and automatic fixes
- 🏗️ **Create new dashboards** using a fluent builder pattern
- ✏️ **Modify dashboard components** (panels, variables, time ranges, etc.)
- ✅ **Validate dashboard structure** and fix common issues
- 🔄 **Convert between JSON and Python objects** seamlessly
- 🧪 **Comprehensive error handling** for malformed JSON and invalid structures
- 📊 **Support for all major panel types** (timeseries, table, stat, gauge, etc.)
- 🔗 **Template variable management** with multiple variable types
- 📁 **File operations** for loading/saving dashboards
- 🔀 **Dashboard merging** capabilities

## Installation

The library requires Python 3.6+ and uses only standard library modules plus `dataclasses` for older Python versions.

```bash
# Install from requirements.txt
pip install -r requirements.txt

# Or install individual dependencies
pip install dataclasses  # Only needed for Python < 3.7
```

## Quick Start

### 1. Parse an Existing Dashboard

```python
from grafana_dashboard_lib import GrafanaDashboardManager

# Load from JSON file
manager = GrafanaDashboardManager()
dashboard, messages = manager.load_dashboard("dashboard.json")

if dashboard:
    print(f"Loaded: {dashboard.title}")
    print(f"Panels: {len(dashboard.panels)}")
    print(f"Variables: {len(dashboard.templating)}")
else:
    print(f"Failed to load: {'; '.join(messages)}")
```

### 2. Create a New Dashboard

```python
from grafana_dashboard_lib import (
    GrafanaDashboardBuilder, 
    DataSource, 
    QueryTarget, 
    GridPosition
)

# Create datasource
postgres_ds = DataSource(type="grafana-postgresql-datasource", uid="${POSTGRES}")

# Create query
cpu_query = QueryTarget(
    datasource=postgres_ds,
    ref_id="A",
    raw_sql="SELECT time, AVG(cpu_usage) FROM metrics WHERE $__timeFilter(time) GROUP BY time"
)

# Build dashboard
dashboard = (GrafanaDashboardBuilder("System Monitoring")
            .with_description("Real-time system metrics")
            .with_tags(["monitoring", "system"])
            .with_time_range("now-1h", "now")
            .with_refresh_interval("30s")
            .add_timeseries_panel(
                "CPU Usage", 
                [cpu_query],
                GridPosition(h=8, w=12, x=0, y=0)
            )
            .add_query_variable(
                "server",
                "SELECT DISTINCT server FROM metrics",
                postgres_ds,
                multi=True
            )
            .build())

# Save to file
success, errors = manager.save_dashboard(dashboard, "new_dashboard.json")
```

### 3. Modify an Existing Dashboard

```python
# Load existing dashboard
dashboard, _ = manager.load_dashboard("existing_dashboard.json")

# Add a new panel
from grafana_dashboard_lib import Panel, PanelType

new_panel = Panel(
    id=999,  # Will be auto-assigned if needed
    title="Memory Usage",
    type=PanelType.STAT.value,
    grid_pos=GridPosition(h=6, w=6, x=12, y=0)
)
dashboard.add_panel(new_panel)

# Modify existing panel
panel = dashboard.get_panel_by_id(1)
if panel:
    panel.title = "Updated Panel Title"
    panel.description = "New description"

# Add template variable
from grafana_dashboard_lib import TemplateVariable, VariableType

new_var = TemplateVariable(
    name="environment",
    type=VariableType.CUSTOM.value,
    options=[
        {"text": "Production", "value": "prod"},
        {"text": "Staging", "value": "stage"}
    ]
)
dashboard.add_variable(new_var)

# Update time range
dashboard.time.from_time = "now-2h"
dashboard.refresh = "1m"

# Save changes
manager.save_dashboard(dashboard, "modified_dashboard.json")
```

## Core Classes

### GrafanaDashboard

The main dashboard class representing a complete Grafana dashboard.

```python
dashboard = GrafanaDashboard(
    title="My Dashboard",
    uid="my-dashboard-uid",
    description="Dashboard description",
    tags=["tag1", "tag2"]
)

# Core operations
dashboard.add_panel(panel)
dashboard.remove_panel(panel_id)
dashboard.get_panel_by_id(panel_id)
dashboard.get_panels_by_type("timeseries")

dashboard.add_variable(variable)
dashboard.remove_variable(variable_name)
dashboard.get_variable_by_name(variable_name)

# Validation
is_valid, errors = dashboard.validate()

# Serialization
json_str = dashboard.to_json()
dashboard = GrafanaDashboard.from_json(json_str)
```

### Panel

Represents individual dashboard panels.

```python
from grafana_dashboard_lib import Panel, PanelType, GridPosition

panel = Panel(
    id=1,
    title="CPU Usage",
    type=PanelType.TIMESERIES.value,
    grid_pos=GridPosition(h=8, w=12, x=0, y=0),
    targets=[query_target],
    description="CPU usage over time"
)
```

### QueryTarget

Represents data queries for panels.

```python
from grafana_dashboard_lib import QueryTarget, DataSource

# For Prometheus queries
prom_target = QueryTarget(
    datasource=DataSource("prometheus", "prometheus-uid"),
    ref_id="A",
    expr="cpu_usage_percent",
    legend_format="CPU Usage"
)

# For SQL queries
sql_target = QueryTarget(
    datasource=DataSource("grafana-postgresql-datasource", "postgres-uid"),
    ref_id="A",
    raw_sql="SELECT time, value FROM metrics WHERE $__timeFilter(time)",
    format="time_series"
)
```

### TemplateVariable

Dashboard template variables for dynamic content.

```python
from grafana_dashboard_lib import TemplateVariable, VariableType

# Query variable
query_var = TemplateVariable(
    name="server",
    type=VariableType.QUERY.value,
    query="SELECT DISTINCT server FROM metrics",
    datasource=datasource,
    multi=True,
    include_all=True
)

# Custom variable
custom_var = TemplateVariable(
    name="environment",
    type=VariableType.CUSTOM.value,
    options=[
        {"text": "Production", "value": "prod"},
        {"text": "Development", "value": "dev"}
    ],
    current={"text": "Production", "value": "prod"}
)
```

### GrafanaDashboardBuilder

Fluent builder for creating dashboards.

```python
dashboard = (GrafanaDashboardBuilder("Dashboard Title")
            .with_description("Description")
            .with_tags(["tag1", "tag2"])
            .with_time_range("now-6h", "now")
            .with_refresh_interval("1m")
            .with_uid("custom-uid")
            .add_timeseries_panel("Panel 1", [target1])
            .add_table_panel("Panel 2", [target2])
            .add_stat_panel("Panel 3", [target3])
            .add_query_variable("var1", "query", datasource)
            .add_custom_variable("var2", ["opt1", "opt2"])
            .build())
```

## Panel Types

The library supports all major Grafana panel types:

```python
from grafana_dashboard_lib import PanelType

# Available panel types:
PanelType.TIMESERIES     # Time series charts
PanelType.TABLE          # Data tables
PanelType.STAT           # Single stat panels
PanelType.GAUGE          # Gauge visualizations
PanelType.BAR_GAUGE      # Bar gauge panels
PanelType.HEATMAP        # Heatmap visualizations
PanelType.PIE_CHART      # Pie charts
PanelType.TEXT           # Text panels
PanelType.LOGS           # Log panels
PanelType.ALERT_LIST     # Alert lists
PanelType.GRAPH          # Legacy graph panels
```

## Variable Types

Support for all Grafana template variable types:

```python
from grafana_dashboard_lib import VariableType

VariableType.QUERY       # Query-based variables
VariableType.CUSTOM      # Custom option lists
VariableType.CONSTANT    # Constant values
VariableType.DATASOURCE  # Datasource selection
VariableType.INTERVAL    # Time interval variables
VariableType.TEXTBOX     # Text input variables
VariableType.ADHOC       # Ad-hoc filters
```

## Error Handling and Validation

The library includes comprehensive error handling:

### Robust JSON Parsing

```python
from grafana_dashboard_lib import GrafanaDashboardParser

# Handles various JSON format issues automatically
problematic_json = '''
// Comments in JSON
{
    "title": "Dashboard",
    "panels": [
        {
            "id": 1,
            "title": "Panel",
            // Another comment
            "type": "timeseries",
        }  // Trailing comma
    ],
}
'''

parsed_data, warnings = GrafanaDashboardParser.parse_json_string(problematic_json)
# warnings will contain: ["Removed comments", "Removed trailing commas"]
```

### Dashboard Validation

```python
dashboard, _ = manager.load_dashboard("dashboard.json")

# Comprehensive validation
is_valid, errors, warnings = manager.validate_dashboard(dashboard)

print(f"Valid: {is_valid}")
print(f"Errors: {errors}")      # Critical issues that must be fixed
print(f"Warnings: {warnings}")  # Non-critical issues
```

### Common Issues Fixed Automatically

- Trailing commas in JSON
- Comments in JSON (`//` style)
- Unquoted object keys
- Single quotes instead of double quotes
- Missing required dashboard fields
- Duplicate panel IDs
- Invalid grid positions

## Advanced Features

### Dashboard Merging

```python
# Merge two dashboards
merged, warnings = manager.merge_dashboards(
    dashboard1, 
    dashboard2, 
    merge_strategy="append"  # "append", "replace", or "merge"
)
```

### Auto-Layout

```python
# Automatically layout panels to prevent overlaps
dashboard.auto_layout(columns=3)
```

### Dashboard Cloning

```python
# Create a deep copy of a dashboard
cloned_dashboard = dashboard.clone()
cloned_dashboard.title = "Cloned Dashboard"
```

### Panel Filtering

```python
# Get panels by type
timeseries_panels = dashboard.get_panels_by_type("timeseries")
table_panels = dashboard.get_panels_by_type("table")

# Get specific panel
panel = dashboard.get_panel_by_id(5)
```

## File Operations

### Loading Dashboards

```python
manager = GrafanaDashboardManager()

# From JSON string
dashboard, messages = manager.load_dashboard(json_string)

# From file path
dashboard, messages = manager.load_dashboard("dashboard.json")

# From dictionary
dashboard, messages = manager.load_dashboard(dashboard_dict)
```

### Saving Dashboards

```python
# Save to file with pretty formatting
success, errors = manager.save_dashboard(dashboard, "output.json", indent=2)

# Save compact JSON
success, errors = manager.save_dashboard(dashboard, "output.json", indent=None)
```

## Integration with Existing Code

The library is designed to work alongside the existing `GrafanaDashboardManager` in your project:

```python
# Use with existing manager
from grafana_dashboard_manager import GrafanaDashboardManager as ExistingManager
from grafana_dashboard_lib import GrafanaDashboardManager as NewManager

# Get dashboard from database using existing manager
existing_mgr = ExistingManager()
db_dashboard = existing_mgr.get_dashboard_by_id(123)

# Parse with new library
new_mgr = NewManager()
dashboard_obj, messages = new_mgr.load_dashboard(db_dashboard['data'])

# Modify using library
dashboard_obj.add_panel(new_panel)

# Convert back to JSON for database storage
modified_json = dashboard_obj.to_dict()
existing_mgr.insert_dashboard("Modified Dashboard", "modified-slug", modified_json)
```

## Examples and Testing

Run the included examples:

```bash
# Run all examples
python dashboard_examples.py

# Run comprehensive tests
python test_dashboard_lib.py

# Interactive demo
python -c "from dashboard_examples import interactive_demo; interactive_demo()"
```

## Best Practices

### 1. Always Validate Dashboards

```python
dashboard, _ = manager.load_dashboard("dashboard.json")
is_valid, errors, warnings = manager.validate_dashboard(dashboard)

if not is_valid:
    print(f"Dashboard has errors: {errors}")
    # Fix errors before proceeding
```

### 2. Use Unique Panel IDs

```python
# Let the library auto-assign IDs
panel = Panel(id=0, title="My Panel")  # ID will be auto-assigned
dashboard.add_panel(panel)

# Or ensure uniqueness manually
existing_ids = {p.id for p in dashboard.panels}
new_id = max(existing_ids, default=0) + 1
panel = Panel(id=new_id, title="My Panel")
```

### 3. Handle Grid Positioning

```python
# Use auto-layout for automatic positioning
dashboard.auto_layout(columns=2)

# Or set positions manually
panel.grid_pos = GridPosition(x=0, y=0, w=12, h=8)
```

### 4. Backup Before Modifications

```python
# Always backup before major changes
original_json = dashboard.to_json()
# ... make modifications ...
# If something goes wrong, restore from original_json
```

## Error Reference

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "Duplicate panel IDs found" | Multiple panels with same ID | Use `dashboard.auto_layout()` or manually assign unique IDs |
| "Panels overlap" | Grid positions conflict | Use `dashboard.auto_layout()` or adjust `grid_pos` manually |
| "Empty JSON string provided" | Invalid input | Check input source and format |
| "Dashboard title cannot be empty" | Missing title | Set `dashboard.title = "Your Title"` |
| "JSON parsing failed" | Malformed JSON | Use robust parser which auto-fixes common issues |

## Performance Considerations

- **Large Dashboards**: For dashboards with 50+ panels, consider processing in batches
- **Memory Usage**: The library creates in-memory objects; monitor usage for very large dashboards
- **JSON Parsing**: Robust parsing is slower than standard JSON parsing but handles real-world data better
- **Validation**: Comprehensive validation adds processing time but prevents runtime errors

## Compatibility

- **Python**: 3.6+ (uses dataclasses, backport available for older versions)
- **Grafana**: Compatible with Grafana dashboard schema versions 30+
- **JSON**: Handles both strict and lenient JSON formats
- **Encoding**: Full Unicode support for international characters

## Contributing

The library is designed to be extensible. Key extension points:

- **Panel Types**: Add new panel types by extending the `PanelType` enum
- **Variable Types**: Add new variable types by extending the `VariableType` enum  
- **Validation Rules**: Add custom validation in the `validate()` methods
- **Parsers**: Extend `GrafanaDashboardParser` for special JSON formats

## License

This library is part of the Groq Cloud Spyder project and follows the same licensing terms.

---

For more examples and advanced usage, see:
- `dashboard_examples.py` - Comprehensive examples
- `test_dashboard_lib.py` - Test cases demonstrating all features
- `grafana_dashboard_lib.py` - Full library source with detailed docstrings
