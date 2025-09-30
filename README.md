# 🎯 Groq Cloud Spyder - AI-Powered Data & Dashboard Analysis

A comprehensive suite of AI-powered tools for database analysis and Grafana dashboard management using the Groq LLM API.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Analysis Pipeline](#database-analysis-pipeline)
- [Grafana Dashboard Management Pipeline](#grafana-dashboard-management-pipeline)
- [Prompt System](#prompt-system)
- [Usage Examples](#usage-examples)
- [Database Schema](#database-schema)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🔍 Overview

This project provides two main capabilities:

1. **Database Analysis** (`index.py`) - Analyze PostgreSQL database tables and custom queries using AI
2. **Grafana Dashboard Management** (`grafana_dashboard_manager.py`) - Manage, analyze, and modify Grafana dashboards with AI assistance

Both tools leverage the Groq LLM API for intelligent analysis and modification capabilities.

## ✨ Features

### Database Analysis
- 📊 Automated table schema analysis
- 🔍 Sample data summarization
- 📈 Statistical insights and patterns
- 💼 Business intelligence recommendations
- 🔍 Custom SQL query analysis
- 🏗️ Multiple analysis types (general, statistical, business, quality)

### Grafana Dashboard Management
- 📋 List and browse existing dashboards
- 🔍 AI-powered dashboard analysis and summarization
- ✏️ Natural language dashboard modification
- 💾 Automated dashboard creation and storage
- 🎨 Dashboard optimization recommendations
- 🔧 Troubleshooting assistance

## 🚀 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Groq API key

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd groq-cloud-spyder
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```env
   # Database Configuration
   psgrsql_db_host=localhost
   psgrsql_db_name=your_database_name
   psgrsql_db_user=postgres
   psgrsql_db_pswd=your_password
   psgrsql_db_port=5432
   
   # Groq API Configuration
   GROQ_API_KEY=your_groq_api_key_here
   ```

## ⚙️ Configuration

### Database Setup

For **Database Analysis**, ensure your PostgreSQL database is accessible with the configured credentials.

For **Grafana Dashboard Management**, you need a `grafana_test` database with the following table structure:

```sql
CREATE TABLE public.dashboard (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data JSONB NOT NULL
);

-- Create an index for better performance
CREATE INDEX idx_dashboard_slug ON public.dashboard(slug);
CREATE INDEX idx_dashboard_updated ON public.dashboard(updated DESC);
```

### Model Configuration

Update the model in either script by modifying the `MODEL` variable:

```python
MODEL = "qwen/qwen3-32b"  # or any other supported Groq model
```

## 📊 Database Analysis Pipeline

### Workflow Steps

1. **Initialize Connection** - Connect to PostgreSQL and Groq API
2. **Table Discovery** - List all available tables in the database
3. **Table Selection** - User selects a table or provides custom query
4. **Analysis Type Selection** - Choose from multiple analysis categories:
   - Data Analysis: general, statistical, business, quality
   - Schema Analysis: structure, optimization
   - Security Analysis: assessment
5. **AI Analysis** - Generate insights using Groq LLM
6. **Results Display** - Present formatted analysis results

### Usage

```bash
python index.py
```

### Example Output

```
Database Summarizer POC with Groq API
============================================================

Found 5 tables in database:
  1. users
  2. orders
  3. products
  4. categories
  5. reviews

Options:
1. Summarize a specific table
2. Execute custom query and summarize
3. Exit

Enter your choice (1-3): 1
Enter table number (1-5): 2

Analysis categories:
1. Data Analysis
2. Schema Analysis
3. Security Analysis
4. Query Analysis

Choose category (1-4): 1

Available analysis types for Data Analysis:
1. General - General overview analysis of database data
2. Statistical - Statistical analysis focused on numerical insights
3. Business - Business-focused analysis for strategic insights
4. Quality - Data quality assessment and validation

Choose type (1-4): 3

============================================================
Analyzing table: orders
============================================================

[AI-generated business analysis results...]
```

## 🎯 Grafana Dashboard Management Pipeline

### Workflow Steps

1. **Database Connection** - Connect to `grafana_test` database
2. **Dashboard Discovery** - List all dashboards from the `dashboard` table
3. **Dashboard Selection** - User selects a dashboard by number
4. **AI Analysis** - Comprehensive dashboard analysis using Groq LLM
5. **Modification Request** - User describes desired changes
6. **Name New Dashboard** - User provides name for the modified dashboard
7. **AI Modification** - LLM modifies the dashboard JSON
8. **Database Storage** - Save the new dashboard to the database

### Usage

```bash
python grafana_dashboard_manager.py
```

### Example Workflow

```
🎯 Grafana Dashboard Manager
============================================================

📊 Found 3 dashboards:
------------------------------------------------------------
 1. System Performance Overview
    Slug: system-performance-overview
    Updated: 2024-01-15 10:30:00

 2. Application Metrics
    Slug: application-metrics
    Updated: 2024-01-14 15:45:00

 3. Infrastructure Monitoring
    Slug: infrastructure-monitoring
    Updated: 2024-01-13 09:20:00

Select a dashboard (1-3): 1

✅ Selected: System Performance Overview

🔍 Analyzing dashboard...
============================================================

## Dashboard Overview
This dashboard monitors system performance metrics including CPU usage, memory consumption, disk I/O, and network traffic...

[Detailed AI analysis continues...]

============================================================
📝 Dashboard Modification
============================================================

Describe the changes you want to make to this dashboard: Add a new panel showing database connection counts and slow query metrics

Enter a name for the new dashboard: System Performance with Database Metrics

🤖 Modifying dashboard using AI...
This may take a moment...

💾 Saving new dashboard: 'System Performance with Database Metrics'

✅ Successfully created new dashboard with ID: 4
   Title: System Performance with Database Metrics
   Slug: system-performance-with-database-metrics

🎉 Dashboard workflow completed!
```

## 🔧 Robust JSON Processing

The Grafana Dashboard Manager includes sophisticated JSON extraction and validation capabilities to handle various LLM response formats:

### JSON Extraction Strategies

The system uses multiple fallback strategies to extract valid JSON from LLM responses:

1. **Direct Parsing** - Try parsing the response as-is
2. **Code Block Removal** - Remove markdown code block markers (```json, ```)
3. **Regex Pattern Matching** - Find JSON objects using regex patterns
4. **Line-by-Line Analysis** - Extract JSON from mixed text responses
5. **Common Issue Fixes** - Fix trailing commas, quotes, comments
6. **Minimal Structure Generation** - Create basic dashboard structure as last resort

### Dashboard Validation

After successful JSON extraction, the system validates and fixes dashboard structure:

- **Required Fields** - Ensures all mandatory Grafana dashboard fields exist
- **Panel Validation** - Validates panel structure and ensures unique IDs
- **Time Range Validation** - Checks and fixes time configuration
- **Template Variables** - Validates templating structure
- **Annotations** - Ensures proper annotations format

### Error Handling and Debugging

- **Debug File Generation** - Saves problematic LLM responses for analysis
- **Detailed Error Messages** - Provides specific information about parsing failures
- **Warning Messages** - Alerts when fallback strategies are used
- **Test Mode** - Built-in testing for JSON extraction capabilities

### Usage Examples

```bash
# Test JSON extraction capabilities
python grafana_dashboard_manager.py --test-json

# Normal operation with enhanced error handling
python grafana_dashboard_manager.py
```

### Troubleshooting JSON Issues

If you encounter JSON parsing errors:

1. Check the generated debug files (`debug_response_*.txt`)
2. Review the LLM response for unexpected formatting
3. Use the test mode to validate extraction logic
4. Consider adjusting the model temperature or prompt

## 📊 Comprehensive Logging System

The Grafana Dashboard Manager includes extensive logging capabilities to track all interactions, debug issues, and audit system usage:

### Log File Structure

Each session creates timestamped log files in the `logs/` directory:

- **Standard Log**: `logs/grafana_manager_YYYYMMDD_HHMMSS.log` - Human-readable detailed logs
- **Structured Log**: `logs/grafana_manager_YYYYMMDD_HHMMSS_structured.jsonl` - Machine-readable JSON logs

### What Gets Logged

#### 1. Session Information
- System initialization and configuration
- Database connection details
- Model and API settings
- Session start/end timestamps

#### 2. Complete Prompt/Response Pairs
- **Dashboard Analysis**: Full prompts and AI responses for dashboard summarization
- **Dashboard Modification**: Complete modification requests and resulting JSON
- **System Prompts**: All system prompts sent to the LLM
- **Response Metadata**: Response lengths, processing times, model used

#### 3. Workflow Activities
- Dashboard selection and user choices
- User modification requests
- Database operations (fetch, insert)
- Success/failure status for each step

#### 4. Error Handling
- JSON extraction failures with full context
- Database connection issues
- API call failures
- Validation warnings and errors

#### 5. Debug Information
- JSON extraction strategies used
- Dashboard validation steps
- Performance metrics
- User interaction patterns

### Log Format Examples

#### Standard Log Entry
```
2024-01-15 14:30:25,123 | INFO | dashboard_analysis | OPERATION: dashboard_analysis
2024-01-15 14:30:25,124 | INFO | dashboard_analysis | METADATA: {
  "dashboard_id": 1,
  "dashboard_title": "System Performance",
  "operation_type": "analysis"
}
2024-01-15 14:30:25,125 | INFO | dashboard_analysis | PROMPT:
SYSTEM: You are a Grafana dashboard expert...
USER: Analyze the following Grafana dashboard...
2024-01-15 14:30:45,332 | INFO | dashboard_analysis | RESPONSE:
## Dashboard Overview
This dashboard monitors system performance...
```

#### Structured JSON Log Entry
```json
{
  "timestamp": "2024-01-15T14:30:25.123456",
  "operation": "dashboard_analysis",
  "model": "qwen/qwen3-32b",
  "prompt_length": 2048,
  "response_length": 1536,
  "metadata": {
    "dashboard_id": 1,
    "dashboard_title": "System Performance",
    "operation_type": "analysis"
  },
  "prompt": "SYSTEM: You are a Grafana dashboard expert...",
  "response": "## Dashboard Overview..."
}
```

### Log Analysis and Usage

#### Parse Structured Logs for Analytics
```python
import json

# Read structured logs
with open('logs/grafana_manager_20240115_143025_structured.jsonl', 'r') as f:
    for line in f:
        entry = json.loads(line)
        print(f"Operation: {entry['operation']}, Time: {entry['timestamp']}")
```

#### Monitor System Performance
```bash
# Count operations by type
grep "OPERATION:" logs/grafana_manager_*.log | cut -d: -f4 | sort | uniq -c

# Find error patterns
grep "ERROR" logs/grafana_manager_*.log

# Check response times
grep "response_length" logs/*_structured.jsonl
```

### Privacy and Security

- **Sensitive Data**: Database credentials are not logged
- **User Data**: Dashboard content is logged for debugging (consider this for sensitive environments)
- **API Keys**: Only key presence is logged, not actual values
- **Retention**: Implement log rotation for production use

### Configuration Options

Log behavior can be customized by modifying the `setup_logging()` method:

```python
# Adjust log levels
file_handler.setLevel(logging.DEBUG)  # More verbose
console_handler.setLevel(logging.ERROR)  # Less console output

# Change log location
log_dir = "/custom/log/path"

# Modify log format
formatter = logging.Formatter('%(asctime)s - %(message)s')
```

## 🎨 Prompt System

The project uses a sophisticated prompt management system (`prompts.py`) that organizes prompts by categories and types:

### Available Categories

1. **data_analysis** - Database data analysis prompts
   - `general` - General overview and insights
   - `statistical` - Statistical patterns and distributions
   - `business` - Business intelligence and recommendations
   - `quality` - Data quality assessment

2. **schema_analysis** - Database schema evaluation
   - `structure` - Schema design assessment
   - `optimization` - Performance optimization

3. **security_analysis** - Security-focused analysis
   - `assessment` - Security and compliance review

4. **query_analysis** - SQL query analysis
   - `performance` - Query optimization
   - `results` - Result set analysis

5. **grafana_analysis** - Grafana dashboard analysis
   - `summary` - Comprehensive dashboard summary
   - `modification` - Dashboard JSON modification
   - `best_practices` - Best practices review
   - `troubleshooting` - Issue diagnosis and resolution

6. **grafana_panels** - Panel-specific analysis
   - `optimization` - Panel performance optimization
   - `comparison` - Comparative panel analysis

### Adding Custom Prompts

```python
from prompts import PromptManager

pm = PromptManager()
pm.add_custom_prompt(
    "custom_category", 
    "custom_type",
    "Your prompt template with {variables}",
    "Description of the prompt",
    "Use case for this prompt"
)
```

## 📝 Usage Examples

### Database Analysis Example

```python
from index import DatabaseSummarizer

# Initialize
summarizer = DatabaseSummarizer()

# Analyze a specific table
summarizer.summarize_table("users", "business", "data_analysis")

# Execute custom query
data = summarizer.execute_query("SELECT COUNT(*) as total FROM orders WHERE status = 'completed'")
```

### Grafana Dashboard Management Example

```python
from grafana_dashboard_manager import GrafanaDashboardManager

# Initialize
manager = GrafanaDashboardManager()

# Get dashboard list
dashboards = manager.get_dashboard_list()

# Analyze specific dashboard
dashboard = manager.get_dashboard_by_id(1)
summary = manager.summarize_dashboard_with_groq(dashboard)

# Modify dashboard
modified = manager.modify_dashboard_with_groq(dashboard, "Add CPU temperature panel")
```

## 🗄️ Database Schema

### Required Tables

#### For Database Analysis
Any PostgreSQL database with tables you want to analyze.

#### For Grafana Dashboard Management
```sql
-- grafana_test database
CREATE TABLE public.dashboard (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data JSONB NOT NULL
);
```

### Sample Data Insertion

```sql
INSERT INTO public.dashboard (title, slug, data) VALUES 
(
    'Sample Dashboard',
    'sample-dashboard',
    '{
        "title": "Sample Dashboard",
        "panels": [
            {
                "id": 1,
                "title": "CPU Usage",
                "type": "graph",
                "targets": [{"expr": "cpu_usage"}]
            }
        ],
        "time": {"from": "now-1h", "to": "now"},
        "refresh": "5s"
    }'
);
```

## 🔧 Troubleshooting

### Common Issues

1. **Connection Errors**
   - Verify database credentials in `.env`
   - Ensure PostgreSQL is running and accessible
   - Check firewall settings

2. **Groq API Errors**
   - Verify `GROQ_API_KEY` is set correctly
   - Check API quota and limits
   - Ensure internet connectivity

3. **JSON Parsing Errors**
   - Verify dashboard JSON format in database
   - Check for special characters in dashboard data
   - Validate JSON structure

4. **Import Errors**
   - Run `pip install -r requirements.txt`
   - Check Python version compatibility (3.8+)
   - Verify virtual environment activation

### Debug Mode

Enable debug logging by adding to your script:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing Connection

```python
# Test database connection
from grafana_dashboard_manager import GrafanaDashboardManager
manager = GrafanaDashboardManager()
dashboards = manager.get_dashboard_list()
print(f"Found {len(dashboards)} dashboards")

# Test Groq API
summary = manager.summarize_dashboard_with_groq(dashboards[0])
print("API working!" if summary else "API error")
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Include error handling for database and API calls
- Add type hints where applicable
- Update README for new features

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Groq](https://groq.com/) for the fast LLM API
- [Grafana](https://grafana.com/) for the dashboard platform
- [PostgreSQL](https://postgresql.org/) for the database engine

---

**Happy Analyzing! 🚀**

For questions or support, please open an issue in the repository.
# gen-grafana-ai
