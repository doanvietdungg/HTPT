Tôi là sinh viên ngành Công nghệ thông tin, đang làm đồ án môn Phát triển Hệ thống Phân tán theo nhóm 3 người, thời gian thực hiện là 2 tuần.

Tôi muốn bạn đóng vai trò là:
1. Kiến trúc sư hệ thống phân tán
2. Technical lead
3. Senior backend engineer

Nhiệm vụ của bạn là giúp tôi triển khai trọn bộ một đề án theo hướng thực chiến, có thể code/demo được, không chỉ dừng ở lý thuyết.

========================
1. BỐI CẢNH ĐỀ TÀI
========================

Đề tài của nhóm tôi là:

“Thiết kế và triển khai hệ thống lưu trữ file phân tán hỗ trợ replication, leader election, fault recovery, phân quyền và đa client trong môi trường LAN”

Hệ thống là một mini distributed file storage lấy cảm hứng từ HDFS nhưng mở rộng thêm nhiều chức năng.

========================
2. MỤC TIÊU ĐỀ TÀI
========================

Hệ thống cần hỗ trợ:

- Upload file
- Download file
- Chia file thành chunk
- Lưu chunk trên nhiều node
- Replication factor cấu hình được
- Heartbeat giữa các node
- Phát hiện node lỗi
- Tự động recovery và re-replication
- Leader election khi node chính lỗi
- Hỗ trợ nhiều client đồng thời
- Thêm / sửa / xóa / đổi tên file
- Phân quyền đầy đủ theo user/role/file-level ACL
- Có web UI / dashboard cơ bản để demo
- Chạy trên 3 máy khác nhau trong LAN

========================
3. KIẾN TRÚC CUỐI CÙNG ĐÃ CHỐT
========================

Triển khai trên 3 máy khác nhau trong cùng mạng LAN.

Mỗi máy sẽ chạy:
- 1 DataNode
- 1 NameNode agent

Trong 3 NameNode agent:
- 1 node đóng vai trò Leader NameNode
- 2 node đóng vai trò Follower/Standby NameNode

Tức là:
- cả 3 máy đều có storage
- cả 3 máy đều có khả năng tham gia leader election ở lớp control/metadata
- dữ liệu được phân tán thật qua mạng LAN

Kiến trúc logic gồm 4 lớp:
1. Client layer
2. Metadata & coordination layer
3. Storage layer
4. Security & access control layer

========================
4. CÔNG NGHỆ ƯU TIÊN
========================

Ưu tiên stack dễ làm, dễ demo, phù hợp nhóm sinh viên 2 tuần, nhưng vẫn đủ đẹp về mặt kiến trúc.

Ưu tiên:
- Python
- FastAPI hoặc gRPC (hãy đề xuất phương án hợp lý nhất)
- SQLite hoặc JSON persistence cho metadata
- threading / asyncio nếu cần
- local disk folder cho DataNode storage
- web UI đơn giản bằng FastAPI + Jinja / React nhẹ / hoặc giải pháp gọn nhất có thể

Nếu có nhiều lựa chọn, hãy ưu tiên:
- dễ code
- dễ debug
- dễ demo
- vẫn thể hiện được đúng tinh thần hệ thống phân tán

========================
5. PHẠM VI CHỨC NĂNG CẦN THIẾT KẾ VÀ TRIỂN KHAI
========================

A. Core distributed storage:
- chunking
- replication
- upload
- download
- metadata management
- DataNode storage
- NameNode metadata
- block report
- heartbeat
- failure detection
- re-replication

B. Advanced distributed features:
- leader election
- follower sync metadata
- leader failover
- node rejoin
- metadata reconciliation

C. Business/file operations:
- create/upload file
- update file (theo hướng upload version mới / overwrite có kiểm soát)
- delete file
- rename file
- logical folders nếu hợp lý

D. Security:
- login
- user
- role
- role-permission
- file-level ACL
- audit log

E. Concurrent clients:
- nhiều client cùng truy cập
- file-level lock
- shared lock cho read
- exclusive lock cho write/delete/rename
- timeout lock

F. Demo/UI:
- upload file
- xem node status
- xem chunk distribution
- xem metadata cơ bản
- xem replication status
- xem leader/follower status

========================
6. THIẾT KẾ METADATA ĐÃ CHỐT
========================

Hệ thống cần metadata đủ sâu để triển khai thật.

Các thực thể logic cần có:

1. ClusterNode
- node_id
- node_type
- host
- port
- machine_name
- status
- role
- term/epoch
- last_heartbeat
- storage_capacity_total
- storage_capacity_used
- cpu_load
- network_score
- version

2. User
- user_id
- username
- password_hash
- full_name
- status
- created_at
- last_login

3. Role
- role_id
- role_name
- description

4. UserRole
- user_id
- role_id

5. FileEntry
- file_id
- file_name
- logical_path
- owner_user_id
- size_bytes
- chunk_size
- total_chunks
- replication_factor
- version_no
- checksum_whole_file
- status
- created_at
- updated_at
- last_access_at
- parent_directory_id (nếu dùng folder logic)

6. ChunkEntry
- chunk_id
- file_id
- chunk_index
- primary_node_id
- chunk_size
- checksum_chunk
- status
- created_at

7. ChunkReplica
- replica_id
- chunk_id
- node_id
- replica_order
- replica_state
- stored_path
- last_verified_at

8. FilePermission
- permission_id
- file_id
- subject_type
- subject_id
- can_read
- can_write
- can_delete
- can_rename
- can_share
- granted_by
- granted_at

9. UploadSession
- session_id
- file_id
- client_id
- status
- started_at
- expires_at
- completed_chunks
- failed_chunks

10. ClientSession
- client_id
- user_id
- login_time
- ip_address
- status

11. FileLock
- lock_id
- file_id
- lock_type
- owner_client_id
- owner_user_id
- acquired_at
- expire_at
- status

12. AuditLog
- audit_id
- user_id
- action_type
- file_id
- target_node_id
- timestamp
- result
- detail

13. ElectionState
- node_id
- current_term
- voted_for
- leader_id
- last_leader_heartbeat
- state

Bạn có thể chuẩn hóa lại model/bảng nếu cần, nhưng phải giữ tinh thần thiết kế trên.

========================
7. QUY TẮC CHỌN NODE KHÔNG ĐƯỢC ĐƠN GIẢN
========================

Tôi không muốn round-robin đơn thuần.

Hãy thiết kế cơ chế placement theo kiểu scoring-based placement.

Yêu cầu:
- node phải ALIVE
- đủ dung lượng
- không chứa replica trùng chunk
- ưu tiên node có free space tốt
- ưu tiên node có load thấp hơn
- ưu tiên node có reliability tốt
- có xét network score
- tránh hotspot
- nếu hợp lý, có thể thêm zone-awareness mô phỏng

Hãy thiết kế:
- công thức scoring
- thuật toán chọn primary replica
- thuật toán chọn secondary replicas
- cách chọn node khi recovery
- cách chọn node khi download/read

========================
8. YÊU CẦU VỀ UPLOAD PHỨC TẠP HƠN
========================

Tôi muốn upload được thiết kế bài bản hơn, không quá đơn giản.

Hãy triển khai theo hướng:
- client gửi request tạo upload session
- leader namenode kiểm tra quyền, tạo file_id, lập chunk placement plan
- client chia file thành chunk
- với mỗi chunk:
  - client gửi tới primary DataNode
  - primary DataNode lưu local
  - primary forward sang secondary replicas theo pipeline
  - secondary ack ngược về
- chỉ khi đủ ack theo chính sách thì chunk mới được coi là thành công
- khi tất cả chunk thành công thì mới commit metadata file
- nếu fail giữa chừng:
  - chỉ retry chunk fail
  - chunk orphan cần có cleanup mechanism

Nếu bạn thấy cần, có thể dùng mô hình commit 2 phase đơn giản:
- phase upload chunk
- phase commit file metadata

========================
9. YÊU CẦU VỀ LEADER ELECTION
========================

Tôi muốn có leader election thật sự ở mức demo được.

Tuy nhiên, phải cân bằng với tính khả thi trong 2 tuần.

Bạn hãy đề xuất và triển khai theo hướng thực tế nhất, ví dụ:
- Bully algorithm nâng cao
hoặc
- Raft simplified

Nhưng phải giải quyết được ít nhất:
- leader heartbeat
- follower timeout
- election trigger
- chọn leader mới
- cập nhật leader info
- follower sync metadata cơ bản
- leader failover
- node rejoin cluster

Nếu bạn cho rằng Bully phù hợp hơn cho tiến độ 2 tuần, hãy chọn Bully và giải thích rõ.

========================
10. YÊU CẦU VỀ CONSISTENCY & RECOVERY
========================

Hãy thiết kế rõ:

- file chỉ visible khi metadata commit thành công
- eventual consistency có kiểm soát
- chunk chưa commit thì coi là orphan
- có background cleanup
- node status gồm: ALIVE / SUSPECT / DEAD / RECOVERING
- khi node chết:
  - detect
  - đánh dấu under-replicated
  - re-replicate
  - update metadata
- khi node sống lại:
  - block report lại
  - leader đối chiếu metadata
  - reconcile chunk stale nếu cần

========================
11. GIỚI HẠN THỜI GIAN VÀ CÁCH LÀM VIỆC
========================

Nhóm tôi có:
- 3 người
- 2 tuần
- muốn làm rộng và sâu hơn mức cơ bản
- tự tin có thể làm phần bonus

Vì vậy, tôi muốn bạn giúp theo hướng:
- thực chiến
- chia nhỏ phase
- mỗi phase có output rõ
- có thể code được ngay
- có roadmap từ dễ đến khó
- tránh lan man lý thuyết

========================
12. CÁCH BẠN PHẢI HỖ TRỢ TÔI
========================

Tôi muốn bạn triển khai cùng tôi theo đúng thứ tự sau.
Không được nhảy cóc.

BƯỚC 1:
Hãy đánh giá lại toàn bộ scope trên dưới góc nhìn technical lead:
- điểm mạnh
- rủi ro
- phần nào bắt buộc
- phần nào nên làm sau
- phần nào có thể giảm rủi ro bằng cách đổi giải pháp

BƯỚC 2:
Thiết kế kiến trúc hệ thống hoàn chỉnh:
- component diagram
- node responsibilities
- communication paths
- deployment architecture trên 3 máy LAN
- service boundaries

BƯỚC 3:
Thiết kế dữ liệu và metadata hoàn chỉnh:
- model logic
- quan hệ giữa các thực thể
- nếu cần thì đề xuất schema SQLite/PostgreSQL/JSON store
- giải thích ngắn gọn từng bảng/model

BƯỚC 4:
Thiết kế API/spec giao tiếp:
- API giữa client và leader namenode
- API giữa client và datanode
- API giữa namenode và datanode
- API giữa namenode agents với nhau
- request/response mẫu
- flow lỗi

BƯỚC 5:
Thiết kế sequence flow chi tiết cho:
- upload file
- download file
- update file
- delete file
- rename file
- login và permission check
- concurrent access + locking
- heartbeat
- failure detection
- re-replication
- leader election
- node rejoin

BƯỚC 6:
Thiết kế thuật toán:
- chunking
- placement scoring
- re-replication
- read replica selection
- file locking
- leader election
- metadata sync
- orphan cleanup

BƯỚC 7:
Đề xuất cấu trúc source code/project folder hoàn chỉnh.

BƯỚC 8:
Lập plan triển khai 2 tuần cực chi tiết cho nhóm 3 người:
- theo ngày
- chia việc theo người
- phụ thuộc giữa các task
- output mỗi ngày
- mốc test tích hợp
- mốc demo thử

BƯỚC 9:
Sinh code skeleton hoàn chỉnh cho toàn hệ thống:
- folder structure
- server bootstrap
- model classes
- API routers
- service classes
- storage service
- election service
- heartbeat service
- recovery service
- auth service
- lock service
- metadata repository
- config files

BƯỚC 10:
Sau khi xong skeleton, tiếp tục triển khai từng module theo thứ tự ưu tiên:
1. auth + user + role
2. namenode metadata core
3. datanode storage core
4. upload/download
5. replication pipeline
6. heartbeat
7. failure detection
8. recovery
9. locking
10. multi-client test
11. election
12. dashboard

========================
13. YÊU CẦU VỀ CÁCH TRẢ LỜI
========================

Khi trả lời:
- luôn ưu tiên thực thi được
- không viết quá chung chung
- có thể dùng bullet nhưng phải rõ
- nếu đưa code thì code phải có cấu trúc, thực tế, nhất quán
- nếu phải lựa chọn giải pháp, hãy chọn giải pháp phù hợp nhất cho nhóm 3 người trong 2 tuần
- luôn nói rõ trade-off
- nếu có rủi ro, hãy chỉ rõ cách giảm rủi ro
- nếu một phần quá tham, hãy đề xuất phiên bản MVP rồi phiên bản nâng cao

========================
14. YÊU CẦU KHỞI ĐỘNG
========================

Hãy bắt đầu ngay với:

1. Đánh giá scope toàn dự án dưới góc nhìn technical lead
2. Chốt stack công nghệ tốt nhất
3. Chốt kiến trúc tổng thể cuối cùng
4. Chốt chiến lược leader election phù hợp nhất
5. Chốt chiến lược metadata persistence phù hợp nhất
6. Chốt chiến lược placement phù hợp nhất
7. Chốt chiến lược locking cho multi-client phù hợp nhất

Sau đó mới đi tiếp sang thiết kế chi tiết.