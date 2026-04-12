# Mindmap: TỔNG QUAN HỆ THỐNG PHÂN TÁN (MINI-HDFS)

> Dán nội dung dấu sao bên dưới vào **markmap.js / Xmind / Whimsical** để vẽ sơ đồ.

---

* HỆ THỐNG LƯU TRỮ FILE PHÂN TÁN — MINI-HDFS
  * 1. TÍNH NĂNG TỔNG QUAN CỦA HỆ THỐNG
    * Lưu trữ file phân tán (Distributed File Storage)
      * File lớn được tự động chia nhỏ thành nhiều mảnh (Chunking)
      * Mỗi mảnh được phân phối sang các máy khác nhau trong mạng
    * Nhân bản dữ liệu tự động (Replication)
      * Mỗi mảnh được sao lưu sang ít nhất 1 máy dự phòng
      * Đảm bảo dữ liệu không mất khi 1 máy hỏng
    * Truy xuất file liền mạch (S3 Object Gateway)
      * Mỗi file được cấp 1 URL truy cập trực tiếp (CDN-like)
      * Trình duyệt có thể xem ảnh/video ngay mà không cần tải về
    * Bầu cử thủ lĩnh tự động (Bully Election)
      * Không có máy nào được chỉ định cứng làm Leader
      * Máy có ID cao nhất còn sống sẽ được bầu làm NameNode
    * Giám sát sức khỏe (Heartbeat Monitoring)
      * Các máy liên tục gửi tín hiệu sống cho nhau
      * Máy im lặng quá 30s → Bị đánh dấu DEAD, loại khỏi hệ thống
    * Phân quyền người dùng (Authentication)
      * Đăng ký, đăng nhập bằng JWT Token
      * Mỗi file gắn với chủ sở hữu (owner)
  * 2. CỤM MÁY — 3 NODES
    * NODE 1 (node1 — FastAPI :8001 | MySQL :3307)
      * Tài nguyên cục bộ
        * DB riêng: MySQL instance `mysql_node1` — database `hdfs_meta` (Lưu FileEntry, ChunkEntry, ClusterNode)
        * Ổ cứng riêng: data_node1/ (Lưu Chunk vật lý)
        * Cấu hình riêng: NODE_ID=node1, PEER_IPS=node2,node3
      * Vai trò mặc định sau Bầu Cử
        * Thường là DataNode vì có Node_ID nhỏ nhất
        * Nhận và lưu Chunk khi NameNode phân công
    * NODE 2 (node2 — FastAPI :8002 | MySQL :3308)
      * Tài nguyên cục bộ
        * DB riêng: MySQL instance `mysql_node2` — database `hdfs_meta`
        * Ổ cứng riêng: data_node2/
        * Cấu hình riêng: NODE_ID=node2, PEER_IPS=node1,node3
      * Vai trò mặc định sau Bầu Cử
        * DataNode hoặc thăng lên NameNode nếu Node3 sập
    * NODE 3 (node3 — FastAPI :8003 | MySQL :3309)
      * Tài nguyên cục bộ
        * DB riêng: MySQL instance `mysql_node3` — database `hdfs_meta`
        * Ổ cứng riêng: data_node3/
        * Cấu hình riêng: NODE_ID=node3, PEER_IPS=node1,node2
      * Vai trò mặc định sau Bầu Cử
        * NameNode — vì có Node_ID lớn nhất (node3 > node2 > node1)
        * Điều phối toàn bộ upload, phân phối mảnh, giám sát mạng
    * LƯU Ý: Cả 3 node chạy chung 1 mã nguồn — vai trò được giao ĐỘNG theo Election
  * 3. CƠ CHẾ ĐẢM BẢO TÍNH HA (High Availability)
    * Không có điểm chết duy nhất (No Single Point of Failure)
      * Mỗi Chunk tồn tại ở 2 máy khác nhau (Replication Factor = 2)
      * Máy nào sập → dữ liệu vẫn còn ở máy dự phòng
    * Phát hiện sự cố tự động (Failure Detection)
      * Heartbeat Daemon chạy ngầm mỗi 10 giây
      * Nếu 1 node không phản hồi → Bị gán trạng thái DEAD
      * Node DEAD bị loại khỏi danh sách nhận Chunk mới
    * Tự phục hồi dữ liệu (Re-Replication Daemon)
      * Daemon nền kiểm tra định kỳ số bản sao của từng Chunk
      * Nếu 1 bản sao bị mất (do node chết) → Tự tạo lại bản sao trên node còn sống
      * [Đang triển khai] Đảm bảo Replication Factor luôn được duy trì
    * Bầu lại Leader tự động (Re-Election)
      * Khi NameNode chết → Các node còn lại tự khởi động Bầu Cử mới
      * Không cần can thiệp thủ công, hệ thống tự hồi phục
      * [Đang triển khai] Đồng bộ Metadata sang Leader mới sau khi bầu xong
  * 4. TÍNH TỰ TRỊ CỦA MỖI NODE (Autonomy)
    * Mỗi node tự quản lý dữ liệu cục bộ
      * DB SQLite độc lập — không phụ thuộc node khác để đọc/ghi
      * Thư mục ổ cứng độc lập — file vật lý tách biệt hoàn toàn
      * API đầy đủ — node nào cũng có thể nhận request trực tiếp từ Client
    * Mỗi node tự vận hành kể cả khi bị cô lập
      * Có thể tiếp nhận Upload, lưu Chunk, phục vụ Download
      * Không sập theo khi node khác ngừng hoạt động
    * Mỗi node tự quyết định vai trò của mình
      * Tự tham gia bầu cử và quyết định mình là Leader hay Follower
      * Tự loại bỏ node chết ra khỏi danh sách hợp tác
  * 5. GIAO DỊCH TRÊN TOÀN HỆ THỐNG (Cross-Node Transactions)
    * Giao dịch Upload (Đã triển khai)
      * Client → NameNode: Xin kế hoạch phân phối mảnh
      * Client → DataNode A: Đẩy Mảnh 0 (trực tiếp P2P)
      * DataNode A → DataNode B: Tự đẩy bản sao ngầm (Pipelining)
      * Client → DataNode B: Đẩy Mảnh 1 (trực tiếp P2P)
      * Kết quả: Dữ liệu trải ra đồng đều trên toàn cụm
    * Giao dịch Xem File (Đã triển khai)
      * Client → NameNode (S3 Gateway): Yêu cầu xem file
      * NameNode → DataNode A,B,C: Kéo từng Mảnh theo thứ tự
      * NameNode → Client: Truyền stream liên tục, ghép trong suốt
    * Giao dịch Phục hồi Sự cố (Đã triển khai một phần)
      * Heartbeat phát hiện Node chết → Cập nhật trạng thái toàn DB
      * Khi Client tải Chunk → Tự chuyển hướng sang Replica còn sống
      * [Kế hoạch] Re-Replication tự động sang node mới thay thế
    * Giao dịch Đồng bộ Metadata (Kế hoạch triển khai)
      * Sau mỗi lần Upload thành công → NameNode broadcast Metadata sang tất cả node
      * Bất kỳ node nào cũng có thể trả lời "File này ở đâu?" mà không hỏi NameNode
      * Đảm bảo tính nhất quán dữ liệu (Eventual Consistency) trên toàn cụm
