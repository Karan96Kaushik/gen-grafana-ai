"""
Grafana Dashboard Library - Parse, Update, and Construct Grafana Dashboards

This library provides a comprehensive toolkit for working with Grafana dashboard JSON configurations.
It allows you to:
- Parse existing dashboard JSON into structured Python objects
- Modify dashboard components programmatically
- Serialize dashboard objects back to JSON
- Validate dashboard structure and fix common issues
- Create new dashboards from scratch

Author: AI Assistant
License: MIT
"""

import json
import copy
import re
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum


class PanelType(Enum):
    """Supported Grafana panel types"""
    GRAPH = "graph"
    TIMESERIES = "timeseries"
    TABLE = "table"
    STAT = "stat"
    GAUGE = "gauge"
    BAR_GAUGE = "bargauge"
    HEATMAP = "heatmap"
    PIE_CHART = "piechart"
    TEXT = "text"
    LOGS = "logs"
    ALERT_LIST = "alertlist"
    DASHBOARD_LIST = "dashlist"
    NEWS = "news"
    PLUGIN_LIST = "pluginlist"
    ROW = "row"


class FieldType(Enum):
    """Field configuration types"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    TIME = "time"


class VariableType(Enum):
    """Template variable types"""
    QUERY = "query"
    CUSTOM = "custom"
    CONSTANT = "constant"
    DATASOURCE = "datasource"
    INTERVAL = "interval"
    TEXTBOX = "textbox"
    ADHOC = "adhoc"


@dataclass
class GridPosition:
    """Represents panel grid position and size"""
    h: int = 8  # height
    w: int = 12  # width
    x: int = 0  # x position
    y: int = 0  # y position

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary format"""
        return {"h": self.h, "w": self.w, "x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'GridPosition':
        """Create from dictionary"""
        return cls(
            h=data.get("h", 8),
            w=data.get("w", 12),
            x=data.get("x", 0),
            y=data.get("y", 0)
        )


@dataclass
class DataSource:
    """Represents a Grafana datasource reference"""
    type: str
    uid: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format"""
        return {"type": self.type, "uid": self.uid}

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'DataSource':
        """Create from dictionary"""
        return cls(
            type=data.get("type", ""),
            uid=data.get("uid", "")
        )


@dataclass
class QueryTarget:
    """Represents a query target for panels"""
    datasource: Optional[DataSource] = None
    ref_id: str = "A"
    expr: Optional[str] = None
    raw_sql: Optional[str] = None
    format: str = "time_series"
    editor_mode: str = "code"
    raw_query: bool = True
    hide: bool = False
    interval: Optional[str] = None
    legend_format: Optional[str] = None
    step: Optional[int] = None
    instant: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        result = {
            "refId": self.ref_id,
            "format": self.format,
            "hide": self.hide
        }
        
        if self.datasource:
            result["datasource"] = self.datasource.to_dict()
        
        if self.expr:
            result["expr"] = self.expr
        
        if self.raw_sql:
            result["rawSql"] = self.raw_sql
            result["editorMode"] = self.editor_mode
            result["rawQuery"] = self.raw_query
        
        if self.interval:
            result["interval"] = self.interval
        
        if self.legend_format:
            result["legendFormat"] = self.legend_format
        
        if self.step:
            result["step"] = self.step
        
        if self.instant:
            result["instant"] = self.instant
        
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueryTarget':
        """Create from dictionary"""
        datasource = None
        if "datasource" in data:
            datasource_data = data["datasource"]
            if isinstance(datasource_data, str):
                # Handle string datasource (legacy format)
                datasource = DataSource(type="", uid=datasource_data)
            elif isinstance(datasource_data, dict):
                # Handle dictionary datasource (standard format)
                datasource = DataSource.from_dict(datasource_data)
            else:
                # Invalid datasource format
                datasource = None
        
        return cls(
            datasource=datasource,
            ref_id=data.get("refId", "A"),
            expr=data.get("expr"),
            raw_sql=data.get("rawSql"),
            format=data.get("format", "time_series"),
            editor_mode=data.get("editorMode", "code"),
            raw_query=data.get("rawQuery", True),
            hide=data.get("hide", False),
            interval=data.get("interval"),
            legend_format=data.get("legendFormat"),
            step=data.get("step"),
            instant=data.get("instant", False)
        )


@dataclass
class FieldConfig:
    """Field configuration for panels"""
    defaults: Dict[str, Any] = field(default_factory=dict)
    overrides: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "defaults": self.defaults,
            "overrides": self.overrides
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FieldConfig':
        """Create from dictionary"""
        return cls(
            defaults=data.get("defaults", {}),
            overrides=data.get("overrides", [])
        )


@dataclass
class Panel:
    """Represents a Grafana dashboard panel"""
    id: int
    title: str
    type: str = PanelType.TIMESERIES.value
    grid_pos: GridPosition = field(default_factory=GridPosition)
    targets: List[QueryTarget] = field(default_factory=list)
    field_config: FieldConfig = field(default_factory=FieldConfig)
    options: Dict[str, Any] = field(default_factory=dict)
    datasource: Optional[DataSource] = None
    description: Optional[str] = None
    transparent: bool = False
    collapsed: bool = False
    panels: Optional[List['Panel']] = None  # For row panels
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        result = {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "gridPos": self.grid_pos.to_dict(),
            "targets": [target.to_dict() for target in self.targets],
            "fieldConfig": self.field_config.to_dict(),
            "options": self.options,
            "transparent": self.transparent
        }
        
        if self.datasource:
            result["datasource"] = self.datasource.to_dict()
        
        if self.description:
            result["description"] = self.description
        
        if self.type == PanelType.ROW.value:
            result["collapsed"] = self.collapsed
            if self.panels:
                result["panels"] = [panel.to_dict() for panel in self.panels]
        
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Panel':
        """Create from dictionary"""
        grid_pos = GridPosition.from_dict(data.get("gridPos", {}))
        
        targets = []
        for target_data in data.get("targets", []):
            targets.append(QueryTarget.from_dict(target_data))
        
        field_config = FieldConfig.from_dict(data.get("fieldConfig", {}))
        
        datasource = None
        if "datasource" in data:
            datasource_data = data["datasource"]
            if isinstance(datasource_data, str):
                # Handle string datasource (legacy format)
                datasource = DataSource(type="", uid=datasource_data)
            elif isinstance(datasource_data, dict):
                # Handle dictionary datasource (standard format)
                datasource = DataSource.from_dict(datasource_data)
            else:
                # Invalid datasource format
                datasource = None
        
        panels = None
        if "panels" in data and data["panels"]:
            panels = [Panel.from_dict(panel_data) for panel_data in data["panels"]]
        
        return cls(
            id=data.get("id", 1),
            title=data.get("title", "Panel"),
            type=data.get("type", PanelType.TIMESERIES.value),
            grid_pos=grid_pos,
            targets=targets,
            field_config=field_config,
            options=data.get("options", {}),
            datasource=datasource,
            description=data.get("description"),
            transparent=data.get("transparent", False),
            collapsed=data.get("collapsed", False),
            panels=panels
        )


@dataclass
class TemplateVariable:
    """Represents a dashboard template variable"""
    name: str
    type: str = VariableType.QUERY.value
    query: str = ""
    current: Dict[str, Any] = field(default_factory=dict)
    options: List[Dict[str, Any]] = field(default_factory=list)
    datasource: Optional[DataSource] = None
    definition: str = ""
    hide: int = 0
    include_all: bool = False
    multi: bool = False
    refresh: int = 1
    regex: str = ""
    skip_url_sync: bool = False
    sort: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        result = {
            "name": self.name,
            "type": self.type,
            "query": self.query,
            "current": self.current,
            "options": self.options,
            "definition": self.definition,
            "hide": self.hide,
            "includeAll": self.include_all,
            "multi": self.multi,
            "refresh": self.refresh,
            "regex": self.regex,
            "skipUrlSync": self.skip_url_sync,
            "sort": self.sort
        }
        
        if self.datasource:
            result["datasource"] = self.datasource.to_dict()
        
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateVariable':
        """Create from dictionary"""
        datasource = None
        if "datasource" in data:
            datasource_data = data["datasource"]
            if isinstance(datasource_data, str):
                # Handle string datasource (legacy format)
                datasource = DataSource(type="", uid=datasource_data)
            elif isinstance(datasource_data, dict):
                # Handle dictionary datasource (standard format)
                datasource = DataSource.from_dict(datasource_data)
            else:
                # Invalid datasource format
                datasource = None
        
        return cls(
            name=data.get("name", ""),
            type=data.get("type", VariableType.QUERY.value),
            query=data.get("query", ""),
            current=data.get("current", {}),
            options=data.get("options", []),
            datasource=datasource,
            definition=data.get("definition", ""),
            hide=data.get("hide", 0),
            include_all=data.get("includeAll", False),
            multi=data.get("multi", False),
            refresh=data.get("refresh", 1),
            regex=data.get("regex", ""),
            skip_url_sync=data.get("skipUrlSync", False),
            sort=data.get("sort", 0)
        )
    
    def __str__(self) -> str:
        """Return a formatted string representation of the variable"""
        parts = [f"Variable: ${{{self.name}}}"]
        parts.append(f"  Type: {self.type}")
        
        if self.query:
            parts.append(f"  Query: {self.query}")
        
        if self.datasource:
            parts.append(f"  Datasource: {self.datasource.type} ({self.datasource.uid})")
        
        if self.current:
            current_value = self.current.get('value', 'N/A')
            parts.append(f"  Current Value: {current_value}")
        
        flags = []
        if self.multi:
            flags.append("multi-select")
        if self.include_all:
            flags.append("include-all")
        if self.hide:
            flags.append("hidden")
        
        if flags:
            parts.append(f"  Flags: {', '.join(flags)}")
        
        return "\n".join(parts)


@dataclass
class TimeRange:
    """Represents dashboard time range"""
    from_time: str = "now-1h"
    to_time: str = "now"
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format"""
        return {"from": self.from_time, "to": self.to_time}

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'TimeRange':
        """Create from dictionary"""
        return cls(
            from_time=data.get("from", "now-1h"),
            to_time=data.get("to", "now")
        )


@dataclass
class Annotation:
    """Represents a dashboard annotation"""
    name: str = "Annotations & Alerts"
    datasource: Dict[str, str] = field(default_factory=lambda: {"type": "grafana", "uid": "-- Grafana --"})
    enable: bool = True
    hide: bool = True
    icon_color: str = "rgba(0, 211, 255, 1)"
    type: str = "dashboard"
    built_in: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "name": self.name,
            "datasource": self.datasource,
            "enable": self.enable,
            "hide": self.hide,
            "iconColor": self.icon_color,
            "type": self.type,
            "builtIn": self.built_in
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Annotation':
        """Create from dictionary"""
        return cls(
            name=data.get("name", "Annotations & Alerts"),
            datasource=data.get("datasource", {"type": "grafana", "uid": "-- Grafana --"}),
            enable=data.get("enable", True),
            hide=data.get("hide", True),
            icon_color=data.get("iconColor", "rgba(0, 211, 255, 1)"),
            type=data.get("type", "dashboard"),
            built_in=data.get("builtIn", 1)
        )


@dataclass
class GrafanaDashboard:
    """Represents a complete Grafana dashboard"""
    title: str
    uid: Optional[str] = None
    id: Optional[int] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)
    panels: List[Panel] = field(default_factory=list)
    time: TimeRange = field(default_factory=TimeRange)
    templating: List[TemplateVariable] = field(default_factory=list)
    annotations: List[Annotation] = field(default_factory=list)
    refresh: str = "5s"
    schema_version: int = 39
    version: int = 1
    editable: bool = True
    graph_tooltip: int = 0
    timezone: str = "browser"
    fiscal_year_start_month: int = 0
    links: List[Dict[str, Any]] = field(default_factory=list)
    live_now: bool = False
    week_start: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert dashboard to dictionary format"""
        result = {
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "panels": [panel.to_dict() for panel in self.panels],
            "time": self.time.to_dict(),
            "templating": {
                "list": [var.to_dict() for var in self.templating]
            },
            "annotations": {
                "list": [annotation.to_dict() for annotation in self.annotations]
            },
            "refresh": self.refresh,
            "schemaVersion": self.schema_version,
            "version": self.version,
            "editable": self.editable,
            "graphTooltip": self.graph_tooltip,
            "timezone": self.timezone,
            "fiscalYearStartMonth": self.fiscal_year_start_month,
            "links": self.links,
            "liveNow": self.live_now
        }
        
        if self.uid:
            result["uid"] = self.uid
        
        if self.id:
            result["id"] = self.id
        
        if self.week_start:
            result["weekStart"] = self.week_start
        
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GrafanaDashboard':
        """Create dashboard from dictionary"""
        # Parse panels
        panels = []
        for panel_data in data.get("panels", []):
            panels.append(Panel.from_dict(panel_data))
        
        # Parse time range
        time_range = TimeRange.from_dict(data.get("time", {}))

        # print('data', json.dumps(data, indent=2))
        
        # Parse template variables
        templating_data = data.get("templating", {})
        # print('templating_data', templating_data)
        variables = []
        for var_data in templating_data.get("list", []):

            # print('var_data', var_data)

            variables.append(TemplateVariable.from_dict(var_data))
        
        # Parse annotations
        annotations_data = data.get("annotations", {})
        annotations = []
        for annotation_data in annotations_data.get("list", []):
            annotations.append(Annotation.from_dict(annotation_data))
        
        # If no annotations exist, add default one
        if not annotations:
            annotations.append(Annotation())
        
        return cls(
            title=data.get("title", "Untitled Dashboard"),
            uid=data.get("uid"),
            id=data.get("id"),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            panels=panels,
            time=time_range,
            templating=variables,
            annotations=annotations,
            refresh=data.get("refresh", "5s"),
            schema_version=data.get("schemaVersion", 39),
            version=data.get("version", 1),
            editable=data.get("editable", True),
            graph_tooltip=data.get("graphTooltip", 0),
            timezone=data.get("timezone", "browser"),
            fiscal_year_start_month=data.get("fiscalYearStartMonth", 0),
            links=data.get("links", []),
            live_now=data.get("liveNow", False),
            week_start=data.get("weekStart", "")
        )

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Convert dashboard to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'GrafanaDashboard':
        """Create dashboard from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def add_panel(self, panel: Panel) -> None:
        """Add a panel to the dashboard"""
        # Auto-assign ID if not set
        if panel.id is None or panel.id == 0:
            existing_ids = {p.id for p in self.panels if p.id}
            panel.id = max(existing_ids, default=0) + 1
        
        # Auto-position panel if not set
        if panel.grid_pos.x == 0 and panel.grid_pos.y == 0:
            max_y = max((p.grid_pos.y + p.grid_pos.h for p in self.panels), default=0)
            panel.grid_pos.y = max_y
        
        self.panels.append(panel)

    def remove_panel(self, panel_id: int) -> bool:
        """Remove a panel by ID"""
        for i, panel in enumerate(self.panels):
            if panel.id == panel_id:
                del self.panels[i]
                return True
        return False

    def get_panel_by_id(self, panel_id: int) -> Optional[Panel]:
        """Get a panel by ID"""
        for panel in self.panels:
            if panel.id == panel_id:
                return panel
        return None

    def get_panels_by_type(self, panel_type: str) -> List[Panel]:
        """Get all panels of a specific type"""
        return [panel for panel in self.panels if panel.type == panel_type]

    def add_variable(self, variable: TemplateVariable) -> None:
        """Add a template variable to the dashboard"""
        self.templating.append(variable)

    def remove_variable(self, variable_name: str) -> bool:
        """Remove a template variable by name"""
        for i, var in enumerate(self.templating):
            if var.name == variable_name:
                del self.templating[i]
                return True
        return False

    def get_variable_by_name(self, variable_name: str) -> Optional[TemplateVariable]:
        """Get a template variable by name"""
        for var in self.templating:
            if var.name == variable_name:
                return var
        return None

    def get_variables_formatted(self, format_type: str = "detailed") -> str:
        """
        Get template variables as a formatted string.
        
        Args:
            format_type: Format type - "detailed", "summary", or "list"
        
        Returns:
            Formatted string representation of template variables
        """
        if not self.templating:
            return "No template variables defined"
        
        if not self.templating:
            return "No template variables defined"
        
        if format_type == "list":
            # Simple list format
            var_list = [f"${{{var.name}}}" for var in self.templating]
            return f"Template Variables ({len(var_list)}): {', '.join(var_list)}"
        
        elif format_type == "summary":
            # Summary format with basic info
            lines = [f"Template Variables ({len(self.templating)}):"]
            # lines.append("-" * 60)
            for var in self.templating:
                # print('var', var)
                flags = []
                if var.multi:
                    flags.append("multi")
                if var.include_all:
                    flags.append("all")
                if var.hide:
                    flags.append("hidden")
                flag_str = f" [{', '.join(flags)}]" if flags else ""
                
                current_val = '' # var.current.get('value', 'N/A') if var.current else 'N/A'
                lines.append(f"  {var.name} ({var.type}): {current_val}{flag_str}")
            
            return "\n".join(lines)
        
        else:  # detailed format
            # Detailed format with all information
            lines = [f"Template Variables ({len(self.templating)}):"]
            lines.append("=" * 60)
            
            for i, var in enumerate(self.templating, 1):
                lines.append(f"\n{i}. {str(var)}")
            
            return "\n".join(lines)

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate dashboard structure and return validation results"""
        errors = []
        
        # Check for duplicate panel IDs
        panel_ids = [panel.id for panel in self.panels]
        if len(panel_ids) != len(set(panel_ids)):
            errors.append("Duplicate panel IDs found")
        
        # Check for overlapping panels
        for i, panel1 in enumerate(self.panels):
            for panel2 in self.panels[i+1:]:
                if self._panels_overlap(panel1, panel2):
                    errors.append(f"Panels {panel1.id} and {panel2.id} overlap")
        
        # Check for duplicate variable names
        var_names = [var.name for var in self.templating]
        if len(var_names) != len(set(var_names)):
            errors.append("Duplicate variable names found")
        
        # Check title is not empty
        if not self.title.strip():
            errors.append("Dashboard title cannot be empty")
        
        return len(errors) == 0, errors

    def _panels_overlap(self, panel1: Panel, panel2: Panel) -> bool:
        """Check if two panels overlap"""
        pos1, pos2 = panel1.grid_pos, panel2.grid_pos
        
        # Check if rectangles overlap
        return not (pos1.x + pos1.w <= pos2.x or 
                   pos2.x + pos2.w <= pos1.x or
                   pos1.y + pos1.h <= pos2.y or 
                   pos2.y + pos2.h <= pos1.y)

    def auto_layout(self, columns: int = 2) -> None:
        """Automatically layout panels in a grid"""
        panel_width = 24 // columns
        current_x = 0
        current_y = 0
        
        for panel in self.panels:
            panel.grid_pos.x = current_x
            panel.grid_pos.y = current_y
            panel.grid_pos.w = panel_width
            
            current_x += panel_width
            if current_x >= 24:
                current_x = 0
                current_y += panel.grid_pos.h

    def clone(self) -> 'GrafanaDashboard':
        """Create a deep copy of the dashboard"""
        return GrafanaDashboard.from_dict(self.to_dict())


class GrafanaDashboardBuilder:
    """Builder class for creating Grafana dashboards programmatically"""
    
    def __init__(self, title: str):
        """Initialize builder with dashboard title"""
        self.dashboard = GrafanaDashboard(title=title)
    
    def with_description(self, description: str) -> 'GrafanaDashboardBuilder':
        """Set dashboard description"""
        self.dashboard.description = description
        return self
    
    def with_tags(self, tags: List[str]) -> 'GrafanaDashboardBuilder':
        """Set dashboard tags"""
        self.dashboard.tags = tags
        return self
    
    def with_time_range(self, from_time: str, to_time: str) -> 'GrafanaDashboardBuilder':
        """Set dashboard time range"""
        self.dashboard.time = TimeRange(from_time, to_time)
        return self
    
    def with_refresh_interval(self, interval: str) -> 'GrafanaDashboardBuilder':
        """Set dashboard refresh interval"""
        self.dashboard.refresh = interval
        return self
    
    def with_uid(self, uid: str) -> 'GrafanaDashboardBuilder':
        """Set dashboard UID"""
        self.dashboard.uid = uid
        return self
    
    def add_timeseries_panel(self, title: str, targets: List[QueryTarget], 
                           grid_pos: Optional[GridPosition] = None) -> 'GrafanaDashboardBuilder':
        """Add a timeseries panel"""
        panel_id = len(self.dashboard.panels) + 1
        panel = Panel(
            id=panel_id,
            title=title,
            type=PanelType.TIMESERIES.value,
            targets=targets,
            grid_pos=grid_pos or GridPosition()
        )
        self.dashboard.add_panel(panel)
        return self
    
    def add_table_panel(self, title: str, targets: List[QueryTarget],
                       grid_pos: Optional[GridPosition] = None) -> 'GrafanaDashboardBuilder':
        """Add a table panel"""
        panel_id = len(self.dashboard.panels) + 1
        panel = Panel(
            id=panel_id,
            title=title,
            type=PanelType.TABLE.value,
            targets=targets,
            grid_pos=grid_pos or GridPosition()
        )
        self.dashboard.add_panel(panel)
        return self
    
    def add_stat_panel(self, title: str, targets: List[QueryTarget],
                      grid_pos: Optional[GridPosition] = None) -> 'GrafanaDashboardBuilder':
        """Add a stat panel"""
        panel_id = len(self.dashboard.panels) + 1
        panel = Panel(
            id=panel_id,
            title=title,
            type=PanelType.STAT.value,
            targets=targets,
            grid_pos=grid_pos or GridPosition()
        )
        self.dashboard.add_panel(panel)
        return self
    
    def add_query_variable(self, name: str, query: str, datasource: DataSource,
                          multi: bool = False, include_all: bool = False) -> 'GrafanaDashboardBuilder':
        """Add a query template variable"""
        variable = TemplateVariable(
            name=name,
            type=VariableType.QUERY.value,
            query=query,
            datasource=datasource,
            multi=multi,
            include_all=include_all
        )
        self.dashboard.add_variable(variable)
        return self
    
    def add_custom_variable(self, name: str, options: List[str],
                          multi: bool = False, include_all: bool = False) -> 'GrafanaDashboardBuilder':
        """Add a custom template variable"""
        formatted_options = [{"text": opt, "value": opt} for opt in options]
        variable = TemplateVariable(
            name=name,
            type=VariableType.CUSTOM.value,
            options=formatted_options,
            current={"text": options[0] if options else "", "value": options[0] if options else ""},
            multi=multi,
            include_all=include_all
        )
        self.dashboard.add_variable(variable)
        return self
    
    def build(self) -> GrafanaDashboard:
        """Build and return the dashboard"""
        return self.dashboard


class GrafanaDashboardParser:
    """Parser for Grafana dashboard JSON with robust error handling"""
    
    @staticmethod
    def parse_json_string(json_str: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        """
        Parse JSON string with robust error handling and automatic fixes.
        
        Returns:
            Tuple of (parsed_dict, list_of_warnings)
        """
        warnings = []
        
        if not json_str or not json_str.strip():
            return None, ["Empty JSON string provided"]
        
        original_json = json_str.strip()
        
        # Try direct parsing first
        try:
            # print(json.dumps(json.loads(original_json), indent=2))
            return json.loads(original_json), warnings
        except json.JSONDecodeError:
            print('Failed to parse JSON: Invalid JSON format')
            pass
        
        # Remove common formatting issues
        cleaned_json = original_json
        
        # Remove markdown code blocks
        if cleaned_json.startswith('```json'):
            cleaned_json = cleaned_json[7:]
            warnings.append("Removed JSON markdown formatting")
        elif cleaned_json.startswith('```'):
            cleaned_json = cleaned_json[3:]
            warnings.append("Removed markdown formatting")
        
        if cleaned_json.endswith('```'):
            cleaned_json = cleaned_json[:-3]
        
        cleaned_json = cleaned_json.strip()
        
        try:
            return json.loads(cleaned_json), warnings
        except json.JSONDecodeError:
            pass
        
        # Try to fix common JSON issues
        fixes = [
            # Remove trailing commas
            (lambda x: re.sub(r',(\s*[}\]])', r'\1', x), "Removed trailing commas"),
            # Fix single quotes
            (lambda x: re.sub(r"'([^']*)':", r'"\1":', x), "Fixed single quotes"),
            # Remove comments
            (lambda x: re.sub(r'//.*', '', x), "Removed comments"),
            # Fix unquoted keys
            (lambda x: re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', x), "Fixed unquoted keys")
        ]
        
        current_json = cleaned_json
        for fix_func, warning_msg in fixes:
            try:
                fixed_json = fix_func(current_json)
                parsed = json.loads(fixed_json)
                warnings.append(warning_msg)
                return parsed, warnings
            except json.JSONDecodeError:
                current_json = fixed_json if 'fixed_json' in locals() else current_json
                continue
        
        return None, [f"Could not parse JSON: Invalid JSON format"]
    
    @staticmethod
    def parse_dashboard(json_str: str) -> Tuple[Optional[GrafanaDashboard], List[str]]:
        """
        Parse dashboard from JSON string.
        
        Returns:
            Tuple of (dashboard_object, list_of_warnings_and_errors)
        """
        parsed_data, parse_warnings = GrafanaDashboardParser.parse_json_string(json_str)
        
        if parsed_data is None:
            return None, parse_warnings
        
        try:
            dashboard = GrafanaDashboard.from_dict(parsed_data)
            
            # Validate the dashboard
            is_valid, validation_errors = dashboard.validate()
            
            all_messages = parse_warnings + validation_errors
            return dashboard, all_messages
            
        except Exception as e:
            return None, parse_warnings + [f"Error creating dashboard object: {str(e)}"]
    
    @staticmethod
    def parse_dashboard_from_file(file_path: str) -> Tuple[Optional[GrafanaDashboard], List[str]]:
        """Parse dashboard from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_content = f.read()
            return GrafanaDashboardParser.parse_dashboard(json_content)
        except Exception as e:
            return None, [f"Error reading file {file_path}: {str(e)}"]


class GrafanaDashboardManager:
    """High-level manager for dashboard operations"""
    
    def __init__(self):
        """Initialize the dashboard manager"""
        pass
    
    def load_dashboard(self, source: Union[str, Dict[str, Any]]) -> Tuple[Optional[GrafanaDashboard], List[str]]:
        """
        Load dashboard from various sources (JSON string, dict, or file path).
        
        Args:
            source: JSON string, dictionary, or file path
            
        Returns:
            Tuple of (dashboard, warnings/errors)
        """
        if isinstance(source, dict):
            try:
                dashboard = GrafanaDashboard.from_dict(source)
                is_valid, errors = dashboard.validate()
                return dashboard, errors
            except Exception as e:
                return None, [f"Error creating dashboard from dict: {str(e)}"]
        
        elif isinstance(source, str):
            # Check if it's a file path or JSON string
            if source.strip().startswith('{') or source.strip().startswith('['):
                # It's JSON content
                return GrafanaDashboardParser.parse_dashboard(source)
            else:
                # It's likely a file path
                return GrafanaDashboardParser.parse_dashboard_from_file(source)
        
        else:
            return None, ["Invalid source type. Expected dict, JSON string, or file path"]
    
    def save_dashboard(self, dashboard: GrafanaDashboard, file_path: str, 
                      indent: int = 2) -> Tuple[bool, List[str]]:
        """
        Save dashboard to JSON file.
        
        Args:
            dashboard: Dashboard to save
            file_path: Output file path
            indent: JSON indentation
            
        Returns:
            Tuple of (success, errors)
        """
        try:
            # Validate dashboard before saving
            is_valid, errors = dashboard.validate()
            if not is_valid:
                return False, [f"Dashboard validation failed: {'; '.join(errors)}"]
            
            json_content = dashboard.to_json(indent=indent)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_content)
            
            return True, []
            
        except Exception as e:
            return False, [f"Error saving dashboard: {str(e)}"]
    
    def create_dashboard(self, title: str) -> GrafanaDashboardBuilder:
        """Create a new dashboard using the builder pattern"""
        return GrafanaDashboardBuilder(title)
    
    def merge_dashboards(self, dashboard1: GrafanaDashboard, dashboard2: GrafanaDashboard,
                        merge_strategy: str = "append") -> Tuple[Optional[GrafanaDashboard], List[str]]:
        """
        Merge two dashboards.
        
        Args:
            dashboard1: Primary dashboard
            dashboard2: Dashboard to merge into primary
            merge_strategy: "append", "replace", or "merge"
            
        Returns:
            Tuple of (merged_dashboard, warnings)
        """
        try:
            result = dashboard1.clone()
            warnings = []
            
            if merge_strategy == "append":
                # Add all panels from dashboard2
                max_id = max((p.id for p in result.panels), default=0)
                for panel in dashboard2.panels:
                    new_panel = Panel.from_dict(panel.to_dict())
                    new_panel.id = max_id + 1
                    max_id += 1
                    result.add_panel(new_panel)
                
                # Add variables that don't exist
                existing_vars = {var.name for var in result.templating}
                for var in dashboard2.templating:
                    if var.name not in existing_vars:
                        result.add_variable(var)
                    else:
                        warnings.append(f"Variable '{var.name}' already exists, skipping")
            
            elif merge_strategy == "replace":
                # Replace panels and variables entirely
                result.panels = [Panel.from_dict(p.to_dict()) for p in dashboard2.panels]
                result.templating = [TemplateVariable.from_dict(v.to_dict()) for v in dashboard2.templating]
            
            elif merge_strategy == "merge":
                # Smart merge - update existing, add new
                existing_panel_ids = {p.id for p in result.panels}
                for panel in dashboard2.panels:
                    if panel.id in existing_panel_ids:
                        # Update existing panel
                        for i, existing_panel in enumerate(result.panels):
                            if existing_panel.id == panel.id:
                                result.panels[i] = Panel.from_dict(panel.to_dict())
                                break
                        warnings.append(f"Updated existing panel {panel.id}")
                    else:
                        # Add new panel
                        result.add_panel(Panel.from_dict(panel.to_dict()))
                
                # Merge variables similarly
                existing_var_names = {var.name for var in result.templating}
                for var in dashboard2.templating:
                    if var.name in existing_var_names:
                        # Update existing variable
                        for i, existing_var in enumerate(result.templating):
                            if existing_var.name == var.name:
                                result.templating[i] = TemplateVariable.from_dict(var.to_dict())
                                break
                        warnings.append(f"Updated existing variable '{var.name}'")
                    else:
                        result.add_variable(TemplateVariable.from_dict(var.to_dict()))
            
            # Auto-layout to prevent overlaps
            result.auto_layout()
            
            return result, warnings
            
        except Exception as e:
            return None, [f"Error merging dashboards: {str(e)}"]
    
    def validate_dashboard(self, dashboard: GrafanaDashboard) -> Tuple[bool, List[str], List[str]]:
        """
        Comprehensive dashboard validation.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        # Basic validation
        is_valid, basic_errors = dashboard.validate()
        errors.extend(basic_errors)
        
        # Additional checks
        if len(dashboard.panels) == 0:
            warnings.append("Dashboard has no panels")
        
        if len(dashboard.templating) == 0:
            warnings.append("Dashboard has no template variables")
        
        # Check for panels with no data sources
        panels_without_datasource = [p for p in dashboard.panels 
                                   if not p.datasource and not p.targets]
        if panels_without_datasource:
            warnings.append(f"{len(panels_without_datasource)} panels have no datasource or targets")
        
        # Check time range validity
        time_patterns = [r'now-\d+[smhdwMy]', r'now', r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}']
        if not any(re.match(pattern, dashboard.time.from_time) for pattern in time_patterns):
            warnings.append(f"Unusual time range 'from' value: {dashboard.time.from_time}")
        
        return len(errors) == 0, errors, warnings


# Example usage and convenience functions
def create_simple_dashboard(title: str, panels_config: List[Dict[str, Any]]) -> GrafanaDashboard:
    """
    Create a simple dashboard from basic configuration.
    
    Args:
        title: Dashboard title
        panels_config: List of panel configurations
    
    Returns:
        GrafanaDashboard object
    """
    builder = GrafanaDashboardBuilder(title)
    
    for i, config in enumerate(panels_config):
        panel_type = config.get('type', 'timeseries')
        panel_title = config.get('title', f'Panel {i+1}')
        
        # Create basic target if query provided
        targets = []
        if 'query' in config:
            target = QueryTarget(
                ref_id="A",
                expr=config['query'] if 'expr' in config else None,
                raw_sql=config['query'] if 'sql' in config else None
            )
            targets.append(target)
        
        grid_pos = GridPosition(
            x=config.get('x', 0),
            y=config.get('y', i * 8),
            w=config.get('w', 12),
            h=config.get('h', 8)
        )
        
        if panel_type == 'timeseries':
            builder.add_timeseries_panel(panel_title, targets, grid_pos)
        elif panel_type == 'table':
            builder.add_table_panel(panel_title, targets, grid_pos)
        elif panel_type == 'stat':
            builder.add_stat_panel(panel_title, targets, grid_pos)
    
    return builder.build()


# Export main classes and functions
__all__ = [
    'GrafanaDashboard',
    'GrafanaDashboardBuilder', 
    'GrafanaDashboardParser',
    'GrafanaDashboardManager',
    'Panel',
    'QueryTarget',
    'TemplateVariable',
    'DataSource',
    'GridPosition',
    'TimeRange',
    'FieldConfig',
    'Annotation',
    'PanelType',
    'VariableType',
    'create_simple_dashboard'
]
