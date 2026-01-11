import ibm_db
import psycopg2
from sqlalchemy import create_engine
import logging
from typing import Dict, Any, Optional

class DatabaseConnection:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def test_connection(self) -> bool:
        raise NotImplementedError

class DB2Connection(DatabaseConnection):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connection = None
        self.engine = None
        
    def connect(self) -> bool:
        try:
            dsn = f"DATABASE={self.config['database']};HOSTNAME={self.config['host']};PORT={self.config['port']};PROTOCOL=TCPIP;UID={self.config['user']};PWD={self.config['password']};"
            self.connection = ibm_db.connect(dsn, "", "")
            
            # Create SQLAlchemy engine for easier querying
            db_uri = f"db2+ibm_db://{self.config['user']}:{self.config['password']}@{self.config['host']}:{self.config['port']}/{self.config['database']}"
            self.engine = create_engine(db_uri)
            
            self.logger.info("Successfully connected to DB2")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to DB2: {e}")
            return False
            
    def test_connection(self) -> bool:
        return self.connect()
        
    def execute_query(self, query: str) -> Optional[list]:
        try:
            if not self.connection:
                self.connect()
                
            stmt = ibm_db.exec_immediate(self.connection, query)
            results = []
            
            row = ibm_db.fetch_assoc(stmt)
            while row:
                results.append(row)
                row = ibm_db.fetch_assoc(stmt)
                
            return results
        except Exception as e:
            self.logger.error(f"Error executing DB2 query: {e}")
            return None
            
    def close(self):
        if self.connection:
            ibm_db.close(self.connection)
        if self.engine:
            self.engine.dispose()

class PostgreSQLConnection(DatabaseConnection):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connection = None
        self.engine = None
        
    def connect(self) -> bool:
        try:
            self.connection = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            
            # Create SQLAlchemy engine
            db_uri = f"postgresql://{self.config['user']}:{self.config['password']}@{self.config['host']}:{self.config['port']}/{self.config['database']}"
            self.engine = create_engine(db_uri)
            
            self.logger.info("Successfully connected to PostgreSQL")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to PostgreSQL: {e}")
            return False
            
    def test_connection(self) -> bool:
        return self.connect()
        
    def execute_query(self, query: str) -> Optional[list]:
        try:
            if not self.connection:
                self.connect()
                
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Fetch all rows
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))
                
            cursor.close()
            return results
        except Exception as e:
            self.logger.error(f"Error executing PostgreSQL query: {e}")
            return None
            
    def close(self):
        if self.connection:
            self.connection.close()
        if self.engine:
            self.engine.dispose()