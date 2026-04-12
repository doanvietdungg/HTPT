from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    NODE_ID: str = "node1"
    MY_IP: str = "127.0.0.1"
    API_PORT: int = 8000
    PEER_IPS: str = "" # Comma separated list of IP:PORT of other nodes
    DATA_DIR: str = "data"
    DB_URL: str = "mysql+pymysql://hdfs_user:hdfs_pass@localhost:3306/hdfs_meta"
    
    # Storage settings
    REPLICATION_FACTOR: int = 2
    CHUNK_SIZE: int = 1024 * 1024 * 20 # 20MB
    
    # Leader Election settings
    HEARTBEAT_INTERVAL: int = 1 # seconds
    ELECTION_TIMEOUT: int = 4 # seconds
    
    # Security
    SECRET_KEY: str = "supersecretkey_for_jwt_which_should_be_changed"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    class Config:
        env_file = ".env"

settings = Settings()
