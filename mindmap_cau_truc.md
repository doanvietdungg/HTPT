# Mindmap: LUỒNG XỬ LÝ PHÂN TÁN (MINI-HDFS)

> Dán nội dung cấu trúc dấu sao bên dưới vào **Markmap.js / Xmind / Whimsical** để vẽ sơ đồ tự động.

---

* MINI-HDFS: LUỒNG XỬ LÝ PHÂN TÁN
  * 1. LUỒNG UPLOAD FILE
    * Bước 1: Client xin Sổ Đỏ (Init Upload)
      * Client gọi POST /api/files/upload/init
      * Gửi lên: tên file, kích thước (byte), đường dẫn ảo
      * NameNode tính toán: 150MB ÷ 20MB = 8 Mảnh (Chunks)
      * NameNode trả về Placement Plan (Bản đồ phân công từng mảnh)
        * chunk_index: Số thứ tự mảnh (0 → N)
        * primary_node: Máy chủ chính nhận mảnh
        * secondary_nodes: Danh sách máy sao lưu
        * cdn_url: URL S3 xem trực tiếp ngay khi upload xong
    * Bước 2: Client tự băm nhỏ File (Chunk Slicing)
      * Dùng file.slice(start, end) trong Javascript
      * Không cần Server làm thay → Giải phóng băng thông NameNode
      * Mỗi mảnh là một khối byte độc lập
    * Bước 3: Đẩy từng Mảnh lên DataNode (Upload Chunk)
      * Client gọi POST /api/chunks/upload (Form-Data)
      * Gửi đúng đến máy chủ primary_node theo Sổ Đỏ
        * Mảnh 0 → gửi thẳng vào Node 3 (port :8003)
        * Mảnh 1 → gửi thẳng vào Node 2 (port :8002)
        * Mảnh N → ... (phân phối tròn Round-Robin)
      * Kèm theo tên các máy sao lưu (secondary_nodes)
  * 2. CHIẾN THUẬT SAO LƯU (REPLICATION)
    * Thuật toán Pipelined Replication
      * DataNode nhận Mảnh → Ghi xuống ổ cứng cục bộ
      * DataNode tự động gọi ngầm POST /api/chunks/replica
      * Chuyển tiếp bản sao sang Node dự phòng (secondary_node)
      * Replication Factor = 2 → mỗi Mảnh tồn tại ở 2 máy khác nhau
      * Client không cần biết → Hoàn toàn tự trị phía Server
    * Chiến lược chọn Node lưu trữ (Load Balancing)
      * NameNode chấm điểm từng máy theo công thức
        * 50% × Tỉ lệ ổ cứng còn trống
        * 30% × (1 − Tải CPU hiện tại)
        * 20% × Điểm mạng (Network Score)
      * Mảnh được phân phối theo Round-Robin trên tập máy đã xếp hạng
      * Máy đầy hoặc quá tải → Bị loại khỏi danh sách ứng viên
    * Cơ chế Tự Phục Hồi (Re-Replication Daemon)
      * Background Daemon chạy ngầm định kỳ
      * Phát hiện Mảnh bị thiếu bản sao (do máy chết)
      * Tự động nhân bản lại sang máy khác còn sống
  * 3. LUỒNG LẤY FILE & XEM TRỰC TIẾP
    * Cách 1: Tải File Thủ Công (Download Pipeline - P2P)
      * Bước 1: Client xin Bản Đồ Tải → GET /api/files/download/init/{file_id}
        * NameNode trả về download_plan
        * Danh sách từng Mảnh + các replica đang sống (active_replicas)
      * Bước 2: Client tự tải từng Mảnh → GET /api/chunks/download/{chunk_id}
        * Gọi thẳng vào IP máy đang giữ Mảnh đó
        * Server trả về Binary (Octet-Stream)
        * Nếu máy A chết → chuyển ngay sang máy B (replica dự phòng)
      * Bước 3: Client ghép lại → Xuất file hoàn chỉnh
    * Cách 2: Xem Trực Tiếp qua S3 Gateway (CDN Stream)
      * Client chỉ cần 1 URL duy nhất → GET /api/files/s3/{file_id}
      * NameNode đóng vai trò Proxy Gateway
        * Tra cứu download_plan nội bộ
        * Kết nối đến lần lượt các DataNode theo httpx AsyncClient
        * Streaming từng luồng byte liên tục (Streaming Response)
      * Trình duyệt nhận về File hoàn chỉnh mà không biết bên trong có nhiều mảnh
      * Tự nhận diện loại file (MIME Sniffing) → Hiển thị video/ảnh inline
  * 4. GIÁM SÁT SỨC KHỎE CỤM (Heartbeat System)
    * Mỗi Node tự động ping định kỳ sang các Node khác
      * Gửi: POST /api/nodes/heartbeat
      * Payload: node_id, dung lượng lưu trữ, CPU load hiện tại
    * NameNode cập nhật bảng trạng thái ClusterNode
      * Máy gửi nhịp tim → Status: ALIVE
      * Máy im lặng quá hạn → Status: DEAD → Bị loại khỏi Placement Plan
    * Kết nối trực tiếp với luồng Upload
      * Máy bị gán DEAD sẽ không bao giờ được chỉ định nhận Mảnh mới
