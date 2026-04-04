# TÀI LIỆU MÔ TẢ KIẾN TRÚC HỆ THỐNG (MINI-HDFS)

## 1. Mục Đích Hệ Thống
Hệ thống **Mini-HDFS** được thiết kế như một cụm server "Tệp Lưu Trữ Phân Tán" dựa trên nguồn cảm hứng từ kiến trúc Hadoop Distributed File System (HDFS). 
Mục đích chính của nền tảng này là giải quyết bài toán: **Làm sao để lưu trữ một tệp dữ liệu lớn cực kì an toàn trên nhiều máy tính độc lập (Nodes), đảm bảo nếu 1 hoặc vài máy (Laptop) bị cháy ổ cứng, rút điện mạng, mất kết nối thì dữ liệu đó vẫn được bảo toàn nguyên vẹn và người dùng vẫn có thể tải về.**

Nền tảng này rất phù hợp để lưu các tệp Multimedia dùng chung cho hệ thống do cơ chế tự rải băng thông ngang (Horizontal Scaling) và băm nhỏ file.

---

## 2. Các Chức Năng Chính Phục Vụ Phân Tán
Hệ thống không chỉ lưu một cục file đơn giản, mà bao gồm 7 module hoạt động song song để vận hành kiến trúc phân tán thực thụ:
- **Authentication & RBAC**: Định danh và cấp quyền khóa tệp qua Json Web Token (JWT).
- **Scoring Chunk Placement**: Tính điểm linh hoạt để đưa ra gợi ý chia file vật lý cho hệ thống, Node nào cấu hình ít RAM hay đang chứa quá nhiều File sẽ bị hạ điểm nhường cho Node khỏe hơn lưu đồ.
- **Pipelining Replication**: Upload không phải chờ tuần tự. Thay vào đó DataNode số 1 vừa lưu file vừa lập tức "truyền miệng" ngầm cho Node số 2 để tạo bản dự phòng.
- **Background Heartbeat**: Nhịp tim được đập kiểm tra mỗi giây (Ping-Pong). Failure Detection cho phép phát hiện sự im lặng của các Node chỉ trong vài giây.
- **Bully Algorithm Election**: Bầu cử thủ lĩnh phân tán. Các Node tự vote cho nhau xem ai lên làm Leader (NameNode) để quản lý Metadata mà không cần chỉ định cứng (Decentralized Master).
- **Multi-client Lock Manager**: Khóa vòng giao dịch (Transaction Lock) tránh trường hợp 2 máy sinh viên cùng gửi file lên đè vào nhau gây hư rỗng tệp.
- **Tự động Re-replication**: Khi một Laptop trong LAN bị tắt máy, hệ thống tự phát hiện tệp tin bị "thiếu bản sao" và gọi nhiệm vụ nội bộ đắp lại bù vào một máy còn sống.

---

## 3. Công Nghệ Theo Từng Thành Phần
- **Framework API (FastAPI - Python):** Xử lý giao tiếp song song. Lý do chọn: Hỗ trợ Async/Await cực mạnh để xử lý Heartbeat/Ping pong đồng thời mà không bị treo API Upload của Client.
- **Persistence Metadata (SQLite + SQLAlchemy):** Lưu lịch sử Chunk File và Trạng thái Server. Lý do chọn: Nhẹ, không cần thiết lập máy chủ MySQL độc lập. Khi Leader rớt, SQLite dễ dàng được Sync sang Leader mới do đặc tính file-based base.
- **Đóng gói & Chạy mạng (Docker & Docker Compose):** Giúp Node dễ dàng bootstrap trong nội mạng LAN bằng các lệnh gán ENV (ví dụ truyền `MY_IP`). Dễ dàng Mount Map (Liên kết) Volume từ ổ cứng vật lý Laptop vào thẳng Container.
- **Giao thức liên lạc nội bộ (HTTPX Client):** Thay vì RPC/gRPC phức tạp, httpx cung cấp Pipeline kết nối giữa Server với Server rất mạnh trong việc đẩy Data Streams (Tệp Chunk).

---

## 4. Cơ Chế Lưu Trữ & Rải Phân Tán Qua Nhiều Node (Topology)

Quy trình vòng lặp lưu trữ được thiết kế như sau:
1. Bạn có 1 file MP4 dung lượng 100MB và có **3 Laptop (Node)** đang ở trạng thái `ALIVE` (có nộp Heartbeat lên Leader).
2. Quy định `Chunk_Size = 64MB`, file bị chẻ làm **2 mảnh (Chunk)** (1 mảnh 64MB và 1 mảnh 36MB).
3. Client bắt đầu hỏi Leader (NameNode): "Mảnh 1 quăng ở đâu?". Leader đánh giá sức mạnh của Laptop 2 và 3 đang rất rảnh (Dung lượng cao). Trả về một **Placement Plan** yêu cầu Primary ưu tiên là Laptop 2, Replication là Laptop 3.
4. Client thẳng đà đẩy Mảnh 1 sang **DataNode ở Laptop 2**.
5. Laptop 2 ghi đoạn byte 64MB vào folder `/data` dưới dạng mã ID (Ví dụ: `file1_ck_0`).
6. Viết thẻ xong, Laptop 2 ngầm mở `httpx.post` ném bản sao chép y hệt của `file1_ck_0` sang cho **DataNode ở Laptop 3**. 
  *(Cơ chế Pipeline này giúp Client không phải up 2 lần ở 2 máy gây tốn băng thông nhánh).*
7. Làm tương tự cho Mảnh 2. Cuối cùng File 100MB được phân bổ đồng đều bản gốc + dự phòng nằm rải rác trên cả 3 Laptops mạng LAN.

---

## 5. Sơ Đồ Use Case (Hành Vi)

Bản sơ đồ dưới mô tả tương tác của Client và sự giao tiếp nội bộ giữa 2 loại Role của Hệ thống Node (Leader NameNode vs Follower DataNode).

```mermaid
usecaseDiagram
    actor "Người Dùng (Client)" as user
    actor "System Daemon" as daemon

    rectangle "Hệ Thống Mini-HDFS" {
        usecase "Đăng ký / Đăng nhập (JWT)" as UC1
        usecase "Upload Khởi Tạo (Lấy Plan)" as UC2
        usecase "Upload Chunk / Ghi File Vật Lý" as UC3
        usecase "Download File Từng Mảnh" as UC4
        usecase "Khóa Tệp (Concurrency Lock)" as UC5
        
        usecase "Replication Pipelining" as UC6
        usecase "Gửi Heartbeat Điểm Danh" as UC7
        usecase "Bầu Cử Bully Election" as UC8
        usecase "Phát Hiện Lỗi & Thu Hồi Re-replicate" as UC9
    }

    user --> UC1
    user --> UC5
    user --> UC2
    user --> UC3
    user --> UC4

    UC2 ..> (Leader NameNode) : Gọi lên để phân công rác đĩa
    UC3 ..> (Follower DataNode) : Lưu trực tiếp xuống ở DataNode Primary
    UC4 ..> (Follower DataNode) : Lôi trực tiếp file từ Data Local lên

    (Follower DataNode) --> UC6 : Tự gửi nền sang DataNode Secondary
    
    daemon --> UC7
    daemon --> UC8
    daemon --> UC9

    UC8 ..> (Mọi Node) : Tranh vị trí NameNode
```
*(Ghi chú: Để xem hình ảnh nét nhất của Sơ đồ trên, bạn có thể copy đoạn code nằm trong cặp ngoặc ````mermaid … ```` dán trực tiếp vào trang [Mermaid Live Editor](https://mermaid.live). Hoặc ứng dụng View Markdown Github sẽ tự Render)*
