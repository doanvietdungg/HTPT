# TÀI LIỆU HƯỚNG DẪN TÍNH NĂNG & DANH SÁCH API CHI TIẾT (Mini-HDFS)

Tài liệu này đóng vai trò như Sách Trắng (Whitepaper) dành cho Client (hoặc đội ngũ phát triển giao diện Web/App) để giao tiếp với hệ thống Mini-HDFS của chúng ta. Ở đây trình bày toàn bộ các tính năng nội tại, ý nghĩa của các cổng API, và quy trình (Flow) từng bước để gọi API hoàn thành những tác vụ phức tạp như Upload/Download phân mảnh.

---

## PHẦN 1: TỔNG QUAN CÁC CHỨC NĂNG HỆ THỐNG CUNG CẤP

Hệ thống cung cấp một môi trường Tệp Lưu Trữ Hoàn Toàn Phân Tán với độ kháng lỗi cao, bao gồm 6 chức năng lớn:

1. **Chức năng Xác thực Danh tính (Authentication & Authorization):** 
   Cung cấp tính năng đăng ký tài khoản và cấp phát thẻ bài JWT (Json Web Token) có thời hạn. Bất kỳ thao tác nào nhằm thêm/trích xuất tệp đều phải đính kèm thẻ bài này qua chuỗi Bearer Token.

2. **Chức năng Lưu Trữ Phân Mảnh (Storage & Chunking):**
   Hệ thống có khả năng nhận thông tin từ những file khổng lồ và đưa ra **Chiến lược Cắt Mảnh (Placement Plan)**. Các Mảnh (Chunk) này sẽ được ấn định chia đều vào những máy (DataNode) khác nhau trong mạng dựa trên sức khỏe máy đó (Máy nào nhiều ổ trống, ít tải CPU sẽ được đẩy nhiều Mảnh hơn).

3. **Chức năng Tự Động Dự Phòng (Pipelined Replication):**
   Nhằm chống lại thảm họa sập nguồn vật lý 1 máy tính. Hệ thống cung cấp cơ chế: Cứ 1 Mảnh (Chunk) được lưu vào 1 máy, hệ thống tự động sinh thêm 1 bản sao chép tàng hình và luân chuyển sang ổ cứng của máy tính thứ 2 liền kề.

4. **Chức năng Tranh Giành Khoá Tác Vụ (Distributed Mutex Locking):**
   Cung cấp hệ thống Khóa Chống Cạnh Tranh (Concurrency Lock). Cho phép cấp quyền Sinh viên A (Ví dụ: `client_id=1`) được độc quyền sửa file. Các sinh viên B, C sẽ bị kẹt lại hoặc từ chối thao tác (Lỗi HTTP 409 Conflict) chờ tới khi vòng khóa của sinh viên A được giải phóng an toàn.

5. **Chức năng Giám Sát Sức Khỏe (Heartbeat & Failure Detection):**
   Chức năng theo dõi Nhịp tim. Mỗi Node sẽ đều đặn phát tín hiệu sống (Ping pong) bao gồm trạng thái phần cứng của mình đi khắp các máy trong LAN. Nếu 1 máy lặn mất tăm sau thời gian giới hạn $\rightarrow$ Máy đó bị gán nhãn `DEAD` và ngắt khỏi hệ thống giao tiếp.

6. **Chức năng Bầu Cử Thủ Lĩnh Mạng (Bully Algorithm Election):**
   Thủ lĩnh (NameNode) không được chỉ định cứng từ đầu. Chức năng này hỗ trợ khởi tạo đấu trường sinh tử giữa các máy đang rảnh sóng, máy cài đặt `Node_ID` to hơn sẽ chiến thắng, gạt các máy khác lùi về làm Follower (DataNode) để phân tán vai trò.

---

## PHẦN 2: CHI TIẾT CÁC TRƯỜNG DỮ LIỆU (FIELDS) CỦA TOÀN BỘ API

Dưới đây là danh sách chi tiết các Endpoint, giải thích rõ các tham số (Fields) cần truyền vào và dữ liệu trả ra. Đi kèm là Header: `Authorization: Bearer <token>` (Bắt buộc ở các API yêu cầu đăng nhập).

### 🔰 Nhóm 1: Xác Thực Danh Tính User (Auth APIs)

**1. Đăng ký tài khoản**
- **Route:** `POST /api/auth/register`
- **Request Body (JSON):**
  - `username` (string): Tên đăng nhập.
  - `password` (string): Mật khẩu thô (Được mã hóa Bcrypt dưới DB).
  - `full_name` (string): Tên đầy đủ hiển thị.
- **Response (JSON):**
  - `user_id` (string): Mã định danh UUID của User.
  - `username` (string), `full_name` (string).

**2. Đăng nhập**
- **Route:** `POST /api/auth/login`
- **Request Body (JSON):**
  - `username` (string)
  - `password` (string)
- **Response (JSON):**
  - `access_token` (string): Vô cùng quan trọng. Dùng để làm thẻ thông hành.
  - `token_type` (string): "bearer"

---

### 🔰 Nhóm 2: Hệ Thống Cắt Mảnh (Files & Chunks APIs)

**1. Báo cáo Tệp & Nhận Kế Hoạch Cắt (Init Upload)**
- **Route:** `POST /api/files/upload/init`
- **Yêu cầu Header:** Có `Bearer Token`
- **Request Body (JSON):**
  - `file_name` (string): Tên tệp gốc (VD: `test_video.mp4`).
  - `size_bytes` (integer): Kích thước chính xác của tệp tính bằng byte.
  - `logical_path` (string): Đường dẫn ảo danh mục (VD: `/videos`).
- **Response (JSON):**
  - `file_id` (string): ID duy nhất hệ thống cấp cho tệp này.
  - `chunk_size` (integer): Quy chuẩn lưới lọc (VD: `20971520` byte tức 20MB). Client tự viết Javascript dựa trên tỉ lệ này để cắt file gốc.
  - `total_chunks` (integer): Tổng số mảnh.
  - `placement_plan` (array): Danh sách các Object Bản đồ chứa `chunk_index` (số thứ tự mảnh), `primary_node` (IP Node Lưu Mảnh Chính), `secondary_nodes` (Mảng IP Node Dự Phòng Copy).
  - `cdn_url` (string): **[MỚI]** Hỗ trợ S3 Object Storage. Cung cấp URL Public để xem trực tiếp (Stream) liền mạch ngay trên Trình duyệt mà không cần tải Mảnh.

**2. Đẩy Tệp Nhị Phân Gốc (Upload Chunk)**
- **Route:** `POST /api/chunks/upload`
- **Yêu cầu Header:** Có `Bearer Token`
- **Request Body (Form-Data):** (Không phải JSON nữa vì là Form nhị phân)
  - `file_id` (string): ID lấy từ bước Init.
  - `chunk_index` (integer): Số thứ tự Mảnh đang up (Từ 0 đến N).
  - `secondary_nodes` (string): Lấy từ mảng `secondary_nodes` của Bản đồ gộp thành chuỗi cách nhau dấu phẩy (Cực kỳ quan trọng để kích hoạt Pipelining).
  - `file` (File/Binary): Khối Byte nhị phân thật đã bị cắt.
- **Response (JSON):**
  - `status` (string): "success" hoặc "failed"
  - `message` (string): Thông báo Chunk đã được ghi và Replicated thành công.

**3. Xin Lấy Tọa Độ Mảnh Để Trích Tệp (Init Download)**
- **Route:** `GET /api/files/download/init/{file_id}`
- **Yêu cầu Header:** Có `Bearer Token`
- **Path Param:** `file_id` (string).
- **Response (JSON):**
  - `file_name` (string), `size_bytes` (int), `total_chunks` (int).
  - `download_plan` (array): Chứa các Object gồm `chunk_index`, và mảng `active_replicas` (Mảng chứa các IP đang sở hữu Mảnh này và MÁY CHƯA BỊ CHẾT).

**4. Kéo Tệp Vật Lý Về Máy (Download Chunk)**
- **Route:** `GET /api/chunks/download/{chunk_id}`
- **Path Param:** `chunk_id` (string): Ghép theo cú pháp `<file_id>_ck_<chunk_index>`.
- **Response:**
  - Không Trả JSON. Trả thẳng **Octet-Stream Binary (Raw Data)**. Tệp tự động được trình duyệt nặn bắt lấy tên kèm đuôi .jpg / .mp4 gốc nhờ thuật toán Sniffer ngầm.

**5. Đường Dẫn Xem Trực Tiếp CDN (S3 Gateway)**
- **Route:** `GET /api/files/s3/{file_id}`
- **Path Param:** `file_id` (string): Mã định danh tổng của tệp.
- **Response:**
  - Fast-Proxy Streaming toàn bộ các Binary từ các Node ghép lại để trả về 1 Cục Dữ Liệu nguyên vẹn trực tiếp tới thẻ HTML `<img />` hoặc `<video />` trên trình duyệt.

---

### 🔰 Nhóm 3: Khóa Giao Dịch Đồng Thời (Locking APIs)

**1. Giật Khóa Tác Vụ**
- **Route:** `POST /api/lock/acquire`
- **Yêu cầu Header:** Có `Bearer Token`
- **Query Params (URL `?key=value`):**
  - `file_id` (string): ID của tệp đang muốn khóa.
  - `client_id` (string): Tên hoặc ID của thiết bị Client.
  - `lock_type` (Enum): Truyền vào `EXCLUSIVE` (Không ai được vào chung) hoặc `SHARED` (Mọi người được đọc chung nhưng cấm ghi đè).
- **Response (JSON):**
  - `lock_id` (string): Mã số ổ khóa. Client cất mã này đi để giữ thân.
  - `status` (string): "granted"

**2. Gỡ Khóa Trả Không Gian**
- **Route:** `POST /api/lock/release`
- **Yêu cầu Header:** Có `Bearer Token`
- **Query Params:**
  - `lock_id` (string), `client_id` (string).
- **Response:**
  - `status`: Báo "released".

---

### 🔰 Nhóm 4: Đặc Tuyến Phân Tán (Node/Election APIs)

**1. Báo Nhịp Tim (Tự Động Máy Gọi)**
- **Route:** `POST /api/nodes/heartbeat`
- **Query Params:** `node_id`, `capacity` (byte), `used` (byte), `cpu_load` (float 0.0 - 1.0).
- **Response:** 200 OK. (Chỉ dùng ngầm giữ Server).

**2. Bầu Cử Thủ Lĩnh Bằng Lệnh (Manual Election)**
- **Route:** `POST /api/election/start`
- **Lưu ý:** Không cần Body. API này ép buộc Server NameNode tổ chức lại một kì Bầu Cử (Gửi Ping đe dọa các Node khác để cướp Quyền Trị Vì mới).
- **Response (JSON):** `{"message": "Election triggered"}`.

---

## PHẦN 3: WORKFLOW - HƯỚNG DẪN CÁCH SỬ DỤNG LIÊN KẾT CÁC CỤM CHỨC NĂNG

Hệ thống không chạy 1 lệnh là xong như Web đơn khối (Monolithic), một Web Developer xây dựng Client phải nắm chắc Flow nhịp nhàng của các API giống trình tự dưới đây.

### Thực tiễn 1: Workflow "Upload 1 Bức Ảnh 100MB"

1. **Step 1 - Xác Minh:** Client gọi `/api/auth/login`. Lấy về `Token ABC`. Từ giờ ở mọi bước, Header Authorization mặc định kẹp thẻ Bearer mang Token này.
2. **Step 2 - Khắc Khung (Init):** Client gọi `/api/files/upload/init`. Truyền JSON lên `"size_bytes": 104857600` (100MB). Trưởng trạm NameNode tính nhẩm (vì hệ thống `CHUNK_SIZE` là 20MB) nên chia ra làm 5 Mảnh. NameNode quăng về cho Client một Bản Đồ (Gồm tọa độ 5 mảnh 0-4 và danh sách các cục Node giữ mảnh). NameNode chốt bảng ghi lưu vào SQLite Database.
3. **Step 3 - Cưa Đôi Ở Cục (Frontend Tách):** Máy tính Client tự động dùng thẻ HTML FileReader (Hoặc Python Code) chặt tấm ảnh 100MB ra làm 5 đoạn array byte.
4. **Step 4 - Upload Ngầm (Loop):** 
   - Vòng lặp For qua 5 bản đồ kia: Client gọi `/api/chunks/upload` với FormData chứa Array byte của mảnh `0`. Trỏ thẳng mũi tên gửi cho `Node 1` làm culi vác (như bản đồ bảo).
   - Tiếp tục `/api/chunks/upload` với Tọa độ Mảnh `1` trỏ mũi tên quăng vào máy tính `Node 3` làm culi phụ.
   - Khi API gọi xong, Phía Server (Node1 và Node3) tự lo logic Pipelining (tự chuyển tiếp cho nhau), Client không cần bóc tay lần 2 ở mạng!

### Thực tiễn 2: Workflow "Mở Trình Tải Phim Về Nhấn Play"

1. **Step 1:** Lấy `Token` như trên.
2. **Step 2 - Lấy Chìa Khóa Map:** Client gọi `GET /api/files/download/init/{file_id_của_phim}`.
   NameNode phản hồi: *"Có 5 mảnh. Mảnh 0 hiện đang sống an toàn ở Node 2 và Node 3. Mảnh 1 sống ở Node 1."*
3. **Step 3 - Kéo Tải Mảnh Sạch:** Loop lần lượt qua các mảnh:
   - Gọi `GET /api/chunks/download/{chunk_id_mảnh_0}` thẳng ở tên miền của Node 2.
   - Node 2 trả về Byte nhị phân cục bộ. Lưu tạm nó vào bộ nhớ đệm Buffer của Client.
   *(Nếu xui xẻo gọi vào Node 2 mà nó vừa bị Rút Dây Điện sập cmn server, Client thông minh theo Bản Đồ vạch ở Bước 2, chuyển tiếp gọi API Download y hệt trỏ vào Node số 3 để xin cấp cứu mảnh 0 đó).*
4. **Step 4 - Ghép Nối Client:** Ghép đủ 5 Buffer, ghi cắm lại thành File `.mp4` hoàn chỉnh cho người dùng xem.

### Thực tiễn 3: Workflow "Giành Quyền Sửa File Word (Word Lock)"

Tác vụ này phù hợp để làm đồ án chống ghi đè khi làm việc tổ nhóm Online như Google Docs (Distributed Mutex):
1. Sinh viên A (Client 1) mở File Word có `file_id_1`. Client lập tức gọi ẩn ngầm `/api/lock/acquire{EXCLUSIVE}` cho file này.
2. Node Master đồng ý cái Rụp (Vì chưa ai mở). Trạng thái File đó bị khóa với tên cúng cơm thuộc về Sinh viên A.
3. Lúc sau, Sinh viên B (Client 2) ở nhà tọc mạch mở đúng File Word đó, có ý định đòi ghi đè, nó gọi lại `/api/lock/acquire{EXCLUSIVE}`. NameNode Master từ chối lạnh lùng, bắn Lỗi Web `409 Conflict`. Sinh viên B đành phải chờ, file sẽ ở chế độ "Chỉ Đọc (Read mode)".
4. Khi Sinh Viên A ấn "Save & Exit", Client của A tự động kích hoạt `/api/lock/release`. Ổ khóa rơi ra. 
5. Bạn Sinh Viên B ấn nút Ghi lại, lệnh giật ổ khóa cho B thành công. Dữ liệu vĩnh viễn không bao giờ vỡ vụn! Mọi giao dịch được đảm bảo tuyệt đối an toàn trong máy chủ phân tán!
