"""
Prompt templates for database analysis using LLM models.
Organized by use case and analysis type for easy management and extension.
"""

from typing import Dict, Any, Optional


class PromptManager:
    """Manages prompt templates for different analysis types and use cases."""
    
    def __init__(self):
        """Initialize the prompt manager with predefined templates."""
        self.prompts = self._initialize_prompts()
    
    def _initialize_prompts(self) -> Dict[str, Dict[str, Any]]:
        """Initialize all prompt templates organized by category and type."""
        return {
            # Data Analysis Prompts
            "data_analysis": {
                "general": {
                    "template": """Analyze the following database data and provide a concise summary:

{data_text}

Please provide:
1. Overview of the data structure
2. Key patterns or insights
3. Data quality observations
4. Any notable trends or anomalies""",
                    "description": "General overview analysis of database data",
                    "use_case": "General data exploration and understanding"
                },
                
                "statistical": {
                    "template": """Analyze the following database data from a statistical perspective:

{data_text}

Provide statistical insights including:
1. Data distributions and patterns
2. Statistical measures (mean, median, mode, etc.)
3. Outliers and anomalies
4. Correlation insights
5. Data variance and spread""",
                    "description": "Statistical analysis focused on numerical insights",
                    "use_case": "Statistical modeling and data science analysis"
                },
                
                "business": {
                    "template": """Analyze the following database data from a business perspective:

{data_text}

What business insights can you derive? Please include:
1. Key business metrics and KPIs
2. Performance indicators
3. Growth opportunities
4. Risk factors
5. Strategic recommendations""",
                    "description": "Business-focused analysis for strategic insights",
                    "use_case": "Business intelligence and strategic planning"
                },
                
                "quality": {
                    "template": """Evaluate the following database data for quality issues:

{data_text}

Please assess:
1. Data completeness (missing values, null entries)
2. Data consistency (format variations, duplicates)
3. Data accuracy (logical errors, invalid values)
4. Data integrity (referential integrity, constraints)
5. Recommendations for data cleaning""",
                    "description": "Data quality assessment and validation",
                    "use_case": "Data governance and quality improvement"
                }
            },
            
            # Schema Analysis Prompts
            "schema_analysis": {
                "structure": {
                    "template": """Analyze the following database schema structure:

{schema_text}

Please provide:
1. Schema design assessment
2. Table relationships and dependencies
3. Normalization level analysis
4. Potential design improvements
5. Performance considerations""",
                    "description": "Database schema structure analysis",
                    "use_case": "Database design and architecture review"
                },
                
                "optimization": {
                    "template": """Review the following database schema for optimization opportunities:

{schema_text}

Focus on:
1. Index recommendations
2. Query performance improvements
3. Storage optimization
4. Partitioning strategies
5. Maintenance considerations""",
                    "description": "Performance optimization recommendations",
                    "use_case": "Database performance tuning"
                }
            },
            
            # Security Analysis Prompts
            "security_analysis": {
                "assessment": {
                    "template": """Analyze the following database structure for security considerations:

{data_text}

Please evaluate:
1. Sensitive data identification
2. Access control requirements
3. Encryption needs
4. Compliance considerations (GDPR, HIPAA, etc.)
5. Security recommendations""",
                    "description": "Security assessment of database content",
                    "use_case": "Security audit and compliance review"
                }
            },
            
            # Custom Query Analysis
            "query_analysis": {
                "performance": {
                    "template": """Analyze the following SQL query for performance:

{query_text}

Results:
{data_text}

Please provide:
1. Query execution analysis
2. Performance bottlenecks
3. Optimization suggestions
4. Index recommendations
5. Alternative query approaches""",
                    "description": "SQL query performance analysis",
                    "use_case": "Query optimization and tuning"
                },
                
                "results": {
                    "template": """Analyze the results of the following SQL query:

Query: {query_text}

Results:
{data_text}

Please provide:
1. Result set analysis
2. Data insights from the query
3. Patterns in the results
4. Business implications
5. Follow-up query suggestions""",
                    "description": "Analysis of query results and insights",
                    "use_case": "Ad-hoc query analysis and exploration"
                }
            },
            
            # Grafana Dashboard Analysis
            "grafana_analysis": {
                "summary": {
                    "template": """Analyze the following Grafana dashboard configuration and provide a comprehensive summary:

{dashboard_data}

Please provide:
1. **Dashboard Overview**: Purpose and main functionality
2. **Panel Analysis**: Types of visualizations and their purposes
3. **Data Sources**: What metrics or data are being monitored
4. **Layout and Organization**: How the dashboard is structured
5. **Key Insights**: What business/technical insights this dashboard provides
6. **Recommendations**: Potential improvements or optimizations

Format your response in clear sections with bullet points where appropriate.""",
                    "description": "Comprehensive Grafana dashboard analysis and summary",
                    "use_case": "Dashboard review and optimization"
                },
                
                "modification": {
                    "template": """You are a Grafana dashboard expert. Modify the following dashboard JSON based on the user's request.

Current Dashboard Configuration:
{dashboard_summary}

Original Dashboard JSON:
{dashboard_json}

User's Modification Request:
{modification_request}

Please provide the modified dashboard JSON configuration. Ensure that:
1. The JSON is valid and follows Grafana dashboard schema
2. All existing functionality is preserved unless specifically requested to change
3. New features are properly integrated
4. Panel IDs are unique
5. Grid positions don't overlap

Respond with ONLY the modified JSON configuration, no additional text or explanation.""",
                    "description": "AI-powered dashboard modification based on user requirements",
                    "use_case": "Dashboard customization and enhancement"
                },
                
                "best_practices": {
                    "template": """Review the following Grafana dashboard for best practices and optimization:

{dashboard_data}

Please evaluate:
1. **Performance**: Panel efficiency and query optimization
2. **User Experience**: Layout, colors, and navigation
3. **Monitoring Strategy**: Metric selection and alerting setup
4. **Accessibility**: Dashboard usability and clarity
5. **Maintenance**: Template variables and reusability
6. **Security**: Data exposure and access controls

Provide specific recommendations for each area.""",
                    "description": "Dashboard best practices review and recommendations",
                    "use_case": "Dashboard governance and optimization"
                },
                
                "troubleshooting": {
                    "template": """Help troubleshoot issues with the following Grafana dashboard:

Dashboard Configuration:
{dashboard_data}

Reported Issue:
{issue_description}

Please provide:
1. **Problem Analysis**: Likely causes of the issue
2. **Diagnostic Steps**: How to investigate further
3. **Solutions**: Step-by-step fixes
4. **Prevention**: How to avoid similar issues
5. **Testing**: How to verify the fix works

Focus on practical, actionable solutions.""",
                    "description": "Dashboard troubleshooting and issue resolution",
                    "use_case": "Dashboard maintenance and debugging"
                }
            },
            
            # Grafana Panel Analysis
            "grafana_panels": {
                "optimization": {
                    "template": """Analyze the following Grafana panel configuration for optimization:

Panel Configuration:
{panel_data}

Please provide:
1. **Query Optimization**: Improve data source queries
2. **Visualization**: Better chart types and settings
3. **Performance**: Reduce loading time and resource usage
4. **Clarity**: Improve readability and understanding
5. **Alerting**: Suggest threshold and alert configurations

Include specific configuration changes where possible.""",
                    "description": "Individual panel optimization and improvement",
                    "use_case": "Panel-level performance and clarity improvements"
                },
                
                "comparison": {
                    "template": """Compare the following Grafana panels and provide insights:

Panel 1:
{panel1_data}

Panel 2:
{panel2_data}

Please analyze:
1. **Functionality**: What each panel monitors
2. **Differences**: Key configuration variations
3. **Best Choice**: Which approach is better and why
4. **Merge Strategy**: How to combine if beneficial
5. **Use Cases**: When to use each panel type

Provide actionable recommendations.""",
                    "description": "Comparative analysis of dashboard panels",
                    "use_case": "Panel design decisions and optimization"
                }
            },
            
            # Dashboard Schema Analysis for Modifications
            "dashboard_analysis": {
                "schema_recommendations": {
                    "template": """Based on the following database table schemas, provide recommendations for Grafana dashboard modifications:

{schema_info}

User's Modification Request:
{modification_request}

Provide practical recommendations:
1. **Relevant Tables**: Which tables are most suitable for the modification
2. **Key Columns**: Specific columns for metrics, filters, and grouping
3. **Query Patterns**: Suggested SQL patterns based on column types
4. **Panel Types**: Recommended Grafana panel types for different data types
5. **Performance Tips**: Indexing and query optimization suggestions

Focus on actionable implementation guidance.""",
                    "description": "Schema-based analysis for dashboard modifications",
                    "use_case": "Generating dashboard recommendations from database schema information"
                }
            }
        }
    
    def get_prompt(self, category: str, prompt_type: str, **kwargs) -> Optional[str]:
        """
        Get a formatted prompt template.
        
        Args:
            category: The prompt category (e.g., 'data_analysis', 'schema_analysis')
            prompt_type: The specific prompt type within the category
            **kwargs: Variables to substitute in the template
        
        Returns:
            Formatted prompt string or None if not found
        """
        try:
            template = self.prompts[category][prompt_type]["template"]
            return template.format(**kwargs)
        except KeyError:
            return None
    
    def get_prompt_info(self, category: str, prompt_type: str) -> Optional[Dict[str, str]]:
        """
        Get information about a specific prompt.
        
        Args:
            category: The prompt category
            prompt_type: The specific prompt type
        
        Returns:
            Dictionary with prompt information or None if not found
        """
        try:
            prompt_data = self.prompts[category][prompt_type]
            return {
                "description": prompt_data["description"],
                "use_case": prompt_data["use_case"]
            }
        except KeyError:
            return None
    
    def list_categories(self) -> list:
        """Get all available prompt categories."""
        return list(self.prompts.keys())
    
    def list_types(self, category: str) -> list:
        """Get all available prompt types for a given category."""
        if category in self.prompts:
            return list(self.prompts[category].keys())
        return []
    
    def add_custom_prompt(self, category: str, prompt_type: str, template: str, 
                         description: str, use_case: str) -> bool:
        """
        Add a custom prompt template.
        
        Args:
            category: The prompt category
            prompt_type: The specific prompt type
            template: The prompt template with placeholders
            description: Description of the prompt
            use_case: Use case for the prompt
        
        Returns:
            True if added successfully, False otherwise
        """
        try:
            if category not in self.prompts:
                self.prompts[category] = {}
            
            self.prompts[category][prompt_type] = {
                "template": template,
                "description": description,
                "use_case": use_case
            }
            return True
        except Exception:
            return False
    
    def get_system_prompt(self, analysis_type: str = "general") -> str:
        """
        Get appropriate system prompt based on analysis type.
        
        Args:
            analysis_type: Type of analysis being performed
        
        Returns:
            System prompt string
        """
        system_prompts = {
            "general": "You are a data analyst expert who provides clear, insightful summaries of database information.",
            "statistical": "You are a statistical analyst expert who provides detailed statistical insights and patterns from data.",
            "business": "You are a business intelligence expert who provides strategic insights and recommendations from data.",
            "quality": "You are a data quality expert who identifies and provides recommendations for data quality issues.",
            "security": "You are a data security expert who identifies sensitive information and provides security recommendations.",
            "performance": "You are a database performance expert who analyzes and provides optimization recommendations.",
            "grafana": "You are a Grafana dashboard expert who provides detailed analysis and insights about dashboard configurations. Focus on monitoring strategy, visualization choices, and overall effectiveness.",
            "grafana_modification": "You are a Grafana dashboard expert. You modify dashboard JSON configurations based on user requests. Always respond with valid JSON only.",
            "grafana_troubleshooting": "You are a Grafana troubleshooting expert who helps diagnose and solve dashboard issues with practical, step-by-step solutions.",
            "grafana_optimization": "You are a Grafana optimization expert who improves dashboard performance, user experience, and monitoring effectiveness.",
            "schema_recommendations": "You are a database and dashboard expert who analyzes table schemas to provide practical Grafana dashboard recommendations. Focus on actionable implementation guidance."
        }
        
        return system_prompts.get(analysis_type, system_prompts["general"])


# Convenience function for backward compatibility
def get_legacy_prompts(data_text: str) -> Dict[str, str]:
    """
    Get legacy prompt format for backward compatibility.
    
    Args:
        data_text: The data to analyze
    
    Returns:
        Dictionary with legacy prompt structure
    """
    prompt_manager = PromptManager()
    
    return {
        "general": prompt_manager.get_prompt("data_analysis", "general", data_text=data_text),
        "statistical": prompt_manager.get_prompt("data_analysis", "statistical", data_text=data_text),
        "business": prompt_manager.get_prompt("data_analysis", "business", data_text=data_text)
    }


# Example usage and demonstration
if __name__ == "__main__":
    # Initialize prompt manager
    pm = PromptManager()
    
    # List available categories
    print("Available categories:")
    for category in pm.list_categories():
        print(f"  - {category}")
        for prompt_type in pm.list_types(category):
            info = pm.get_prompt_info(category, prompt_type)
            print(f"    └── {prompt_type}: {info['description']}")
    
    # Example usage
    sample_data = "Column: id, name, age\nRow 1: {'id': 1, 'name': 'John', 'age': 30}"
    prompt = pm.get_prompt("data_analysis", "general", data_text=sample_data)
    print(f"\nSample prompt:\n{prompt}")
