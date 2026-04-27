# SƠ ĐỒ KIẾN TRÚC HỆ THỐNG LƯU TRỮ PHÂN TÁN (MINI-HDFS)

> [!TIP]
> Bạn có thể xem hình vẽ trực quan bằng cách mở file này trong trình xem Markdown có hỗ trợ Mermaid (như VS Code, GitHub) hoặc copy đoạn code bên dưới dán vào [Mermaid Live Editor](https://mermaid.live).

```mermaid
mindmap
  root((CẤU TRÚC HỆ THỐNG MINI-HDFS))
    1. Tầng Client (Người dùng)
      Thành phần
        Web Dashboard (HTML/JS)
        Swagger UI (API Client)
        Python Test Scripts
      Vị trí
        Máy tính cá nhân trong mạng LAN
      Chức năng
        Gửi yêu cầu khởi tạo Upload/Download
        Thực hiện cắt nhỏ file thành các mảnh (Chunks)
        Gửi mảnh trực tiếp tới các DataNode
    2. Tầng Điều phối (NameNode - Thủ lĩnh)
      Vai trò
        Bộ não điều phối toàn hệ thống (Leader)
      Chức năng chính
        Lập kế hoạch phân bổ (Placement Plan)
        Quản lý khóa tập trung (Distributed Lock)
        Cổng S3 Gateway (Hợp nhất dữ liệu stream)
        Theo dõi sức khỏe (Heartbeat Monitor)
    3. Tầng Dữ liệu (DataNode - Chi nhánh)
      Nhóm A: Node 1 & 2
        Dữ liệu gốc (Primary Chunk)
        Dữ liệu sao lưu (Secondary Replica)
      Nhóm B: Node 3
        Dữ liệu gốc (Primary Chunk)
        Dữ liệu sao lưu (Secondary Replica)
      Dịch vụ
        FastAPI Service quản lý file nhị phân
        SQLite cục bộ quản lý Metadata chi nhánh
    4. Cơ chế Vận hành & Phục hồi
      Bầu cử (Bully Election)
        Tự động bầu Leader mới khi thủ lĩnh sập
      Tự phục hồi (Re-replication)
        Phát hiện mảnh thiếu bản sao và tự tạo bù
      Đồng bộ (Pipelining)
        Tự động đẩy bản sao sang node dự phòng ngầm
    5. Cơ chế kết nối (Mạng LAN/Wifi)
      Giao thức
        REST API (HTTP/JSON)
        Octet-Stream (Truyền tải file nhị phân)
        JWT (Xác thực bảo mật)
      Tính chất
        Tính trong suốt (Transparency)
        Tính chịu lỗi (Fault Tolerance)
        Tính mở rộng (Scalability)
```

---

## Giải thích chi tiết theo phong cách của sơ đồ mẫu:

### 1. Tầng Client (Người dùng)
*   **Thành phần:** Giao diện Web (Dashboard), Swagger UI hoặc các Script Python.
*   **Chức năng:** Khác với hệ thống tập trung, Client ở đây đóng vai trò chủ động trong việc "chặt" file lớn thành các mảnh nhỏ và gửi đi theo mẻ lưới.

### 2. Tầng Điều phối (NameNode)
*   **Vai trò:** Là "Nhạc trưởng" của hệ thống. 
*   **Chức năng:** Không trực tiếp giữ file mà chỉ giữ "Sổ đỏ" (Bản đồ vị trí file). Nó tính toán xem máy nào đang rảnh (CPU thấp, ổ cứng trống nhiều) để chỉ định lưu trữ.

### 3. Tầng Dữ liệu (DataNodes)
*   **Thành phần:** Các Laptop/Server đóng vai trò như các Chi nhánh kho bãi.
*   **Tự trị:** Mỗi chi nhánh có một két sắt riêng (Mysql/Sql Server) để lưu nhật ký mảnh tệp của mình.

### 4. Cơ chế kết nối & Vận hành
*   **Tính chịu lỗi (Fault Tolerance):** Nếu một máy chi nhánh "cành tạch" (hỏng ổ cứng/rút điện), dữ liệu vẫn an toàn vì luôn có ít nhất một bản sao nằm ở máy khác.
*   **Tính mở rộng (Scalability):** Muốn hệ thống mạnh hơn, chỉ cần cắm thêm máy mới vào mạng LAN và khai báo IP, không cần cài đặt lại từ đầu.
