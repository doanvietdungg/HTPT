from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from app.models.base import Base

class ClusterNode(Base):
    __tablename__ = "cluster_node"
    node_id = Column(String, primary_key=True, index=True)
    node_type = Column(String) # NAMENODE, DATANODE
    host = Column(String)
    port = Column(Integer)
    machine_name = Column(String)
    status = Column(String) # ALIVE, SUSPECT, DEAD, RECOVERING
    role = Column(String) # LEADER, FOLLOWER
    term = Column(Integer, default=0)
    last_heartbeat = Column(DateTime, default=datetime.datetime.utcnow)
    storage_capacity_total = Column(Float, default=0.0)
    storage_capacity_used = Column(Float, default=0.0)
    cpu_load = Column(Float, default=0.0)
    network_score = Column(Float, default=1.0)
    version = Column(String)

class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    full_name = Column(String)
    status = Column(String, default="ACTIVE")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

class Role(Base):
    __tablename__ = "roles"
    role_id = Column(String, primary_key=True, index=True)
    role_name = Column(String, unique=True)
    description = Column(String, nullable=True)

class UserRole(Base):
    __tablename__ = "user_roles"
    user_id = Column(String, ForeignKey("users.user_id"), primary_key=True)
    role_id = Column(String, ForeignKey("roles.role_id"), primary_key=True)

class FileEntry(Base):
    __tablename__ = "file_entry"
    file_id = Column(String, primary_key=True, index=True)
    file_name = Column(String)
    logical_path = Column(String, index=True)
    owner_user_id = Column(String, ForeignKey("users.user_id"))
    size_bytes = Column(Integer)
    chunk_size = Column(Integer)
    total_chunks = Column(Integer)
    replication_factor = Column(Integer)
    version_no = Column(Integer, default=1)
    checksum_whole_file = Column(String, nullable=True)
    status = Column(String) # UPLOADING, COMMITTED, DELETED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_access_at = Column(DateTime, nullable=True)
    parent_directory_id = Column(String, nullable=True)

class ChunkEntry(Base):
    __tablename__ = "chunk_entry"
    chunk_id = Column(String, primary_key=True, index=True)
    file_id = Column(String, ForeignKey("file_entry.file_id"))
    chunk_index = Column(Integer)
    primary_node_id = Column(String)
    chunk_size = Column(Integer)
    checksum_chunk = Column(String, nullable=True)
    status = Column(String) # ORPHAN, COMMITTED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ChunkReplica(Base):
    __tablename__ = "chunk_replica"
    replica_id = Column(String, primary_key=True, index=True)
    chunk_id = Column(String, ForeignKey("chunk_entry.chunk_id"))
    node_id = Column(String, ForeignKey("cluster_node.node_id"))
    replica_order = Column(Integer) # 0 for primary, 1/2 for secondary
    replica_state = Column(String) # STALE, SYNCED
    stored_path = Column(String)
    last_verified_at = Column(DateTime, nullable=True)

class FilePermission(Base):
    __tablename__ = "file_permission"
    permission_id = Column(String, primary_key=True, index=True)
    file_id = Column(String, ForeignKey("file_entry.file_id"))
    subject_type = Column(String) # USER or ROLE
    subject_id = Column(String)
    can_read = Column(Boolean, default=False)
    can_write = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_rename = Column(Boolean, default=False)
    can_share = Column(Boolean, default=False)
    granted_by = Column(String)
    granted_at = Column(DateTime, default=datetime.datetime.utcnow)

class UploadSession(Base):
    __tablename__ = "upload_session"
    session_id = Column(String, primary_key=True, index=True)
    file_id = Column(String, ForeignKey("file_entry.file_id"))
    client_id = Column(String)
    status = Column(String) # STARTED, COMPLETED, FAILED
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime)
    completed_chunks = Column(String) # JSON list or comma sep
    failed_chunks = Column(String) # JSON list or comma sep

class ClientSession(Base):
    __tablename__ = "client_session"
    client_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    login_time = Column(DateTime, default=datetime.datetime.utcnow)
    ip_address = Column(String)
    status = Column(String)

class FileLock(Base):
    __tablename__ = "file_lock"
    lock_id = Column(String, primary_key=True, index=True)
    file_id = Column(String, ForeignKey("file_entry.file_id"))
    lock_type = Column(String) # SHARED, EXCLUSIVE
    owner_client_id = Column(String)
    owner_user_id = Column(String)
    acquired_at = Column(DateTime, default=datetime.datetime.utcnow)
    expire_at = Column(DateTime)
    status = Column(String) # ACQUIRED, RELEASED

class AuditLog(Base):
    __tablename__ = "audit_log"
    audit_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=True)
    action_type = Column(String)
    file_id = Column(String, nullable=True)
    target_node_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    result = Column(String)
    detail = Column(String, nullable=True)

class ElectionState(Base):
    __tablename__ = "election_state"
    node_id = Column(String, primary_key=True, index=True)
    current_term = Column(Integer)
    voted_for = Column(String, nullable=True)
    leader_id = Column(String, nullable=True)
    last_leader_heartbeat = Column(DateTime, nullable=True)
    state = Column(String) # LEADER, FOLLOWER, CANDIDATE
