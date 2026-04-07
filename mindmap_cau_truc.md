# Mindmap: KIẾN TRÚC HỆ THỐNG LƯU TRỮ PHÂN TÁN (MINI-HDFS)

> Dán nội dung dấu sao bên dưới vào **markmap.js** hoặc **Xmind** để vẽ sơ đồ.

---

* HỆ THỐNG LƯU TRỮ PHÂN TÁN (MINI-HDFS)
  * ĐẶC ĐIỂM CỐT LÕI
    * Cả 3 máy chạy cùng 1 mã nguồn — không có máy nào được cứng nhắc chỉ định trước
    * Vai trò NameNode hay DataNode được xác định ĐỘNG theo 2 cơ chế
      * Cơ chế 1 — Bầu Cử (Bully Election): Node nào có Node_ID lớn nhất trong số các máy đang sống sẽ được bầu làm NameNode chính thức
      * Cơ chế 2 — Theo điểm vào Client: Máy nào tiếp nhận yêu cầu Upload từ Client, máy đó đóng vai NameNode cho phiên giao dịch đó
  * VAI TRÒ NAMENODE (Trung tâm điều phối)
    * Khi nào 1 máy là NameNode?
      * TH1: Máy đó thắng phiên Bầu Cử → Được toàn mạng công nhận là Leader chính thức
      * TH2: Client gọi trực tiếp vào máy đó để Upload/Init → Máy đó tự xử lý như NameNode
    * NameNode làm gì?
      * Lưu Metadata: tên file, kích thước, tổng số mảnh vào DB nội bộ
      * Lập kế hoạch phân phối (Placement Plan): quyết định mảnh nào vào máy nào
      * Đứng làm cổng S3 Gateway: gom mảnh từ các DataNode để trả URL xem trực tiếp
      * Giám sát Nhịp tim (Heartbeat): theo dõi sức khỏe các máy khác
  * VAI TRÒ DATANODE (Chi nhánh lưu trữ)
    * Khi nào 1 máy là DataNode?
      * Khi máy đó thua phiên Bầu Cử → Tự động về làm Follower
      * Khi máy đó nhận lệnh lưu Chunk từ Client hoặc từ NameNode
    * DataNode làm gì?
      * Nhận và lưu Chunk vật lý vào ổ cứng cục bộ (tự trị dữ liệu)
      * Sau khi lưu xong → Tự động đẩy bản sao sang máy dự phòng (Pipelined Replication)
      * Báo cáo sức khỏe định kỳ: CPU, ổ cứng còn trống lên NameNode
      * Phục vụ Client tải Chunk khi được yêu cầu
  * CÁC KỊCH BẢN VAI TRÒ TRONG THỰC TẾ
    * Kịch bản bình thường (Bầu cử xong)
      * Node1 (ID=1) < Node2 (ID=2) < Node3 (ID=3)
      * Node3 thắng cử → Node3 là NameNode
      * Node1 và Node2 → là DataNode
      * Client luôn trỏ vào Node3 để Upload/Init
    * Kịch bản Node3 bị sập
      * Node3 không gửi Heartbeat → bị đánh dấu DEAD
      * Phiên Bầu Cử mới tự động kích hoạt
      * Node2 (ID lớn nhất còn sống) → Lên làm NameNode mới
      * Node1 tiếp tục làm DataNode
      * Hệ thống tiếp tục hoạt động không cần khởi động lại
    * Kịch bản Client gọi thẳng vào Node2 (bypass Election)
      * Node2 vẫn chứa đầy đủ API → Tự xử lý như NameNode cục bộ
      * Lưu Metadata vào DB của Node2
      * Phân phối Chunk sang Node1 và Node3
      * Lưu ý: Node1 không biết về file này (Metadata chỉ ở Node2)
  * TÍNH TỰ TRỊ CỦA TỪNG NHÁNH
    * Mỗi máy có DB riêng (SQLite) — không dùng chung
    * Mỗi máy có thư mục ổ cứng riêng — không dùng chung
    * Mỗi máy có thể phục vụ request độc lập kể cả khi 1 máy khác sập
    * Mỗi máy đều có đủ khả năng làm NameNode hoặc DataNode tùy tình huống
