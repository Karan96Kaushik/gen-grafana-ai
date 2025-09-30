import os
import psycopg2
from groq import Groq
from dotenv import load_dotenv
from prompts import PromptManager

# Load environment variables
load_dotenv()

MODEL = "llama-3.1-70b-versatile"
MODEL = "gemma2-9b-it"
MODEL = "qwen/qwen3-32b"

class DatabaseSummarizer:
    def __init__(self):
        """Initialize connections to PostgreSQL and Groq"""
        # PostgreSQL connection
        self.db_config = {
            'host': os.getenv('psgrsql_db_host', 'localhost'),
            'database': os.getenv('psgrsql_db_name', 'your_database'),
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
        
        self.model = MODEL
        
        # Initialize prompt manager
        self.prompt_manager = PromptManager()
    
    def connect_db(self):
        """Create database connection"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    
    def get_table_list(self):
        """Get list of all tables in the database"""
        conn = self.connect_db()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return tables
        except Exception as e:
            print(f"Error fetching tables: {e}")
            return []
    
    def get_table_schema(self, table_name):
        """Get schema information for a specific table"""
        conn = self.connect_db()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT column_name, data_type --, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
            """)
            schema = cursor.fetchall()
            cursor.close()
            conn.close()
            return schema
        except Exception as e:
            print(f"Error fetching schema: {e}")
            return None

    def execute_query(self, query):
        """Execute a custom SQL query"""
        conn = self.connect_db()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Fetch results
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {'columns': columns, 'data': results}
        except Exception as e:
            print(f"Query execution error: {e}")
            return None
    
    def get_table_sample(self, table_name, limit=10):
        """Get sample data from a table"""
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        return self.execute_query(query)
    
    def format_data_for_llm(self, data):
        """Format query results for LLM consumption"""
        if not data:
            return "No data available"
        
        columns = data['columns']
        rows = data['data']
        
        # Create a formatted string
        formatted = f"Columns: {', '.join(columns)}\n\n"
        formatted += "Sample Data:\n"
        
        for i, row in enumerate(rows[:10], 1):
            formatted += f"Row {i}: {dict(zip(columns, row))}\n"
        
        return formatted
    
    def summarize_with_groq(self, data_text, prompt_type="general", category="data_analysis"):
        """Use Groq API to summarize data"""
        
        # Get prompt from prompt manager
        selected_prompt = self.prompt_manager.get_prompt(category, prompt_type, data_text=data_text)
        
        # Fallback to legacy general prompt if not found
        if not selected_prompt:
            selected_prompt = self.prompt_manager.get_prompt("data_analysis", "general", data_text=data_text)
        
        # Get appropriate system prompt
        system_prompt = self.prompt_manager.get_system_prompt(prompt_type)
        
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": selected_prompt
                    }
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=1024
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error calling Groq API: {e}"
    
    def summarize_table(self, table_name, prompt_type="general", category="data_analysis"):
        """Complete workflow: fetch table data and summarize it"""
        print(f"\n{'='*60}")
        print(f"Analyzing table: {table_name}")
        print(f"{'='*60}\n")
        
        # Get schema
        schema = self.get_table_schema(table_name)
        if schema:
            print("Table Schema:")
            for col in schema:
                print(f"  - {col[0]}: {col[1]}")
            print()
        
        # Get sample data
        data = self.get_table_sample(table_name)
        if not data:
            print("No data retrieved")
            return
        
        print(f"Retrieved {len(data['data'])} sample rows")
        print()
        
        # Format data
        formatted_data = self.format_data_for_llm(data)
        
        # Get AI summary
        print("Generating AI summary...\n")
        summary = self.summarize_with_groq(formatted_data, prompt_type, category)
        
        print("AI Summary:")
        print("-" * 60)
        print(summary)
        print("-" * 60)


def main():
    """Main function to run the POC"""
    print("Database Summarizer POC with Groq API")
    print("="*60)
    
    summarizer = DatabaseSummarizer()
    
    # Get list of tables
    tables = summarizer.get_table_list()
    
    if not tables:
        print("No tables found or connection failed")
        return
    
    print(f"\nFound {len(tables)} tables in database:")
    for i, table in enumerate(tables, 1):
        print(f"{i}. {table}")
    
    print("\nOptions:")
    print("1. Summarize a specific table")
    print("2. Execute custom query and summarize")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ")
    
    if choice == "1":
        table_num = int(input(f"Enter table number (1-{len(tables)}): "))
        if 1 <= table_num <= len(tables):
            table_name = tables[table_num - 1]
            
            print("\nAnalysis categories:")
            categories = summarizer.prompt_manager.list_categories()
            for i, cat in enumerate(categories, 1):
                print(f"{i}. {cat.replace('_', ' ').title()}")
            
            cat_choice = input(f"Choose category (1-{len(categories)}): ")
            try:
                selected_category = categories[int(cat_choice) - 1]
            except (ValueError, IndexError):
                selected_category = "data_analysis"
            
            print(f"\nAvailable analysis types for {selected_category.replace('_', ' ').title()}:")
            types = summarizer.prompt_manager.list_types(selected_category)
            for i, t in enumerate(types, 1):
                info = summarizer.prompt_manager.get_prompt_info(selected_category, t)
                print(f"{i}. {t.title()} - {info['description']}")
            
            type_choice = input(f"Choose type (1-{len(types)}): ")
            try:
                selected_type = types[int(type_choice) - 1]
            except (ValueError, IndexError):
                selected_type = "general"
            
            summarizer.summarize_table(table_name, selected_type, selected_category)
    
    elif choice == "2":
        query = input("Enter your SQL query: ")
        data = summarizer.execute_query(query)
        
        if data:
            formatted_data = summarizer.format_data_for_llm(data)
            
            print("\nAnalysis types for query results:")
            print("1. General results analysis")
            print("2. Performance analysis")
            
            analysis_choice = input("Choose analysis type (1-2): ")
            
            if analysis_choice == "2":
                # Performance analysis needs both query and results
                prompt = summarizer.prompt_manager.get_prompt(
                    "query_analysis", "performance", 
                    query_text=query, data_text=formatted_data
                )
                system_prompt = summarizer.prompt_manager.get_system_prompt("performance")
            else:
                # General results analysis
                prompt = summarizer.prompt_manager.get_prompt(
                    "query_analysis", "results", 
                    query_text=query, data_text=formatted_data
                )
                system_prompt = summarizer.prompt_manager.get_system_prompt("general")
            
            print("\nGenerating summary...\n")
            
            try:
                response = summarizer.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    model=summarizer.model,
                    temperature=0.3,
                    max_tokens=1024
                )
                summary = response.choices[0].message.content
                print(summary)
            except Exception as e:
                print(f"Error calling Groq API: {e}")
    
    print("\n\nPOC Complete!")


if __name__ == "__main__":
    main()