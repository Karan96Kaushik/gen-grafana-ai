"""
Grafana Dashboard Manager - AI-powered dashboard analysis and modification
Integrates with PostgreSQL to manage Grafana dashboards using Groq LLM API
Enhanced with GrafanaDashboardParser for robust dashboard manipulation
"""

import os
import sys
import json
import re
import logging
import psycopg2
from groq import Groq
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid
import traceback

from grafana_dashboard_prompts import get_dashboard_analysis_prompt
from grafana_dashboard_prompts import get_dashboard_modification_suggestions_prompt
from grafana_dashboard_prompts import get_table_list_prompt


# As per literature research, this would work well for code/json generation
DASHBOARD_MODEL = "qwen/qwen3-32b"
DASHBOARD_MODEL = "openai/gpt-oss-20b"

# As per testing, this works well for table data analysis
TABLEDATA_MODEL = "llama-3.3-70b-versatile"


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

# Import the new dashboard library
try:
    from grafana_dashboard_lib import (
        GrafanaDashboard,
        GrafanaDashboardParser,
        GrafanaDashboardManager as DashboardLibManager,
        Panel,
        QueryTarget,
        DataSource,
        GridPosition,
        PanelType
    )
    DASHBOARD_LIB_AVAILABLE = True
except ImportError:
    print("⚠️  Warning: grafana_dashboard_lib not available. Some features may be limited.")
    DASHBOARD_LIB_AVAILABLE = False

# Import database explorer
import db_explorer

# Load environment variables
load_dotenv()

class GrafanaDashboardManager:
    """Manages Grafana dashboards with AI-powered analysis and modification capabilities."""
    
    def __init__(self):
        """Initialize connections to PostgreSQL and Groq"""
        # PostgreSQL connection
        self.db_config = {
            'host': os.getenv('psgrsql_db_host', 'localhost'),
            'database': 'grafana_test', #os.getenv('psgrsql_db_name', 'grafana_test'),
            'user': os.getenv('psgrsql_db_user', 'postgres'),
            'password': os.getenv('psgrsql_db_pswd', 'password'),
            'port': os.getenv('psgrsql_db_port', '5432')
        }
        
        # Groq client with error handling
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        try:
            self.groq_client = Groq(api_key=groq_api_key)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Groq client: {e}")
        
        self.model = DASHBOARD_MODEL
        self.dashboard_table = "dashboard"
        self.schema = "public"
        
        # Initialize dashboard library manager if available
        if DASHBOARD_LIB_AVAILABLE:
            self.dashboard_lib_manager = DashboardLibManager()
            print("✅ Dashboard library integration enabled")
        else:
            self.dashboard_lib_manager = None
        
        # Initialize logging
        self.setup_logging()
    
    def setup_logging(self):
        """Setup comprehensive logging for prompts and responses"""
        # Create logs directory if it doesn't exist
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Create unique log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(log_dir, f"grafana_manager_{timestamp}.log")
        
        # Setup logger
        self.logger = logging.getLogger(f"GrafanaManager_{timestamp}")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler for detailed logging
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Console handler for basic info
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Create detailed formatter
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(funcName)s | %(message)s'
        )
        
        # Create simple formatter for console
        simple_formatter = logging.Formatter('%(levelname)s: %(message)s')
        
        file_handler.setFormatter(detailed_formatter)
        console_handler.setFormatter(simple_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Log initialization
        self.logger.info("=" * 80)
        self.logger.info("GRAFANA DASHBOARD MANAGER - SESSION STARTED")
        self.logger.info("=" * 80)
        self.logger.info(f"Dashboard Model: {DASHBOARD_MODEL}")
        self.logger.info(f"Table Data Model: {TABLEDATA_MODEL}")
        self.logger.info(f"Database: {self.db_config['database']}")
        self.logger.info(f"Log file: {self.log_file}")
        
        print(f"📝 Logging enabled - Session logs saved to: {self.log_file}")
    
    def log_prompt_and_response(self, operation: str, prompt: str, response: str, 
                              metadata: Optional[Dict[str, Any]] = None):
        """
        Log prompts and responses with detailed metadata
        
        Args:
            operation: Type of operation (e.g., 'dashboard_analysis', 'dashboard_modification')
            prompt: The prompt sent to the LLM
            response: The response received from the LLM
            metadata: Additional metadata like dashboard_id, user_request, etc.
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "model": DASHBOARD_MODEL,
            "model_table_data": TABLEDATA_MODEL,
            "prompt_length": len(prompt),
            "response_length": len(response),
            "metadata": metadata or {}
        }
        
        # Log the interaction
        self.logger.info("-" * 80)
        self.logger.info(f"OPERATION: {operation}")
        self.logger.info(f"METADATA: {json.dumps(log_entry['metadata'], indent=2)}")
        self.logger.info("-" * 40)
        self.logger.info("PROMPT:")
        self.logger.info(prompt)
        self.logger.info("-" * 40)
        self.logger.info("RESPONSE:")
        self.logger.info(response)
        self.logger.info("-" * 80)
        
        # Also save as structured JSON for easy parsing
        json_log_file = self.log_file.replace('.log', '_structured.jsonl')
        try:
            with open(json_log_file, 'a', encoding='utf-8') as f:
                json_entry = {
                    **log_entry,
                    "prompt": prompt,
                    "response": response
                }
                f.write(json.dumps(json_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write structured log: {e}")
    
    def log_error(self, operation: str, error_message: str, context: Optional[Dict[str, Any]] = None):
        """Log errors with context"""
        self.logger.error("-" * 80)
        self.logger.error(f"ERROR IN OPERATION: {operation}")
        self.logger.error(f"ERROR MESSAGE: {error_message}")
        if context:
            self.logger.error(f"CONTEXT: {json.dumps(context, indent=2)}")
        self.logger.error("-" * 80)
    
    def connect_db(self):
        """Create database connection"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    
    def get_dashboard_list(self) -> List[Dict[str, Any]]:
        """Get list of all dashboards from the database"""
        conn = self.connect_db()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT id, title, slug, created, updated, data
                FROM {self.schema}.{self.dashboard_table}
                WHERE org_id = 1
                ORDER BY updated DESC
            """)
            
            dashboards = []
            for row in cursor.fetchall():
                dashboard = {
                    'id': row[0],
                    'title': row[1],
                    'slug': row[2],
                    'created': row[3],
                    'updated': row[4],
                    'data': row[5]
                }
                dashboards.append(dashboard)
            
            cursor.close()
            conn.close()
            return dashboards
            
        except Exception as e:
            print(f"Error fetching dashboards: {e}")
            return []
    
    def get_dashboard_by_id(self, dashboard_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific dashboard by ID"""
        conn = self.connect_db()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT id, title, slug, created, updated, data
                FROM {self.schema}.{self.dashboard_table}
                WHERE id = %s
            """, (dashboard_id,))
            
            row = cursor.fetchone()
            if row:
                dashboard = {
                    'id': row[0],
                    'title': row[1],
                    'slug': row[2],
                    'created': row[3],
                    'updated': row[4],
                    'data': row[5]
                }
                cursor.close()
                conn.close()
                return dashboard
            
            cursor.close()
            conn.close()
            return None
            
        except Exception as e:
            print(f"Error fetching dashboard: {e}")
            return None
    
    def get_dashboard_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get a specific dashboard by slug"""
        conn = self.connect_db()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT id, title, slug, created, updated, data
                FROM {self.schema}.{self.dashboard_table}
                WHERE slug = %s
            """, (slug,))
            
            row = cursor.fetchone()
            if row:
                dashboard = {
                    'id': row[0],
                    'title': row[1],
                    'slug': row[2],
                    'created': row[3],
                    'updated': row[4],
                    'data': row[5]
                }
                cursor.close()
                conn.close()
                return dashboard
            
            cursor.close()
            conn.close()
            return None
            
        except Exception as e:
            print(f"Error fetching dashboard by slug: {e}")
            return None
    
    def insert_dashboard(self, title: str, slug: str, data: Dict[str, Any], uid: str) -> Optional[int]:
        """Insert a new dashboard into the database or update existing one if slug exists"""
        conn = self.connect_db()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            now = datetime.now()
            
            # Check if slug already exists
            cursor.execute(f"""
                SELECT id, version FROM {self.schema}.{self.dashboard_table}
                WHERE slug = %s
            """, (slug,))
            
            existing_dashboard = cursor.fetchone()
            
            if existing_dashboard:
                # Update existing dashboard
                dashboard_id, current_version = existing_dashboard
                new_version = current_version + 1
                
                cursor.execute(f"""
                    UPDATE {self.schema}.{self.dashboard_table}
                    SET title = %s, updated = %s, data = %s, version = %s, uid = %s
                    WHERE id = %s
                """, (title, now, json.dumps(data), new_version, uid, dashboard_id))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                return dashboard_id
            else:
                # Insert new dashboard
                cursor.execute(f"""
                    INSERT INTO {self.schema}.{self.dashboard_table} (title, slug, created, updated, data, version, org_id, uid)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (title, slug, now, now, json.dumps(data), 1, 1, uid))
                
                dashboard_id = cursor.fetchone()[0]
                conn.commit()
                cursor.close()
                conn.close()
                
                return dashboard_id
            
        except Exception as e:
            print(f"Error inserting/updating dashboard: {e}")
            return None
    
    def parse_dashboard_with_lib(self, dashboard_data: Dict[str, Any]) -> Tuple[Optional[GrafanaDashboard], List[str]]:
        """
        Parse dashboard using the new dashboard library for enhanced manipulation.
        
        Args:
            dashboard_data: Dashboard data from database
            
        Returns:
            Tuple of (GrafanaDashboard object, list of messages/warnings)
        """
        if not DASHBOARD_LIB_AVAILABLE:
            return None, ["Dashboard library not available"]
        
        try:
            # Extract the JSON data
            data = dashboard_data.get('data', {})
            if isinstance(data, str):
                json_str = data
            else:
                json_str = json.dumps(data)
            
            # Parse with the library
            dashboard_obj, messages = GrafanaDashboardParser.parse_dashboard(json_str)
            
            if dashboard_obj:
                # Set database metadata
                dashboard_obj.id = dashboard_data.get('id')
                if 'title' in dashboard_data:
                    dashboard_obj.title = dashboard_data['title']
                
                self.logger.info(f"Successfully parsed dashboard with library: {dashboard_obj.title}")
                self.logger.info(f"Dashboard has {len(dashboard_obj.panels)} panels and {len(dashboard_obj.templating)} variables")
                
                if messages:
                    self.logger.warning(f"Parsing warnings: {'; '.join(messages)}")
            else:
                self.logger.error(f"Failed to parse dashboard with library: {'; '.join(messages)}")
            
            return dashboard_obj, messages
            
        except Exception as e:
            error_msg = f"Error parsing dashboard with library: {str(e)}"
            self.logger.error(error_msg)
            return None, [error_msg]
    
    def format_dashboard_for_llm(self, dashboard: Dict[str, Any]) -> str:
        """Format dashboard data for LLM consumption"""
        try:
            data = dashboard['data']
            if isinstance(data, str):
                data = json.loads(data)
            
            # Extract key dashboard information
            formatted = f"Dashboard: {dashboard['title']}\n"
            formatted += f"Slug: {dashboard['slug']}\n"
            formatted += f"Created: {dashboard['created']}\n"
            formatted += f"Updated: {dashboard['updated']}\n\n"
            
            # Dashboard metadata
            if 'title' in data:
                formatted += f"Dashboard Title: {data['title']}\n"
            if 'description' in data:
                formatted += f"Description: {data['description']}\n"
            if 'tags' in data:
                formatted += f"Tags: {', '.join(data['tags'])}\n"
            
            # Time range
            if 'time' in data:
                formatted += f"Time Range: {data['time']['from']} to {data['time']['to']}\n"
            
            # Refresh settings
            if 'refresh' in data:
                formatted += f"Refresh: {data['refresh']}\n"
            
            formatted += "\nPanels:\n"
            
            # Panel information
            if 'panels' in data:
                for i, panel in enumerate(data['panels'], 1):
                    formatted += f"\nPanel {i}:\n"
                    formatted += f"  - Title: {panel.get('title', 'Untitled')}\n"
                    formatted += f"  - Type: {panel.get('type', 'unknown')}\n"
                    formatted += f"  - ID: {panel.get('id', 'N/A')}\n"
                    
                    if 'gridPos' in panel:
                        pos = panel['gridPos']
                        formatted += f"  - Position: x={pos.get('x', 0)}, y={pos.get('y', 0)}, w={pos.get('w', 0)}, h={pos.get('h', 0)}\n"
                    
                    if 'targets' in panel:
                        formatted += f"  - Queries: {len(panel['targets'])} query(ies)\n"
                        for j, target in enumerate(panel['targets'], 1):
                            if 'expr' in target:
                                formatted += f"    Query {j}: {target['expr'][:100]}...\n"
                    
                    if 'fieldConfig' in panel:
                        formatted += f"  - Field Config: {json.dumps(panel['fieldConfig'], indent=2)[:200]}...\n"
            
            # Variables/Templating
            if 'templating' in data and 'list' in data['templating']:
                formatted += f"\nVariables: {len(data['templating']['list'])} variable(s)\n"
                for var in data['templating']['list']:
                    formatted += f"  - {var.get('name', 'unnamed')}: {var.get('type', 'unknown')} ({var.get('query', 'no query')})\n"
            
            return formatted
            
        except Exception as e:
            return f"Error formatting dashboard: {e}\n\nRaw data: {json.dumps(dashboard, indent=2, default=str)[:1000]}..."
    
    def summarize_dashboard_with_groq(self, dashboard: Dict[str, Any]) -> str:
        """Use Groq API to summarize dashboard"""
        
        formatted_dashboard = self.format_dashboard_for_llm(dashboard)

        prompt, system_prompt = get_dashboard_analysis_prompt(formatted_dashboard)
        
        # Log the operation start
        metadata = {
            "dashboard_id": dashboard.get('id'),
            "dashboard_title": dashboard.get('title'),
            "operation_type": "analysis"
        }
        
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=2048
            )
            
            response_content = response.choices[0].message.content
            
            # Log the complete interaction
            self.log_prompt_and_response(
                operation="dashboard_analysis",
                prompt=f"SYSTEM: {system_prompt}\n\nUSER: {prompt}",
                response=response_content,
                metadata=metadata
            )
            
            return response_content
            
        except Exception as e:
            error_msg = f"Error calling Groq API: {e}"
            self.log_error("dashboard_analysis", error_msg, metadata)
            return error_msg
    
    def suggest_panel_modifications_with_groq(self, dashboard_obj: GrafanaDashboard, modification_request: str, table_information_str: str) -> List[Dict[str, Any]]:
        """
        Use Groq API to suggest panel modifications based on user request.
        Returns a list of panel operations to perform.
        
        Args:
            dashboard_obj: Parsed dashboard object
            modification_request: User's request for modifications
            table_information: Database table schema and sample data for context
            
        Returns:
            List of panel operations: [{"action": "add|remove|modify", "panel": {...}, "id": int}]
        """
        if not DASHBOARD_LIB_AVAILABLE or not dashboard_obj:
            return []
        
        # Format current dashboard panels for context
        panels_summary = []
        for panel in dashboard_obj.panels:
            panel_info = {
                "id": panel.id,
                "title": panel.title,
                "type": panel.type,
                "position": {"x": panel.grid_pos.x, "y": panel.grid_pos.y, "w": panel.grid_pos.w, "h": panel.grid_pos.h},
                "targets_count": len(panel.targets),
                "datasource": panel.datasource.type if panel.datasource else "none"
            }
            panels_summary.append(panel_info)
        
        prompt, system_prompt = get_dashboard_modification_suggestions_prompt(dashboard_obj, panels_summary, table_information_str, modification_request)
        
        metadata = {
            "dashboard_id": dashboard_obj.id,
            "dashboard_title": dashboard_obj.title,
            "operation_type": "panel_suggestions",
            "user_request": modification_request,
            "current_panels_count": len(dashboard_obj.panels)
        }
        
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                model=DASHBOARD_MODEL,
                temperature=0.1,
                max_tokens=4096
            )
            
            response_content = response.choices[0].message.content.strip()
            
            # Log the interaction
            self.log_prompt_and_response(
                operation="panel_suggestions",
                prompt=f"SYSTEM: {system_prompt}\n\nUSER: {prompt}",
                response=response_content,
                metadata=metadata
            )
            
            # Parse the JSON response
            parsed_operations, error_msg = self.extract_json_from_response(response_content)
            
            if parsed_operations and isinstance(parsed_operations, list):
                self.logger.info(f"Successfully extracted {len(parsed_operations)} panel operations")
                return parsed_operations
            else:
                self.logger.error(f"Failed to extract panel operations: {error_msg}")
                return []
                
        except Exception as e:
            error_msg = f"Error calling Groq API for panel suggestions: {e}"
            self.log_error("panel_suggestions", error_msg, metadata)
            return []
    
    def apply_panel_operations(self, dashboard_obj: GrafanaDashboard, operations: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Apply suggested panel operations to the dashboard object.
        
        Args:
            dashboard_obj: Dashboard object to modify
            operations: List of operations from suggest_panel_modifications_with_groq
            
        Returns:
            Tuple of (success, list of messages)
        """
        if not DASHBOARD_LIB_AVAILABLE or not dashboard_obj:
            return False, ["Dashboard library not available"]
        
        messages = []
        
        try:
            for operation in operations:
                action = operation.get("action", "").lower()
                reason = operation.get("reason", "No reason provided")
                
                if action == "add":
                    # Add new panel
                    panel_data = operation.get("panel", {})
                    try:
                        new_panel = Panel.from_dict(panel_data)
                        dashboard_obj.add_panel(new_panel)
                        messages.append(f"✅ Added panel '{new_panel.title}' (ID: {new_panel.id}) - {reason}")
                        self.logger.info(f"Added panel: {new_panel.title} (ID: {new_panel.id})")
                    except Exception as e:
                        messages.append(f"❌ Failed to add panel: {str(e)}")
                        self.logger.error(f"Failed to add panel: {str(e)}")
                
                elif action == "remove":
                    # Remove existing panel
                    panel_id = operation.get("panel_id")
                    if panel_id:
                        panel = dashboard_obj.get_panel_by_id(panel_id)
                        if panel:
                            if dashboard_obj.remove_panel(panel_id):
                                messages.append(f"✅ Removed panel '{panel.title}' (ID: {panel_id}) - {reason}")
                                self.logger.info(f"Removed panel: {panel.title} (ID: {panel_id})")
                            else:
                                messages.append(f"❌ Failed to remove panel ID {panel_id}")
                        else:
                            messages.append(f"❌ Panel ID {panel_id} not found")
                    else:
                        messages.append(f"❌ Remove operation missing panel_id")
                
                elif action == "modify":
                    # Modify existing panel
                    panel_id = operation.get("panel_id")
                    panel_data = operation.get("panel", {})
                    
                    if panel_id and panel_data:
                        existing_panel = dashboard_obj.get_panel_by_id(panel_id)
                        if existing_panel:
                            try:
                                # Update panel properties
                                for key, value in panel_data.items():
                                    if key == "gridPos" and isinstance(value, dict):
                                        existing_panel.grid_pos = GridPosition.from_dict(value)
                                    elif key == "targets" and isinstance(value, list):
                                        existing_panel.targets = [QueryTarget.from_dict(t) for t in value]
                                    elif key == "datasource" and isinstance(value, dict):
                                        existing_panel.datasource = DataSource.from_dict(value)
                                    elif hasattr(existing_panel, key):
                                        setattr(existing_panel, key, value)
                                
                                messages.append(f"✅ Modified panel '{existing_panel.title}' (ID: {panel_id}) - {reason}")
                                self.logger.info(f"Modified panel: {existing_panel.title} (ID: {panel_id})")
                            except Exception as e:
                                messages.append(f"❌ Failed to modify panel ID {panel_id}: {str(e)}")
                                self.logger.error(f"Failed to modify panel {panel_id}: {str(e)}")
                        else:
                            messages.append(f"❌ Panel ID {panel_id} not found for modification")
                    else:
                        messages.append(f"❌ Modify operation missing panel_id or panel data")
                
                else:
                    messages.append(f"❌ Unknown operation action: {action}")
            
            # Validate the dashboard after all operations
            is_valid, errors, warnings = self.dashboard_lib_manager.validate_dashboard(dashboard_obj)
            
            if not is_valid:
                messages.append(f"⚠️  Dashboard validation issues: {'; '.join(errors)}")
                # Auto-fix common issues
                dashboard_obj.auto_layout(columns=2)
                messages.append("🔧 Applied auto-layout to fix positioning issues")
            
            if warnings:
                messages.append(f"⚠️  Warnings: {'; '.join(warnings)}")
            
            return True, messages
            
        except Exception as e:
            error_msg = f"Error applying panel operations: {str(e)}"
            self.logger.error(error_msg)
            return False, [error_msg]
    
    def use_llm_to_get_table_list(self, modification_request: str, dashboard: Dict[str, Any]) -> List[str]:
        """Use LLM to analyze dashboard and modification request to determine relevant database tables"""
        
        # Get dashboard panels and their queries
        dashboard_data = dashboard.get('data', {})

        if type(dashboard_data) == str:
            dashboard_data = json.loads(dashboard_data)

        panels = dashboard_data.get('panels', [])
        
        # Extract queries from panels
        panel_queries = []
        for panel in panels:
            if 'targets' in panel:
                for target in panel['targets']:
                    if target.get('rawSql') or target.get('expr'):
                        query = target.get('rawSql', target.get('expr', ''))
                        if query:
                            panel_queries.append(query)

        prompt = get_table_list_prompt(dashboard, panel_queries, modification_request)
        
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a database expert specializing in analyzing dashboard requirements. Return only a comma-separated list of table names."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=TABLEDATA_MODEL,
                temperature=0.1,
                max_tokens=500
            )
            
            response_content = response.choices[0].message.content.strip()
            
            # Parse the response to extract table names
            table_names = [name.strip() for name in response_content.split(',') if name.strip()]
            
            self.logger.info(f"LLM suggested tables: {table_names}")
            return table_names
            
        except Exception as e:
            self.logger.error(f"Error getting table list from LLM: {e}")
            return []

    def get_table_ddl_only_for_dashboard(self, db_summarizer: 'db_explorer.DatabaseSummarizer', 
                                          table_list: List[str]) -> List[str]:
        table_ddls = []
        for table_name in table_list:
            schema = db_summarizer.get_table_schema(table_name)
            if schema:
                # Create a simple multiline string from columns
                ddl_lines = [f"Table: {table_name}"]
                ddl_lines.append("-" * (len(table_name) + 7))  # Underline
                for column_name, data_type in schema:
                    ddl_lines.append(f"  {column_name}: {data_type}")
                ddl_lines.append("")  # Empty line between tables
                table_ddls.append("\n".join(ddl_lines))
            else:
                table_ddls.append(f"Table: {table_name}\nError: Could not retrieve schema")
        return table_ddls
    
    def DEPRECATED_get_table_information_for_dashboard(self, db_summarizer: 'db_explorer.DatabaseSummarizer', 
                                          table_list: List[str], modification_request: str) -> Dict[str, Any]:
        """Get detailed table schema information and sample data for dashboard modification"""
        
        table_information = {
            'tables': {},
            'summary': '',
            'recommendations': []
        }
        
        print(f"\n📊 Analyzing {len(table_list)} potentially relevant tables...")
        
        # Get available tables from database
        available_tables = db_summarizer.get_table_list()
        
        # Filter table_list to only include tables that actually exist
        existing_tables = [table for table in table_list if table in available_tables]
        
        if not existing_tables:
            print("⚠️  No matching tables found in database")
            self.logger.warning(f"No tables from LLM suggestions found in database. Suggested: {table_list}, Available: {available_tables[:10]}...")
            table_information['summary'] = "No relevant tables found in the database for the requested modification."
            return table_information
        
        print(f"✅ Found {len(existing_tables)} existing tables: {existing_tables}")
        
        # Get detailed information for each table
        for table_name in existing_tables:
            try:
                print(f"  🔍 Getting schema for table: {table_name}")
                
                # Get table schema
                schema = db_summarizer.get_table_schema(table_name)
                
                # Get sample data
                sample_data = db_summarizer.get_table_sample(table_name, limit=5)
                
                # Store table information with schema and sample data only
                table_information['tables'][table_name] = {
                    'schema': schema,
                    'sample_data': sample_data,
                    'columns': [col[0] for col in schema] if schema else [],
                    'column_info': [{'name': col[0], 'type': col[1], 'max_length': col[2]} for col in schema] if schema else []
                }
                
            except Exception as e:
                self.logger.error(f"Error analyzing table {table_name}: {e}")
                table_information['tables'][table_name] = {
                    'error': str(e),
                    'schema': None,
                    'sample_data': None,
                    'columns': [],
                    'column_info': []
                }
        
        # Generate overall summary with modification context
        overall_summary = self.DEPRECATED_generate_table_analysis_summary(table_information, modification_request)
        table_information['summary'] = overall_summary
        
        return table_information
    
    def DEPRECATED_generate_table_analysis_summary(self, table_info: Dict[str, Any], modification_request: str) -> str:
        """Generate an overall summary of table analysis for dashboard modification using schema context"""
        
        # Compile table schema information
        table_schemas = []
        for table_name, info in table_info['tables'].items():
            if 'error' not in info and info.get('column_info'):
                schema_text = f"Table '{table_name}':\n"
                schema_text += f"  Columns: {len(info['column_info'])}\n"
                for col in info['column_info']:
                    schema_text += f"    - {col['name']} ({col['type']})\n"
                table_schemas.append(schema_text)
        
        if not table_schemas:
            return "No table schema information available for analysis."
        
        # Create comprehensive prompt for overall analysis using schema context
        prompt = f"""Based on the following database table schemas, provide recommendations for modifying a Grafana dashboard.

        User's Modification Request:
        {modification_request}

        Available Database Tables and Schemas:
        {chr(10).join(table_schemas)}

        Provide practical recommendations:
        1. Which tables are most relevant for the requested modification
        2. Specific column recommendations for dashboard metrics and filters
        3. Suggested SQL query patterns based on available columns
        4. Recommended panel types based on data types
        5. Performance considerations for large tables

        Focus on actionable dashboard implementation guidance."""

        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Grafana dashboard expert analyzing database schemas for dashboard modifications. Provide practical, actionable recommendations based on table structures and column types."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=TABLEDATA_MODEL,
                temperature=0.3,
                max_tokens=1024
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating table analysis summary: {e}")
            return f"Error generating analysis summary: {str(e)}"
    
    def DEPRECATED_modify_dashboard_with_groq(self, dashboard: Dict[str, Any], modification_request: str) -> Optional[Dict[str, Any]]:
        """Use Groq API to modify dashboard based on user request"""
        
        formatted_dashboard = self.format_dashboard_for_llm(dashboard)
        
        prompt = f"""You are a Grafana dashboard expert. Modify the following dashboard JSON based on the user's request.

        Current Dashboard Configuration:
        {formatted_dashboard}

        Original Dashboard JSON:
        {json.dumps(dashboard['data'], indent=2)}

        User's Modification Request:
        {modification_request}

        Please provide the modified dashboard JSON configuration. Ensure that:
        1. The JSON is valid and follows Grafana dashboard schema
        2. All existing functionality is preserved unless specifically requested to change
        3. New features are properly integrated
        4. Panel IDs are unique
        5. Grid positions don't overlap

        Respond with ONLY the modified JSON configuration, no additional text or explanation."""
        
        system_prompt = "You are a Grafana dashboard expert. You modify dashboard JSON configurations based on user requests. Always respond with valid JSON only."
        
        # Log the operation start
        metadata = {
            "dashboard_id": dashboard.get('id'),
            "dashboard_title": dashboard.get('title'),
            "operation_type": "modification",
            "user_request": modification_request
        }
        
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=DASHBOARD_MODEL,
                temperature=0.1,
                max_tokens=4096
            )
            
            # Extract and parse JSON using robust extraction method
            response_content = response.choices[0].message.content.strip()
            
            # Log the complete interaction
            self.log_prompt_and_response(
                operation="dashboard_modification",
                prompt=f"SYSTEM: {system_prompt}\n\nUSER: {prompt}",
                response=response_content,
                metadata=metadata
            )
            
            print("🔍 Extracting JSON from LLM response...")
            modified_data, error_message = self.extract_json_from_response(response_content)
            
            if modified_data is not None:
                if error_message:
                    print(f"⚠️  {error_message}")
                    # Log the warning
                    warning_metadata = {**metadata, "extraction_warning": error_message}
                    self.logger.warning(f"JSON extraction warning: {error_message}")
                else:
                    print("✅ Successfully parsed JSON response")
                
                # Validate and fix the dashboard JSON structure
                print("🔧 Validating and fixing dashboard structure...")
                try:
                    validated_data = self.validate_and_fix_dashboard_json(modified_data)
                    print("✅ Dashboard structure validated and fixed")
                    
                    # Log successful modification
                    success_metadata = {
                        **metadata,
                        "modification_successful": True,
                        "panels_count": len(validated_data.get('panels', [])),
                        "extraction_method": "successful" if not error_message else "with_warnings"
                    }
                    self.logger.info(f"Dashboard modification completed successfully: {json.dumps(success_metadata, indent=2)}")
                    
                    return validated_data
                except Exception as validation_error:
                    print(f"⚠️  Warning: Dashboard validation failed: {validation_error}")
                    print("📤 Returning unvalidated dashboard data")
                    
                    # Log validation warning
                    self.log_error("dashboard_validation", str(validation_error), {**metadata, "validation_failed": True})
                    
                    return modified_data
            else:
                print(f"❌ JSON extraction failed: {error_message}")
                print(f"📄 First 500 chars of response: {response_content[:500]}...")
                
                # Log the extraction failure
                failure_metadata = {
                    **metadata,
                    "extraction_failed": True,
                    "error_message": error_message,
                    "response_length": len(response_content)
                }
                self.log_error("json_extraction", error_message, failure_metadata)
                
                # Save full response for debugging
                debug_filename = f"debug_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                try:
                    with open(debug_filename, 'w') as f:
                        f.write("=== FULL LLM RESPONSE ===\n")
                        f.write(response_content)
                        f.write("\n\n=== ERROR MESSAGE ===\n")
                        f.write(error_message)
                    print(f"💾 Full response saved to {debug_filename} for debugging")
                    self.logger.info(f"Debug file saved: {debug_filename}")
                except Exception as save_error:
                    print(f"Could not save debug file: {save_error}")
                    self.logger.error(f"Failed to save debug file: {save_error}")
                
                return None
            
        except Exception as e:
            error_msg = f"Error calling Groq API: {e}"
            print(error_msg)
            self.log_error("groq_api_call", error_msg, metadata)
            return None
    
    def extract_json_from_response(self, response_text: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Extract and parse JSON from LLM response, handling various formatting issues.
        
        Args:
            response_text: Raw response text from LLM
            
        Returns:
            Tuple of (parsed_json_dict, error_message)
            If successful: (dict, "")
            If failed: (None, error_description)
        """

        # remove the <think> and </think> tags and all data between them
        # response_text = re.sub(r'<think>.*?</think>', '', response_text)
        response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL)

        if not response_text or not response_text.strip():
            return None, "Empty response text"
        
        original_text = response_text.strip()
        
        # Strategy 1: Try direct parsing (cleanest case)
        try:
            # print(f"Trying to parse JSON: {original_text}")
            parsed = json.loads(original_text)
            # print(f"Successfully parsed JSON: {parsed}")
            return parsed, ""
        except json.JSONDecodeError:
            print(f"Failed to parse JSON: {original_text}")
            pass
        
        # Strategy 2: Remove common code block markers
        cleaned_text = original_text
        
        # Remove markdown code blocks
        if cleaned_text.startswith('```json'):
            cleaned_text = cleaned_text[7:]
        elif cleaned_text.startswith('```'):
            cleaned_text = cleaned_text[3:]
        
        if cleaned_text.endswith('```'):
            cleaned_text = cleaned_text[:-3]
        
        cleaned_text = cleaned_text.strip()
        
        try:
            parsed = json.loads(cleaned_text)
            return parsed, ""
        except json.JSONDecodeError:
            pass
        
        # Strategy 3: Find JSON using regex patterns
        json_patterns = [
            # Look for content between outermost braces
            r'\{.*\}',
            # Look for content between square brackets (for arrays)
            r'\[.*\]',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, original_text, re.DOTALL)
            for match in matches:
                try:
                    # Try to find the most complete JSON object
                    brace_count = 0
                    start_idx = -1
                    
                    for i, char in enumerate(match):
                        if char == '{':
                            if start_idx == -1:
                                start_idx = i
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0 and start_idx != -1:
                                candidate = match[start_idx:i+1]
                                try:
                                    parsed = json.loads(candidate)
                                    return parsed, ""
                                except json.JSONDecodeError:
                                    continue
                    
                    # If brace counting didn't work, try the whole match
                    parsed = json.loads(match)
                    return parsed, ""
                except json.JSONDecodeError:
                    continue
        
        # Strategy 4: Try to extract JSON from lines
        lines = original_text.split('\n')
        json_lines = []
        in_json = False
        brace_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip obvious non-JSON lines
            if line.startswith('#') or line.startswith('//') or line.startswith('Here') or line.startswith('The'):
                continue
            
            # Check if line contains JSON-like content
            if '{' in line or '[' in line or in_json:
                json_lines.append(line)
                in_json = True
                
                # Count braces to determine when JSON ends
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0 and in_json:
                    break
        
        if json_lines:
            candidate = '\n'.join(json_lines)
            try:
                parsed = json.loads(candidate)
                return parsed, ""
            except json.JSONDecodeError:
                pass
        
        # Strategy 5: Try to fix common JSON issues
        fixes_to_try = [
            # Remove trailing commas
            lambda x: re.sub(r',(\s*[}\]])', r'\1', x),
            # Fix single quotes to double quotes
            lambda x: re.sub(r"'([^']*)':", r'"\1":', x),
            # Remove comments
            lambda x: re.sub(r'//.*', '', x),
            # Remove multiple spaces
            lambda x: re.sub(r'\s+', ' ', x),
        ]
        
        for fix_func in fixes_to_try:
            try:
                fixed_text = fix_func(cleaned_text)
                parsed = json.loads(fixed_text)
                return parsed, ""
            except json.JSONDecodeError:
                continue
        
        # Strategy 6: Last resort - try to extract key-value pairs manually
        try:
            # Look for something that resembles a dashboard structure
            dashboard_match = re.search(r'"title":\s*"([^"]*)"', original_text)
            if dashboard_match:
                # Try to build a minimal valid JSON structure
                title = dashboard_match.group(1)
                minimal_dashboard = {
                    "title": title,
                    "panels": [],
                    "time": {"from": "now-1h", "to": "now"},
                    "refresh": "5s",
                    "tags": [],
                    "templating": {"list": []},
                    "annotations": {"list": []},
                    "schemaVersion": 1,
                    "version": 1
                }
                return minimal_dashboard, "Warning: Generated minimal dashboard structure due to JSON parsing issues"
        except Exception:
            pass
        
        # Complete failure
        error_msg = f"Failed to extract valid JSON from response. Response length: {len(original_text)} chars"
        return None, error_msg
    
    def validate_and_fix_dashboard_json(self, dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and fix common issues in dashboard JSON structure.
        
        Args:
            dashboard_data: Raw dashboard JSON data
            
        Returns:
            Fixed dashboard JSON data
        """
        # Ensure required top-level fields exist
        required_fields = {
            "title": "Untitled Dashboard",
            "panels": [],
            "time": {"from": "now-1h", "to": "now"},
            "refresh": "5s",
            "tags": [],
            "templating": {"list": []},
            "annotations": {"list": []},
            "schemaVersion": 1,
            "version": 1,
            "timezone": "browser",
            "editable": True,
            "gnetId": None,
            "graphTooltip": 0,
            "id": None,
            "links": [],
            "liveNow": False
        }
        
        # Add missing required fields
        for field, default_value in required_fields.items():
            if field not in dashboard_data:
                dashboard_data[field] = default_value
        
        # Fix panels if they exist
        if "panels" in dashboard_data and isinstance(dashboard_data["panels"], list):
            used_ids = set()
            for i, panel in enumerate(dashboard_data["panels"]):
                if not isinstance(panel, dict):
                    continue
                
                # Ensure panel has required fields
                panel_defaults = {
                    "id": i + 1,
                    "title": f"Panel {i + 1}",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                    "targets": [],
                    "fieldConfig": {"defaults": {}, "overrides": []},
                    "options": {}
                }
                
                for field, default_value in panel_defaults.items():
                    if field not in panel:
                        panel[field] = default_value
                
                # Ensure unique panel IDs
                original_id = panel["id"]
                if original_id in used_ids or not isinstance(original_id, int):
                    panel["id"] = i + 1
                    while panel["id"] in used_ids:
                        panel["id"] += 1
                
                used_ids.add(panel["id"])
        
        # Validate time range
        if "time" in dashboard_data and isinstance(dashboard_data["time"], dict):
            time_defaults = {"from": "now-1h", "to": "now"}
            for field, default_value in time_defaults.items():
                if field not in dashboard_data["time"]:
                    dashboard_data["time"][field] = default_value
        
        # Validate templating structure
        if "templating" in dashboard_data:
            if not isinstance(dashboard_data["templating"], dict):
                dashboard_data["templating"] = {"list": []}
            elif "list" not in dashboard_data["templating"]:
                dashboard_data["templating"]["list"] = []
        
        # Validate annotations structure
        if "annotations" in dashboard_data:
            if not isinstance(dashboard_data["annotations"], dict):
                dashboard_data["annotations"] = {"list": []}
            elif "list" not in dashboard_data["annotations"]:
                dashboard_data["annotations"]["list"] = []
        
        return dashboard_data
    
    def create_slug_from_title(self, title: str) -> str:
        """Create a URL-friendly slug from dashboard title"""
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = slug.strip('-')
        return slug
    
    def modify_dashboard_enhanced(self, dashboard_data: Dict[str, Any], modification_request: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        """
        Enhanced dashboard modification using the new library with panel-based operations.
        
        Args:
            dashboard_data: Dashboard data from database
            modification_request: User's modification request
            
        Returns:
            Tuple of (modified_dashboard_dict, list_of_messages)
        """
        if not DASHBOARD_LIB_AVAILABLE:
            return None, ["Dashboard library not available"]
        
        messages = []
        
        try:
            # Parse dashboard with library
            dashboard_obj, parse_messages = self.parse_dashboard_with_lib(dashboard_data)
            messages.extend(parse_messages)
            
            if not dashboard_obj:
                return None, messages + ["Failed to parse dashboard"]
            
            # Get panel modification suggestions from LLM
            operations = self.suggest_panel_modifications_with_groq(dashboard_obj, modification_request)
            
            if not operations:
                return None, messages + ["No panel operations suggested by LLM"]
            
            # Apply the operations
            success, operation_messages = self.apply_panel_operations(dashboard_obj, operations)
            messages.extend(operation_messages)
            
            if not success:
                return None, messages + ["Failed to apply panel operations"]
            
            # Return the modified dashboard as dictionary
            modified_data = dashboard_obj.to_dict()
            
            # Add summary message
            summary = f"Successfully modified dashboard: {len(operations)} operations applied, {len(dashboard_obj.panels)} total panels"
            messages.insert(0, summary)
            
            return modified_data, messages
            
        except Exception as e:
            error_msg = f"Error in enhanced dashboard modification: {str(e)}"
            self.logger.error(error_msg)
            return None, messages + [error_msg]
    
    def run_dashboard_workflow(self):
        """Main workflow for dashboard management"""
        print("🎯 Grafana Dashboard Manager")
        print("=" * 60)
        
        # Log workflow start
        self.logger.info("=" * 60)
        self.logger.info("DASHBOARD WORKFLOW STARTED")
        self.logger.info("=" * 60)
        
        # Step 1: Get and display dashboard list
        self.logger.info("Step 1: Fetching dashboard list from database")
        dashboards = self.get_dashboard_list()
        
        if not dashboards:
            print("No dashboards found or connection failed")
            self.logger.error("No dashboards found or database connection failed")
            return
        
        self.logger.info(f"Found {len(dashboards)} dashboards in database")
        
        print(f"\n📊 Found {len(dashboards)} dashboards:")
        print("-" * 60)
        for i, dashboard in enumerate(dashboards, 1):
            print(f"{i:2d}. {dashboard['title']}")
            print(f"    Slug: {dashboard['slug']}")
            print(f"    Updated: {dashboard['updated']}")
            print()
        
        # Step 2: Dashboard selection
        try:
            choice = int(input(f"Select a dashboard (1-{len(dashboards)}): "))
            if not (1 <= choice <= len(dashboards)):
                print("Invalid selection")
                return
            
            selected_dashboard = dashboards[choice - 1]
            print(f"\n✅ Selected: {selected_dashboard['title']}")
            
            # Log dashboard selection
            self.logger.info(f"Step 2: User selected dashboard - ID: {selected_dashboard['id']}, Title: {selected_dashboard['title']}")
            
        except ValueError:
            print("Invalid input. Please enter a number.")
            self.logger.error("Invalid dashboard selection - user entered non-numeric input")
            return

        
        # Step 3: Analyze and summarize dashboard
        if "analysis" in sys.argv:
            print("\n🔍 Analyzing dashboard...")
            print("=" * 60)
            self.logger.info("Step 3: Starting dashboard analysis with AI")
            summary = self.summarize_dashboard_with_groq(selected_dashboard)
            print(summary)
        
        # Step 4: Get modification request
        print("\n" + "=" * 60)
        print("📝 Dashboard Modification")
        print("=" * 60)
        
        modification_request = input("\nDescribe the changes you want to make to this dashboard: ")
        if not modification_request.strip():
            print("No modifications requested. Exiting.")
            self.logger.info("Step 4: User cancelled - no modification request provided")
            return
        
        new_dashboard_name = input("Enter a name for the new dashboard: ")
        if not new_dashboard_name.strip():
            new_dashboard_name = f"{selected_dashboard['title']} - Modified"
        
        # Log user inputs
        self.logger.info("Step 4: User provided modification request")
        self.logger.info(f"Modification request: {modification_request}")
        self.logger.info(f"New dashboard name: {new_dashboard_name}")

        print("Using LLM to get a list of all possible table information from the database, include user prompt and all panels")
        print(selected_dashboard)
        # Use LLM to get a list of all possible table information from the database, include user prompt and all panels

        table_list = self.use_llm_to_get_table_list(modification_request, selected_dashboard)

        print("Table list:")
        print(table_list)

        # Initialize database explorer to get detailed table information
        db_summarizer = db_explorer.DatabaseSummarizer()
        table_information_str = self.get_table_ddl_only_for_dashboard(db_summarizer, table_list)
        
        self.logger.info("Step 5: Starting AI-powered panel-based dashboard modification")
        
        # Try to use the enhanced library approach first
        if DASHBOARD_LIB_AVAILABLE:
            print("🔧 Using enhanced dashboard library for modifications...")
            
            # Parse dashboard with library
            dashboard_obj, parse_messages = self.parse_dashboard_with_lib(selected_dashboard)
            
            if dashboard_obj:
                print(f"✅ Successfully parsed dashboard: {dashboard_obj.title}")
                if parse_messages:
                    print(f"   Parsing notes: {'; '.join(parse_messages)}")
                
                # Get panel modification suggestions from LLM
                print("🤖 Analyzing modification request and suggesting panel changes...")
                operations = self.suggest_panel_modifications_with_groq(dashboard_obj, modification_request, table_information_str)
                
                if operations:
                    print(f"📋 LLM suggested {len(operations)} panel operations:")
                    for i, op in enumerate(operations, 1):
                        action = op.get("action", "unknown")
                        reason = op.get("reason", "No reason")
                        if action == "add":
                            panel_title = op.get("panel", {}).get("title", "Unknown")
                            print(f"   {i}. ADD: {panel_title} - {reason}")
                        elif action == "remove":
                            panel_id = op.get("panel_id", "?")
                            print(f"   {i}. REMOVE: Panel ID {panel_id} - {reason}")
                        elif action == "modify":
                            panel_id = op.get("panel_id", "?")
                            print(f"   {i}. MODIFY: Panel ID {panel_id} - {reason}")
                    
                    # Apply the operations
                    print("\n🔧 Applying panel modifications...")
                    success, operation_messages = self.apply_panel_operations(dashboard_obj, operations)
                    
                    if success:
                        print("✅ Panel operations completed successfully!")
                        for msg in operation_messages:
                            print(f"   {msg}")
                        
                        # Convert back to dictionary format for database storage
                        modified_data = dashboard_obj.to_dict()
                        
                        print(f"📊 Final dashboard: {len(dashboard_obj.panels)} panels, {len(dashboard_obj.templating)} variables")
                        
                    else:
                        print("❌ Failed to apply panel operations:")
                        for msg in operation_messages:
                            print(f"   {msg}")
                        print("🔄 [DEPRECATED] Falling back to legacy modification approach...")
                        # modified_data = self.DEPRECATED_modify_dashboard_with_groq(selected_dashboard, modification_request)
                else:
                    print("❌ No panel operations suggested by LLM")
                    print("🔄 [DEPRECATED] Falling back to legacy modification approach...")
                    # modified_data = self.DEPRECATED_modify_dashboard_with_groq(selected_dashboard, modification_request)
            else:
                print("❌ Failed to parse dashboard with library:")
                for msg in parse_messages:
                    print(f"   {msg}")
                print("🔄 [DEPRECATED] Falling back to legacy modification approach...")
                # modified_data = self.DEPRECATED_modify_dashboard_with_groq(selected_dashboard, modification_request)
        else:
            print("⚠️ [DEPRECATED] Dashboard library not available, using legacy approach...")
            # modified_data = self.DEPRECATED_modify_dashboard_with_groq(selected_dashboard, modification_request)
        
        if not modified_data:
            print("❌ Failed to modify dashboard. Please try again.")
            self.logger.error("Step 5: Dashboard modification failed")
            return
        
        # Step 6: Insert new dashboard
        new_slug = self.create_slug_from_title(new_dashboard_name)

        # generate random uid
        uid = str(uuid.uuid4())

        # Update dashboard title in dashboard json
        modified_data['title'] = new_dashboard_name

        # Update uid in dashboard json
        modified_data['uid'] = uid
        
        print(f"\n💾 Saving new dashboard: '{new_dashboard_name}'")
        self.logger.info("Step 6: Saving modified dashboard to database")
        self.logger.info(f"New dashboard name: {new_dashboard_name}")
        self.logger.info(f"New dashboard slug: {new_slug}")

        # Get uid from modified_data
        uid = modified_data.get('uid')
        if not uid:
            print("❌ No uid found in modified data")
            return
        
        new_dashboard_id = self.insert_dashboard(new_dashboard_name, new_slug, modified_data, uid)
        
        if new_dashboard_id:
            print(f"✅ Successfully created new dashboard with ID: {new_dashboard_id}")
            print(f"   Title: {new_dashboard_name}")
            print(f"   Slug: {new_slug}")
            
            # Log successful completion with enhanced metadata
            completion_metadata = {
                "original_dashboard_id": selected_dashboard['id'],
                "original_dashboard_title": selected_dashboard['title'],
                "new_dashboard_id": new_dashboard_id,
                "new_dashboard_title": new_dashboard_name,
                "new_dashboard_slug": new_slug,
                "modification_request": modification_request,
                "modification_method": "enhanced_panel_based" if DASHBOARD_LIB_AVAILABLE else "legacy",
                "dashboard_library_available": DASHBOARD_LIB_AVAILABLE
            }
            
            # Add panel count information if available
            if isinstance(modified_data, dict) and 'panels' in modified_data:
                completion_metadata["final_panels_count"] = len(modified_data['panels'])
                completion_metadata["final_variables_count"] = len(modified_data.get('templating', {}).get('list', []))
            self.logger.info("WORKFLOW COMPLETED SUCCESSFULLY")
            self.logger.info(f"Final result: {json.dumps(completion_metadata, indent=2)}")
        else:
            print("❌ Failed to save new dashboard to database")
            self.logger.error("Step 6: Failed to save dashboard to database")
        
        print("\n🎉 Dashboard workflow completed!")
        self.logger.info("=" * 60)
        self.logger.info("DASHBOARD WORKFLOW ENDED")
        self.logger.info("=" * 60)

def main():
    """Main function to run the Grafana Dashboard Manager"""

    if len(sys.argv) > 1 and sys.argv[1] == "--test-parse-dashboard":
        manager = GrafanaDashboardManager()
        selected_dashboard_id = sys.argv[2]
        selected_dashboard = manager.get_dashboard_by_id(selected_dashboard_id)
        # print(json.dumps(json.loads(selected_dashboard['data']), indent=2, cls=DateTimeEncoder))
        dashboard_obj, parse_messages = manager.parse_dashboard_with_lib(selected_dashboard)
        print()
        print(dashboard_obj.get_variables_formatted('summary'))

        return

    if len(sys.argv) > 1 and sys.argv[1] == "--test-table-information":
        manager = GrafanaDashboardManager()
        db_summarizer = db_explorer.DatabaseSummarizer()

        table_ddls = manager.get_table_ddl_only_for_dashboard(db_summarizer, [''], "")
        
        print(json.dumps(table_ddls, indent=2, cls=DateTimeEncoder))
        return
    
    # Check for test flag
    if len(sys.argv) > 1 and sys.argv[1] == "--test-json":
        # test_json_extraction()
        return
    
    try:
        manager = GrafanaDashboardManager()
        manager.run_dashboard_workflow()
    except Exception as e:
        traceback.print_exc()
        print(f"Error initializing Grafana Dashboard Manager: {e}")


if __name__ == "__main__":
    main()
