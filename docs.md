# Hướng Dẫn Sử Dụng & Test Hệ Thống Toàn Diện (HDFS Mini)

Hệ thống HDFS Mini đã được lập trình hoàn chỉnh với các thành phần cốt lõi và được bao bọc bằng FastAPI. Các kiến trúc phức tạp như Chunking Pipeline, Heartbeat, Failure Detection, hay Election Bully đều đã được triển khai.

## Môi Trường & Web UI Có Sẵn
Thực tế, hệ thống server đã được đính kèm sẵn Web Dashboard UI:
1. **Trang Dashboard Admin HTML:** Truy cập `http://localhost:8000/` (hoặc IP chạy Node). Giao diện tĩnh này cho phép theo dõi Node ID, IP, các tham số kết nối, và kèm **nút bấm kích hoạt Bầu cử nhân tạo** bằng tay mà không cần gọi API chay.
2. **Web Giao Tiếp File (Swagger Client):** Đặt tại `http://localhost:8000/docs`. Swagger ở đây hoạt động như một ứng dụng Client thứ 3, cho phép Đăng ký/Login nhúng token JWT, và thử thực hiện luồng Upload/Download.

---

## 🔥 1. Cấu Hình Setup Chạy Docker Lên 3 Máy (Wi-Fi/LAN)

Ba máy tính nối vào chung mạng Wi-Fi (Ví dụ: dải IP `192.168.1.x`). Không cần sửa mã nguồn, cài đặt ngay bằng biến môi trường qua PowerShell.

### Laptop 1 (Góc nhìn Máy Nhóm Trưởng - Node 1)
Giả sử IP máy bạn là `192.168.1.100`:
```bash
# 1. Mở PowerShell, trỏ tới thư mục chứa code:
cd D:\HTPT

# 2. Setup định danh và IP Peer cho Docker Compose:
$env:NODE_ID="node1"
$env:MY_IP="192.168.1.100"
$env:PEER_IPS="192.168.1.101:8000,192.168.1.102:8000"

# 3. Chạy Server
docker-compose up --build -d
```

### Laptop 2 & Laptop 3 (Máy Member - Node 2 và 3)
Ví dụ IP là `192.168.1.101` và `192.168.1.102`:
```bash
# Ở Máy Laptop 2:
$env:NODE_ID="node2"
$env:MY_IP="192.168.1.101"
$env:PEER_IPS="192.168.1.100:8000,192.168.1.102:8000"
docker-compose up --build -d
```

---

## 🎯 2. Trình Tự Demo Lên Thầy Cô

### Test 1: Bầu Cử Master và Nhận Dạng Server Chết
1. Truy cập trang `http://localhost:8000` trên một Browser.
2. Bấm Nút **"Manually Trigger Election"**. Lúc này tại Log Terminal, hệ thống chạy cơ chế Bully Broadcast cho ai điểm cao nhất tự xưng vương Leader.
3. Kịch bản Disconnect: Bạn rút mạng Wi-Fi hoặc dừng Docker đột ngột ở Máy 3 (gõ `docker-compose stop`).
4. Xem Server Log của Node 1 hay Node 2 bằng lệnh `docker-compose logs -f`. Sau vài giây Heartbeat rỗng, màn hình sẽ thông báo phát hiện: `Node 3 detected as DEAD` và hệ thống tự hiểu Master đã sập để bầu người khác.

### Test 2: Upload / Download Cắt Chunks
Test được thực hiện trên trang Swagger Docs `http://localhost:8000/docs`:
1. **Bước Auth**: Gọi mở API `/api/auth/register`, rồi login `/api/auth/login` để lấy cặp Token (Paste vào nút Authorize Ổ Khóa phía trên cùng màn hình).
2. **Khởi Trị Gửi File**: Gọi `/api/files/download/init/{file_id}` (hoặc chiều upload). Cục NameNode (Leader) thông minh nó sẽ tính toán rác không gian đĩa ở 3 máy để trả về kế hoạch "Chia làm 4 Chunk, 2 Chunk bỏ máy A, 2 Chunk bỏ máy B".
3. **Pipelining**: Nhét Chunk qua API `/api/chunks/upload`. Ném file vào Node 1, nhưng Code đã viết httpx Pipeline nên ngầm tự động DataNode 1 quăng file đó dự phòng sang DataNode 2 mà lập trình viên không cần đụng tay.

### Test 3: Tranh Giành Khoá Tệp Nhấn Sập Lẫn Nhau Theo Transaction (Multi-client)
Hệ thống cho phép khoá Transaction khi upload y hệt DBMS. Kịch bản tôi đã viết vào `scripts/test_multi_client.py`:
1. Mở Cửa Sổ Terminal riêng, cd thư mục chứa code:
   ```bash
   pip install httpx
   python scripts/test_multi_client.py
   ```
2. Đoạn script Python này giả lập 5 phiên Client ập vào cùng giành giật quyền Lock Exlusive cho tệp file id số `123`.
3. Nhìn màn hình Python Terminal in ra: Hệ thống chặn đứng 4 Client báo `Lỗi HTTP 409 (Conflict)` và nhường duy trì chính xác quyền thao tác cho duy nhất `1 Client` hợp lệ (Chống race-condition đồng thời). Sau đúng 30s khoá đó mới được thả bằng hệ thống Time-To-Live.
