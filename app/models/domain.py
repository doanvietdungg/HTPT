from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
import datetime
from app.models.base import Base

# Shared MySQL table options for all models
MYSQL_TABLE_ARGS = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

class ClusterNode(Base):
    __tablename__ = "cluster_node"
    __table_args__ = MYSQL_TABLE_ARGS
    node_id = Column(String(64), primary_key=True, index=True)
    node_type = Column(String(32))          # NAMENODE, DATANODE
    host = Column(String(128))
    port = Column(Integer)
    machine_name = Column(String(128))
    status = Column(String(32))             # ALIVE, SUSPECT, DEAD, RECOVERING
    role = Column(String(32))               # LEADER, FOLLOWER
    term = Column(Integer, default=0)
    last_heartbeat = Column(DateTime, default=datetime.datetime.utcnow)
    storage_capacity_total = Column(Float, default=0.0)
    storage_capacity_used = Column(Float, default=0.0)
    cpu_load = Column(Float, default=0.0)
    network_score = Column(Float, default=1.0)
    version = Column(String(32))

class User(Base):
    __tablename__ = "users"
    __table_args__ = MYSQL_TABLE_ARGS
    user_id = Column(String(36), primary_key=True, index=True)
    username = Column(String(128), unique=True, index=True)
    password_hash = Column(String(256))
    full_name = Column(String(256))
    status = Column(String(32), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

class Role(Base):
    __tablename__ = "roles"
    __table_args__ = MYSQL_TABLE_ARGS
    role_id = Column(String(36), primary_key=True, index=True)
    role_name = Column(String(64), unique=True)
    description = Column(String(256), nullable=True)

class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = MYSQL_TABLE_ARGS
    user_id = Column(String(36), ForeignKey("users.user_id"), primary_key=True)
    role_id = Column(String(36), ForeignKey("roles.role_id"), primary_key=True)

class FileEntry(Base):
    __tablename__ = "file_entry"
    __table_args__ = MYSQL_TABLE_ARGS
    file_id = Column(String(36), primary_key=True, index=True)
    file_name = Column(String(512))
    logical_path = Column(String(512), index=True)
    owner_user_id = Column(String(36)) # Soft link to users.user_id
    size_bytes = Column(Integer)
    chunk_size = Column(Integer)
    total_chunks = Column(Integer)
    replication_factor = Column(Integer)
    version_no = Column(Integer, default=1)
    checksum_whole_file = Column(String(128), nullable=True)
    status = Column(String(32))             # UPLOADING, COMMITTED, DELETED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_access_at = Column(DateTime, nullable=True)
    parent_directory_id = Column(String(36), nullable=True)

class ChunkEntry(Base):
    __tablename__ = "chunk_entry"
    __table_args__ = MYSQL_TABLE_ARGS
    chunk_id = Column(String(64), primary_key=True, index=True)
    file_id = Column(String(36), index=True) # Soft link to file_entry.file_id
    chunk_index = Column(Integer)
    primary_node_id = Column(String(64))
    chunk_size = Column(Integer)
    checksum_chunk = Column(String(128), nullable=True)
    status = Column(String(32))             # ORPHAN, COMMITTED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ChunkReplica(Base):
    __tablename__ = "chunk_replica"
    __table_args__ = MYSQL_TABLE_ARGS
    replica_id = Column(String(36), primary_key=True, index=True)
    chunk_id = Column(String(64), index=True) # Soft link to chunk_entry.chunk_id
    node_id = Column(String(64)) # Soft link to cluster_node.node_id
    replica_order = Column(Integer)         # 0 for primary, 1/2 for secondary
    replica_state = Column(String(32))      # STALE, SYNCED
    stored_path = Column(String(512))
    last_verified_at = Column(DateTime, nullable=True)

class FilePermission(Base):
    __tablename__ = "file_permission"
    __table_args__ = MYSQL_TABLE_ARGS
    permission_id = Column(String(36), primary_key=True, index=True)
    file_id = Column(String(36), index=True) # Soft link to file_entry.file_id
    subject_type = Column(String(32))       # USER or ROLE
    subject_id = Column(String(36))
    can_read = Column(Boolean, default=False)
    can_write = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_rename = Column(Boolean, default=False)
    can_share = Column(Boolean, default=False)
    granted_by = Column(String(36))
    granted_at = Column(DateTime, default=datetime.datetime.utcnow)

class UploadSession(Base):
    __tablename__ = "upload_session"
    __table_args__ = MYSQL_TABLE_ARGS
    session_id = Column(String(36), primary_key=True, index=True)
    file_id = Column(String(36), index=True) # Soft link to file_entry
    client_id = Column(String(128))
    status = Column(String(32))             # STARTED, COMPLETED, FAILED
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime)
    completed_chunks = Column(Text, nullable=True)  # JSON list
    failed_chunks = Column(Text, nullable=True)     # JSON list

class ClientSession(Base):
    __tablename__ = "client_session"
    __table_args__ = MYSQL_TABLE_ARGS
    client_id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36)) # Soft link to users
    login_time = Column(DateTime, default=datetime.datetime.utcnow)
    ip_address = Column(String(64))
    status = Column(String(32))

class FileLock(Base):
    __tablename__ = "file_lock"
    __table_args__ = MYSQL_TABLE_ARGS
    lock_id = Column(String(36), primary_key=True, index=True)
    file_id = Column(String(36), index=True) # Soft link to file_entry
    lock_type = Column(String(32))          # SHARED, EXCLUSIVE
    owner_client_id = Column(String(128))
    owner_user_id = Column(String(36))
    acquired_at = Column(DateTime, default=datetime.datetime.utcnow)
    expire_at = Column(DateTime)
    status = Column(String(32))             # ACQUIRED, RELEASED

class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = MYSQL_TABLE_ARGS
    audit_id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), nullable=True)
    action_type = Column(String(64))
    file_id = Column(String(36), nullable=True)
    target_node_id = Column(String(64), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    result = Column(String(32))
    detail = Column(Text, nullable=True)

class ElectionState(Base):
    __tablename__ = "election_state"
    __table_args__ = MYSQL_TABLE_ARGS
    node_id = Column(String(64), primary_key=True, index=True)
    current_term = Column(Integer)
    voted_for = Column(String(64), nullable=True)
    leader_id = Column(String(64), nullable=True)
    last_leader_heartbeat = Column(DateTime, nullable=True)
    state = Column(String(32))              # LEADER, FOLLOWER, CANDIDATE
