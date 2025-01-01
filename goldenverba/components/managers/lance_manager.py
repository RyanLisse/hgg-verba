import os
from typing import Optional, Any
import lancedb
from dotenv import load_dotenv
from lancedb.db import LanceDB
from lancedb.table import LanceTable

class LanceDBManager:
    """Manages LanceDB operations for vector storage and retrieval."""
    
    def __init__(self):
        """Initialize the LanceDB manager with environment variables."""
        load_dotenv()
        self.api_key = os.getenv("LANCEDB_API_KEY")
        self.uri = os.getenv("LANCEDB_URI")
        self.region = os.getenv("LANCEDB_REGION")
        self._db: Optional[LanceDB] = None
        
    def connect(self) -> LanceDB:
        """
        Connect to LanceDB using environment credentials.
        
        Returns:
            LanceDB: Connected database instance
            
        Raises:
            ValueError: If required environment variables are missing
            ConnectionError: If connection fails
        """
        if not all([self.api_key, self.uri, self.region]):
            raise ValueError("Missing required environment variables for LanceDB connection")
            
        try:
            self._db = lancedb.connect(
                uri=self.uri,
                api_key=self.api_key,
                region=self.region
            )
            return self._db
        except Exception as e:
            raise ConnectionError(f"Failed to connect to LanceDB: {str(e)}")
    
    def get_table(self, table_name: str) -> Optional[LanceTable]:
        """
        Get a table from the database.
        
        Args:
            table_name: Name of the table to retrieve
            
        Returns:
            Optional[LanceTable]: The requested table if it exists, None otherwise
        """
        if not self._db:
            self._db = self.connect()
        
        try:
            return self._db.open_table(table_name)
        except Exception:
            return None
    
    def create_table(self, table_name: str, schema: dict[str, Any]) -> LanceTable:
        """
        Create a new table in the database.
        
        Args:
            table_name: Name of the new table
            schema: Schema definition for the table
            
        Returns:
            LanceTable: The newly created table
            
        Raises:
            ValueError: If table creation fails
        """
        if not self._db:
            self._db = self.connect()
            
        try:
            return self._db.create_table(table_name, schema=schema)
        except Exception as e:
            raise ValueError(f"Failed to create table {table_name}: {str(e)}")