

from typing import List, Dict, Any, Tuple
import json

def get_dashboard_analysis_prompt(formatted_dashboard: str) -> tuple[str, str]:

        prompt = f"""Analyze the following Grafana dashboard configuration and provide a comprehensive summary:

{formatted_dashboard}

Please provide:
1. **Dashboard Overview**: Purpose and main functionality
2. **Panel Analysis**: Types of visualizations and their purposes
3. **Data Sources**: What metrics or data are being monitored
4. **Layout and Organization**: How the dashboard is structured
5. **Key Insights**: What business/technical insights this dashboard provides
6. **Recommendations**: Potential improvements or optimizations

Format your response in clear sections with bullet points where appropriate."""
        
        system_prompt = "You are a Grafana dashboard expert who provides detailed analysis and insights about dashboard configurations. Focus on the monitoring strategy, visualization choices, and overall effectiveness."
        
        return prompt, system_prompt


def get_dashboard_modification_suggestions_prompt(dashboard_obj: Any, panels_summary: list[dict], table_information_str: str, modification_request: str) -> tuple[str, str]:


        prompt = f"""You are a Grafana dashboard expert. Analyze the user's request and suggest specific panel modifications.

Current Dashboard: {dashboard_obj.title}
Current Panels Summary:
{json.dumps(panels_summary, indent=2)}

Available Database Tables:
{table_information_str}

User's Request: {modification_request}

Based on the request, the current dashboard panels, and the available database table information, suggest panel operations. Use the table schema and sample data to create appropriate queries and visualizations. For each operation, provide:

1. **ADD operations** - New panels to add:
   - Provide complete panel JSON configuration
   - Assign new unique panel IDs (start from {max([p.id for p in dashboard_obj.panels], default=0) + 1})
   - Set appropriate grid positions to avoid overlaps
   - Include proper datasource references and queries based on available table schemas
   - Use column names and data types from the table information to create accurate SQL queries
   - Consider sample data patterns when designing visualizations

2. **REMOVE operations** - Existing panels to remove:
   - Specify panel ID to remove
   - Provide reason for removal

3. **MODIFY operations** - Existing panels to update:
   - Specify panel ID to modify
   - Provide updated panel JSON configuration
   - Keep existing ID and adjust only necessary fields

Respond with a JSON array of operations in this format:
[
  {{
    "action": "add",
    "panel": {{
      "id": 999,
      "title": "New Panel Title",
      "type": "timeseries",
      "gridPos": {{"h": 8, "w": 12, "x": 0, "y": 16}},
      "targets": [...],
      "fieldConfig": {{"defaults": {{}}, "overrides": []}},
      "options": {{}}
    }},
    "reason": "Adding new panel for monitoring XYZ"
  }},
  {{
    "action": "remove",
    "panel_id": 2,
    "reason": "Panel no longer needed based on user request"
  }},
  {{
    "action": "modify",
    "panel_id": 1,
    "panel": {{
      "id": 1,
      "title": "Updated Title",
      ...updated fields only...
    }},
    "reason": "Updated panel title and configuration"
  }}
]

Respond with ONLY the JSON array, no additional text."""
        
        system_prompt = "You are a Grafana dashboard expert. You analyze user requests and suggest specific panel operations (add, remove, modify) with complete JSON configurations. Always respond with valid JSON only."
        
        return prompt, system_prompt


def get_table_list_prompt(dashboard: Any, panel_queries: list[str], modification_request: str) -> str:

        # Create prompt to analyze what tables might be needed
        prompt = f"""Analyze the following Grafana dashboard modification request and existing panel queries to determine which database tables might be relevant and return only a simple comma-separated list of table names (no explanations)

Dashboard Title: {dashboard.get('title', 'Unknown')}

User's Modification Request:
{modification_request}

Existing Panel Queries:
{chr(10).join(panel_queries) if panel_queries else 'No existing queries found'}

Based on this information, provide a list of database table names that might be relevant for this modification. Consider:
1. Tables mentioned in existing queries
2. Tables that might be needed for the requested modification
3. Common table patterns for the type of data being requested

Return only a simple comma-separated list of table names (no explanations):"""

        return prompt