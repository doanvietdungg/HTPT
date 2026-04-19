# BỘ GIÁO DỤC VÀ ĐẠO TẠO
## HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG
### KHOA HỆ THỐNG THÔNG TIN

---

# BÁO CÁO
# HỆ THỐNG LƯU TRỮ FILE PHÂN TÁN MINI HDFS

**Giáo viên hướng dẫn:** Phan Thị Hà

**Nhóm:** 03

**Sinh viên thực hiện:**
- Đoàn Việt Dũng
- Phạm Tùng
- Lê Huy Hoàng

*…., tháng… năm….*

---

## Mục lục

- **Chương 1: Bài toán và Tổng quan Giải pháp (Solution)**
- **Chương 2: Công nghệ sử dụng (Tech Stack)**
- **Chương 3: Cài đặt và Cấu hình hệ thống (Deployment)**
- **Chương 4: Hiện thực hóa thiết kế và Giải thích Source Code**
- **Chương 5: Kết luận & Hướng phát triển**

---

## Chương 1: Bài toán và Tổng quan Giải pháp (Solution)

### 1.1. Nêu Bài Toán và Vấn Đề Cần Giải Quyết
Trong thời đại bùng nổ dữ liệu số, việc lưu trữ các tệp tin kích thước lớn (như video, dataset, tài liệu lưu trữ) trên một máy chủ (Server) đơn lẻ đối mặt với những rủi ro chí mạng:
1. **Giới hạn không gian cứng (Scalability Limit):** Không gian lưu trữ vật lý của một máy chủ sẽ nhanh chóng cạn kiệt và không thể mở rộng vô hạn một cách linh hoạt.
2. **Điểm mù hệ thống (Single Point of Failure):** Nếu máy chủ duy nhất gặp sự cố phần cứng (hỏng hóc ổ đĩa, mất kết nối), toàn bộ dữ liệu sẽ không thể truy cập, gây gián đoạn hoạt động hệ thống.
3. **Nút thắt cổ chai I/O (Bottleneck):** Khi có số lượng lớn người dùng cùng truy xuất hoặc tải xuống tệp dữ liệu dung lượng cao, băng thông mạng và tốc độ đọc/ghi (I/O) đĩa của một máy chủ sẽ bị quá tải hoàn toàn dẫn đến từ chối dịch vụ (Crash).

### 1.2. Giải Pháp (Solution) của Dự Án
Dự án **Mini-HDFS** là một Hệ thống Tệp Phân tán (Distributed File System) lấy cảm hứng từ cấu trúc phân tán mạnh mẽ của Hadoop HDFS. Dự án giải quyết trọn vẹn 3 bài toán trên thông qua các giải pháp cốt lõi:

- **Cơ chế Phân Mảnh (Client-side Chunking):** Xử lý phân tách tệp nguyên bản định cỡ lớn (GB) thành các khối dữ liệu (Chunk) kích thước nhỏ (ví dụ 20MB) ngay tại Trình duyệt người dùng (Client). Quá trình phân tán lưu trữ các khối này lên rải rác nhiều máy chủ khác nhau giúp phá vỡ giới hạn vật lý phần cứng của thiết bị lưu trữ đơn.
- **Cơ chế Nhân Bản (Replication) & Phục hồi:** Mỗi khối dữ liệu (Chunk) được hệ thống tự động sao chép (copy) và lưu trữ dự phòng sang tối thiểu 2 đến 3 máy chủ khác nhau trong mạng lưới (Replication Factor). Trong kịch bản một thiết bị gặp rủi ro mất dữ liệu, hệ thống vẫn duy trì khả năng trích xuất bản sao nguyên vẹn từ các máy chủ dự phòng.
- **Tính Tự Trị và Kháng Lỗi (Data Autonomy & Fault Tolerance):** Áp dụng thiết kế cơ sở dữ liệu phi tập trung kết hợp giao thức Gossip. Mỗi node tồn tại độc lập. Hệ thống tự động định tuyến lại để bảo vệ độ toàn vẹn tuyệt đối khi phân mảng điều phối chính mất luồng thông tin.

---

## Chương 2: Công nghệ sử dụng (Tech Stack)

### 2.1. Back-end Framework: FastAPI (Python)
- **Công nghệ:** Framework AsyncIO hiệu suất cao phát triển API RESTful bằng Python.
- **Giải quyết bài toán:** Xử lý hàng nghìn kết nối truyền dẫn song song (Concurrent I/O). Việc truyền tải các tập tin phân mảnh qua lại giữa các Node yêu cầu tốc độ đáp ứng cao và không khóa luồng tuyến tính (blocking). Kỹ thuật xử lý bất đồng bộ (`async/await`) của FastAPI khắc phục triệt để tồn đọng tài nguyên bộ nhớ so với cơ chế đa luồng (`Threading`) truyền thống.

### 2.2. Cơ sở dữ liệu: MySQL 8.0 & SQLAlchemy ORM
- **Công nghệ:** Hệ quản trị cơ sở dữ liệu quan hệ mạnh mẽ kết hợp cùng Object-Relational Mapping (ORM) cho Python.
- **Giải quyết bài toán:** SQLAlchemy hỗ trợ xử lý thực thể cấp cao, linh hoạt tích hợp hàm `db.merge()`. Hàm thao tác này xử lý định dạng linh động cho phép dung hợp thông tin giữa các trạm máy chủ (Upsert) mà không gặp trở ngại do xung đột khóa chỉ mục (Index Conflict). SQL Database đảm bảo kiến trúc chịu tải cấp độ doanh nghiệp so với kiến trúc tệp phi phẳng cục bộ.

### 2.3. Trình Quản Lý Môi Trường Khối: Docker & Docker Compose
- **Công nghệ:** Nền tảng ảo hóa đóng gói ứng dụng trong vùng chứa (Containerization).
- **Giải quyết bài toán:** Đặc thù của hệ thống phân tán là yêu cầu triển khai đồng nhất mã nguồn lên nhiều trạm máy chủ (Nodes) vật lý độc lập. Docker mang lại năng lực đóng gói (Packaging) trọn bộ môi trường thực thi: Từ phiên bản hệ điều hành nhân Linux, thư viện Python, ứng dụng kết nối gốc đến cả tham số mạng nội bộ vào trong một tệp ảnh (Image) thống nhất.
- **Lợi ích thực tế:** Khi cần nâng cấp (Scale) mạng lưới từ 3 Node lên 100 Node, quản trị viên chỉ cần chuyển giao file tiêu chuẩn `docker-compose.yml`. Mọi thao tác cấu hình phức tạp từ cài đặt thư viện phần cứng đều bị triệt tiêu hoàn toàn. Khắc phục vấn đề "Hoạt động tốt trên máy tôi, lỗi trên máy chủ" (It works on my machine problem) giữa các thiết bị khác biệt.

### 2.4. Front-end: HTML/CSS & Vanilla JS (Javascript thuần tự nhiên)
- **Công nghệ:** Sử dụng Javascript gốc áp dụng `Fetch API` bất đồng bộ và `File API` hệ thống.
- **Giải quyết bài toán:** Cắt file theo cấp độ tập phân nhị phân (Byte-level slicing) ở luồng Trình duyệt tại Client, giải phóng áp lực RAM (Bộ nhớ ngắn hạn) tối đa cho Server trong quá trình Upload.

---

## Chương 3: Cài đặt và Cấu hình hệ thống (Deployment)

Hệ thống cung cấp tính linh hoạt hỗ trợ cấu hình từ môi trường giả lập (Simulation) ra cụm thực tế liên máy chủ (Production).

### 3.1. Cài đặt triển khai Cục Bộ (Demo/Test Mode)
Thông qua kịch bản thiết lập `docker-compose-test.yml`, tiến trình khởi tạo ảo hóa 3 Node Container và 3 Container MySQL định danh riêng biệt trên duy nhất PC nội dung. Đây là lựa chọn tối giản phục vụ việc mô phỏng thực hành và đồ án.

**Câu lệnh thực thi:**
```bash
docker-compose -f docker-compose-test.yml up --build -d
```
Giao thức tương tác Web UI khởi tạo theo luồng địa chỉ nội hạt:
- Cổng dịch vụ Node 1: `http://localhost:8001/ui`
- Cổng dịch vụ Node 2: `http://localhost:8002/ui`
- Cổng dịch vụ Node 3: `http://localhost:8003/ui`

### 3.2. Cấu hình Môi Trường Mạng Diện Rộng (Production Mode)
Dùng biểu mẫu `docker-compose.yml`. Áp dụng khi liên kết nhiều Máy chủ (Thiết bị) vật lý nội vi trong mạng LAN với IP đích định danh khác biệt.

**Cách thực hiện:** Thiết lập môi trường tham số riêng biệt trong tệp `.env` tại mỗi máy nhằm mở cơ chế định tuyến.
Ví dụ đối với máy trạm 1 (192.168.1.101):
```env
NODE_ID=node1
MY_IP=192.168.1.101
PEER_IPS=192.168.1.102:8000,192.168.1.103:8000
API_PORT=8000
```
Khởi chạy dịch vụ theo tiêu chuẩn chung:
```bash
docker-compose up --build -d
```

---

## Chương 4: Hiện thực hóa thiết kế và Giải thích Source Code

Phần tập trung giải phẫu 7 kỹ thuật kiến trúc P2P then chốt làm nên hiệu năng và đảm bảo khả năng kháng lỗi tuyệt đối của phần mềm. Nội dung diễn giải cơ chế vận hành kèm theo đối chiếu Mã Nguồn (Source Code) trọng yếu.

### 4.1. Thiết Kế Cơ Sở Dữ Liệu Phân Tán (Domain Models)
Hệ thống sử dụng các Error-Tolerant Models (Cấu trúc chống lỗi) thay vì khóa ngoại cứng, nhằm đảm bảo khi dữ liệu được phân mảnh rải rác, các Node vẫn có thể lưu trữ cục bộ độc lập. Dưới đây là ý nghĩa các thực thể cốt lõi:

**1. Bảng `ClusterNode` (Nút mạng lưới)**
Lưu trữ định danh và mức độ khả dụng của các máy chủ trong chùm:
- `node_id`: Mã định danh máy chủ phân tán (vd: `node1`, `node2`).
- `host` & `port`: IP và Lĩnh vực Truy cập mạng TCP/IP.
- `status` (`ALIVE`, `DEAD`): Trạng thái sống/chết được định tính qua giao thức Heartbeat.
- `storage_capacity_total` & `used`: Thông số không gian vật lý lưu trữ ổ đĩa, biến số quan trọng phục vụ hệ số Cân bằng Tải I/O tại mục tiếp theo.

**2. Bảng `FileEntry` (Siêu Dữ Liệu Tệp Gốc)**
Bản đồ định tuyến và thuộc tính tập tin nguyên mẫu:
- `file_id`: Khóa chính định dạng cấu trúc UUID.
- `size_bytes`: Tổng dung lượng thực toàn bộ File.
- `chunk_size`: Kích thước kỹ thuật của mỗi phần cắt quy định ở chuẩn (thường bằng 20MB).
- `total_chunks`: Số lượng cấu hình mảng phân mảnh tổng thiết lập.
- `replication_factor`: Đặc tả số lượng DataNodes ưu tiên lưu trữ làm dự phòng nhân bản.

**3. Bảng `ChunkEntry` (Thực Thể Phân Mảnh)**
Ghi nhận định dạng vòng đời của một khối Chunk nhị phân hình thành từ Tệp Gốc:
- `chunk_id`: Mã định danh khối nhị phân.
- `file_id`: Chuỗi tham chiếu ngược (Soft-link) tới FileEntry sinh ra tương đương.
- `chunk_index`: Vị trí toán học chỉ mục cho định tuyến quá trình gỡ ghép Download trên nền Browser.
- `primary_node_id`: Dấu vết thiết bị nhận I/O ban đầu từ Client khởi chạy Pipeline.

**4. Bảng `ChunkReplica` (Thực Thể Bản Sao Vật Lý - I/O Node)**
Quản trị vị trí xuống tận Track/Sector của phần vùng lưu trữ File System trên địa phương vật lý:
- `replica_id`: Định danh bản chụp cắt lớp mảnh Chunk.
- `chunk_id`: Chuỗi tham chiếu Soft-link định hướng lại ChunkEntry (Không sử dụng Constraint).
- `node_id`: Node Machine nắm giữ file nhị phân đính kèm dưới nền hệ thống vật lý.
- `stored_path`: Vị trí con đường phân phối File trên HDD/SSD (VD: `/app/data/chunks_storage/XYZ.bin`).

### 4.2. Kịch Bản Sử Dụng (Usecase): Trình Tự Bắt Tay (Handshake) Giữa Client & Server Khi Upload
Để hệ thống hóa cách các module phối hợp hoạt động, dưới đây là phiên bản bóc tách từng luồng Request/Response giữa thiết bị Client và cụm Server:

**Bước 1: Client khởi tạo tín hiệu (Init Upload)**
- **Hành động:** Client đo dung lượng File và gọi API `POST /api/files/upload/init`.
- **Payload gửi đi:** JSON chứa các thông số định dạng cơ bản: `{"file_name": "video.mp4", "size_bytes": 104857600}` (100MB).
- **Hành vi của Backend (NameNode):** 
  - Tính toán số lượng khối (Chunks) cần phải cắt tách dựa trên biến cấu hình `CHUNK_SIZE` (ví dụ 20MB/chunk).
  - Khảo sát các Node đang sống (`ALIVE`) và ra quyết định thuật toán cân bằng tải (Chỉ định IP nào sẽ lưu Chunk nào).
- **Dữ liệu trả về cho Client:**
  ```json
  {
      "file_id": "uuid-1234",
      "total_chunks": 5,
      "chunk_size": 20971520,
      "placement_plan": [
          {"chunk_index": 0, "primary_node": "192.168.1.101", "secondary_nodes": ["192.168.1.102"]},
          {"chunk_index": 1, "primary_node": "192.168.1.102", "secondary_nodes": ["192.168.1.103"]},
          ...
      ]
  }
  ```
  *Ý nghĩa các trường cấu trúc trong Bản đồ phân phối (Placement Plan):* 
  - **`chunk_index`:** Số thứ tự định danh lớp cắt logic của file (0, 1, 2...). Trình duyệt tại Client dựa vào chỉ số này để tính toán byte sẽ cắt, và lúc Download ráp lại tránh bị nhầm thứ tự.
  - **`primary_node`:** Địa chỉ IP của Máy Chủ Tuyến Đầu phân bổ riêng cho khối này. Client bắt buộc phải gọi API POST đẩy cục Chunk thành phẩm vào đúng đích danh thiết bị này.
  - **`secondary_nodes`:** Danh sách IP của các Máy Chủ Hậu Phương (Nhân bản dự phòng). **Lưu ý:** Client *không* gửi tệp trực tiếp vào đây. Client chỉ kẹp danh sách này vào Form Data gửi cho `primary_node`. `primary_node` sẽ tự mang trọng trách đọc danh sách này để cấu hình luồng Đồng Bộ Tuyến Tính ngầm ở Bước 2.

**Bước 2: Phân mảnh và Truyền tải dữ liệu đa luồng (Upload Chunks)**
- **Hành động của Client:** Trình duyệt sử dụng hàm `file.slice()` để phân rã tập tin ban đầu thành các khối nhị phân độc lập dựa trên kích thước `chunk_size`.
- **Giao tiếp API:** Client thực hiện các cuộc gọi HTTP `POST http://<primary_node>/api/chunks/upload` dưới định dạng `multipart/form-data`. Gọi độc lập cho phân mảnh, đẩy nó đến đúng IP được xác định ở trường `primary_node`. Đính kèm trong request là danh sách mảng `secondary_nodes` do NameNode cung cấp.
- **Hành vi xử lý của Máy chủ Lớp Đầu (Primary Node - Ví dụ: Máy 101):** 
  1. Ghi nhận trực tiếp chuỗi nhị phân (Bytes) vừa nhận được vào thư mục đĩa cứng vật lý của nó.
  2. Ghi nhận đối tượng siêu dữ liệu vào bảng `ChunkReplica` trong cơ sở dữ liệu MySQL nội bộ xác nhận việc sở hữu thành công.
  3. Lập tức trả về Response HTTP 200 cho Client: `{"status": "ok", "message": "Chunk saved"}` để Trình duyệt giải phóng biến bộ nhớ.
  
**Bước 3: Giao tiếp Nhân bản Nội bộ (Pipeline Replication: Máy 101 -> Máy 102)**
- **Chuẩn bị dữ liệu:** Ngay sau khi phản hồi Client, Máy 101 khởi chạy một luồng xử lý bất đồng bộ (Background Task). Nó truy xuất lại tệp mã nhị phân vừa lưu trên ổ cứng cục bộ của nó, nắn lấy danh sách địa chỉ `secondary_nodes` (Máy 102) mà Client gửi kèm ban nãy.
- **Thực thi gọi chéo:** Máy 101 đóng vai trò như một Client, sử dụng thư viện `httpx` xây dựng một gói Request chứa File nhị phân đó, đính kèm `chunk_index` và gọi sang API nội bộ `POST http://192.168.1.102:8000/api/chunks/replica`.
- **Xử lý tại Máy 102 (Secondary Node):** Máy 102 tiếp nhận luồng dữ liệu từ Máy 101. Tương tự như Máy 101, nó lưu phân mảnh vật lý xuống ổ đĩa cục bộ của nó, và cũng ghi một bản `ChunkReplica` vào cơ sở dữ liệu MySQL của định danh mình. Tuy nhiên, Máy 102 chấp nhận lưu trữ vùng nhị phân mồ côi này mà không cần truy vấn tham chiếu cấu trúc Gốc (`FileEntry`). *(Ví dụ: Máy 102 chứa Chunk số 0 của tệp "Avengers.mp4", nhưng nó vẫn chấp nhận lưu đĩa dẫu cho CSDL của nó chưa từng biết tới thông tin tệp "Avengers.mp4" do Client chưa từng khai báo cho Máy 102).*

**Bước 4: Hoàn tất tiến trình (Client Side Finish & Metadata Sync)**
- Khi Client nhận đủ toàn bộ Response `200 OK` từ các Primary Nodes. Giao diện hiển thị Tiến trình Upload 100%. 
- Đồng thời ở dưới hạ tầng, chức năng đồng bộ nền ngang hàng (Gossip Protocol) luân phiên chạy chéo giữa các Server (Mục 4.7). Chức năng này tự động hợp nhất các bảng dữ liệu khiếm khuyết cho nhau, mang lại tính năng cấu trúc File đồng bộ hoàn chỉnh trên tất cả các mạng lưới.

### 4.3. Phân Mảnh Tệp Tại Trình Duyệt (Client-Side Chunking)
- **Vấn đề (Pain point):** Khi người dùng tải lên tệp tin dung lượng cực lớn (GB), hệ thống phân tán sẽ đối diện nguy cơ quá tải không gian RAM (Buffer Overflow) và tắc nghẽn băng thông.
- **Giải Pháp (Solution):** Xử lý phân mảnh tệp (Chunking) ngay tại thiết bị khách (Client Browser) trước khi truyền đi. Mỗi khối dữ liệu nhỏ (ví dụ 20MB) được truyền tải tuần tự dưới dạng luồng HTTP phụ độc lập, cho phép hệ thống chỉ khôi phục nguyên vẹn lại duy nhất khối dữ liệu lỗi mạng thay vì tải lại toàn bộ.
- **Giải Thích Code (`frontend/js/app.js`):**
  ```javascript
  // Lặp qua dung lượng vật lý của File, gia số theo biến CHUNK_SIZE
  for (let start = 0; start < file.size; start += placement.chunk_size) {
      
      // Chặn biên: Đảm bảo điểm kết thúc (end) không vượt kích thước định mức
      let end = Math.min(start + placement.chunk_size, file.size);
      
      // Trích xuất dữ liệu nhị phân (Blob) qua File API
      // Khối lệnh bỏ qua việc đẩy toàn bộ dung lượng File vào bộ nhớ thiết bị
      let chunkBlob = file.slice(start, end);
      
      let formData = new FormData();
      formData.append('file', chunkBlob);
      
      // Truyền tải bất đồng bộ (AJAX) khối dữ liệu tới đích định tuyến
      uploadPromises.push(uploadChunk(targetUrl, formData));
  }
  ```

### 4.4. Thuật Toán Cân Bằng Tải DataNode (Placement Plan)
- **Vấn đề:** Để tránh dồn luồng truy cập IO cục bộ lên một máy chủ đơn lẻ thay vì dàn trải, hệ thống cần cơ chế điều phối không gian dữ liệu đồng đều qua cụm DataNodes.
- **Giải pháp:** Khi luồng Upload kích hoạt, Primary NameNode đánh giá lại điểm số khả dụng (Score) của toàn bộ thiết bị đang sống `ALIVE`, ưu tiên phân phái truy xuất dữ liệu tới các máy chủ thừa sức chứa lớn nhất kết hợp phương pháp xoay vòng tròn.
- **Giải Thích Code (`app/services/metadata.py` - hàm `generate_placement_plan`):**
  ```python
  # (1) Tính điểm dựa vào tài nguyên ổ cứng thực:
  def score_node(n: ClusterNode):
      free_space = n.storage_capacity_total - n.storage_capacity_used
      return free_space * n.network_score

  # Sắp xếp khả năng đáp ứng giảm dần dựa vào tài nguyên
  valid_nodes.sort(key=lambda x: score_node(x), reverse=True)
  
  # (2) Suy Giảm Đáp Ứng (Graceful Degradation)
  # Nhằm duy trì tính sẵn sàng nếu giới hạn tham số số lượng bản sao đòi hỏi 3 
  # nhưng lượng Node thực tế trong mạng khả dụng chỉ là 2. Lệnh Tự động cấu trúc điều chỉnh
  effective_rf = min(replication_factor, len(valid_nodes))

  # (3) Phân bổ xoay vòng thuật toán Round-Robin 
  for i in range(total_chunks):
      # Thao tác chia lấy dư nhằm san bằng tần suất 
      primary_idx = i % len(valid_nodes)
  ```

### 4.5. Cơ Chế Thu Thập Lõi Input Cho Cân Bằng Tải (Asynchronous Capacity Polling)
- **Vấn đề (Kết nối với Mục 4.3):** Hàm thuật toán Cân bằng tải `generate_placement_plan` (ở Mục 4.3) yêu cầu các biến số thời gian thực (`ALIVE`, `storage_capacity_used`). Ngược lại, CSDL phi tập trung của NameNode mặc định không thể tự biết ổ cứng của hai DataNode ở xa còn trống bao nhiêu. Nếu ứng dụng gài lệnh đo đĩa vào ngay chu trình luồng Upload File, hệ thống sẽ rơi vào trạng thái thắt cổ chai cục bộ (Blocking I/O).
- **Giải pháp:** Tách biệt nghiệp vụ khảo sát ra khỏi luồng xử lý File. Bất kỳ Backend Node nào cũng sẽ khởi chạy ngầm một Trình nền Heartbeat (Nhịp Tim). Trình nền này giao tiếp trực tiếp với hệ điều hành để đo ổ cứng, sau đó liên tục phát sóng UDP/HTTP trạng thái đĩa cứng của chính máy mình tới các anh em trong chùm.
- **Giải Thích Code (`app/services/heartbeat.py`):**
  ```python
  while True:
      # Lệnh gọi hàm cốt lõi của Hệ Điều Hành để đo đạc dung lượng vật lý chính xác
      total, used, free = shutil.disk_usage(settings.DATA_DIR)
      
      async with httpx.AsyncClient() as client:
          for peer in peers:
              # Định kỳ bắn sóng API tới các Server khác nhằm khai báo 2 yếu tố:
              # 1. "Tôi vẫn sống" (Cập nhật cột last_heartbeat -> status: ALIVE)
              # 2. "Ổ cứng tôi đã dùng X GB" (Cập nhật cột storage_capacity_used)
              await client.post(url, params={"host": settings.MY_IP, "used": used...})
              
      await asyncio.sleep(1) # Chu kỳ làm mới 1 Giây (Thời gian thực)
  ```
  => *Nhờ cơ chế bóc tách luồng ngầm này, Backend của NameNode luôn thụ động sở hữu sẵn bộ dữ liệu Input biến đổi liên tục, giúp hàm Placement Plan ở Mục 4.3 hoạt động chia Chunk mượt mà dẫu cho có hàng chục Server ngắt kết nối hay đầy rác đột ngột.*

### 4.6. Đồng Bộ Dữ Liệu Nhân Bản (Pipeline Replication)
- **Vấn đề:** Bắt buộc End-user phải chuyển tải đa luồng cùng một mảnh File sang cả 3 Server là lãng phí tài nguyên Băng Thông Ngoại vi.
- **Giải pháp:** Áp dụng luồng vận chuyển tuyến tính ngầm ở lớp Server (Backend to Backend Pipelining). Client truyền dữ liệu cục bộ duy nhất vào Máy chủ Tiền Phương (Primary Node). Khi I/O Write thành công trên đĩa, Primary Node tạo luồng HTTP Async tiếp sức luân chuyển bản sao dự phòng ngang hàng trong LAN Server.
- **Giải Thích Code (`app/api/chunks.py` - hàm `upload_chunk`):**
  ```python
  # Bước 1: Ghi xuất IO đĩa tại Primary Node, trả phản hồi giải tỏa vòng đời cho Trình Duyệt Client
  with open(file_path, "wb") as buffer:
      shutil.copyfileobj(upload_file.file, buffer)
  db.commit()

  # Bước 2: Khởi tạo luồng sao chép (Pipeline Background Forwarding)
  if secondary_nodes:
      for idx, next_node in enumerate(nodes):
          # Lệnh await truyền tải dữ liệu hệ thống mà không khóa dòng Response của Web
          success = await forward_chunk_to_replica(...)
  ```

### 4.7. Định Tuyến Ràng Buộc Dữ Liệu Ngầm Hóa (Data Autonomy Bypass)
- **Vấn đề:** Luồng nhân bản phi tiếp xúc ở (4.4) phát sinh rào cản từ mô hình Relational DB. Khi máy phụ tiếp nhận Binary File, Database chưa nắm Metadata tương ứng nên SQL báo lỗi `IntegrityError` từ chối Write nếu thiết lập `ForeignKey`.
- **Giải pháp:** Rời rạc hóa khóa vật lý, sử dụng kỹ thuật định tuyến linh hoạt UUID (Soft Link). Chức năng giám định Metadata được chuyển lên mức RAM thay vì cứng ngắt ở SQL. Tối đa hóa đặc quyền ghi độc lập đối với các mảng Server Cục bộ.
- **Giải Thích Code (`app/models/domain.py` - Lớp Thực Thể ChunkReplica):**
  ```python
  class ChunkReplica(Base):
      __tablename__ = "chunk_replica"
      # Từ bỏ Ràng buộc SQL Constraints: ForeignKey("chunk_entry.chunk_id")
      # Trực tiếp ứng dụng chuỗi định danh, bù đắp tốc độ khớp dữ liệu bằng Indexed B-Tree 
      chunk_id = Column(String(100), index=True)
  ```

### 4.8. Kiểm Soát Tính Bền Vững (Failure Detection) & Hội Tu Không Bền Kháng P2P (Gossip Protocol)
- **Vấn đề - Hiệu Ứng Bất Cập:** (A) Master Node định tuyến nhầm vào thiết bị đã rớt nguồn gây Lập tức lỗi Network Timeout. (B) Ở mục 4.5, Slave Machine lưu dữ liệu nhưng Metadata trống. NameNode "chết nguồn", Slave có Data ngụy trang không thể truy xuất dưới dạng Cấu trúc Phẳng cho End-User (Inconsistent State).
- **Giải pháp:** Chấm dứt định tính bằng module Heartbeat 1 Giây; Ứng dụng Giao Thức Rỉ Tai Xã Hội Tính - Ngang hàng Gossip Protocol (P2P), định kỳ thiết bị lấy tệp MetaData máy khác áp nhập cơ chế UPSERT thông minh loại bỏ sai số.
- **Giải Thích Code (Trừ Đứt Gãy Heartbeat):**
  ```python
  # In app/services/heartbeat.py
  for node in nodes:
      delta = (now - node.last_heartbeat).total_seconds()
      # Phán xét ngừng hoạt động nhằm ngắt định tuyến File tới điểm chết.
      if delta > settings.ELECTION_TIMEOUT and node.status == "ALIVE":
          node.status = "DEAD" 
  ```
- **Giải Thích Code (Hồi quy Eventual Consistency bằng Gossip - `app/services/gossip.py`):**
  ```python
  async def sync_metadata_daemon():
      while True: # Vòng lặp ngầm chạy vô hạn 
          for peer in peers:
              resp = await client.get(f"http://{peer}/api/nodes/metadata/dump")
              data = resp.json()
              
              # Tương tác ORM nhúng cấu trúc JSON sang Database Object Model
              for f_data in data.get("files", []):
                  validated = FileEntryDump(**f_data).dict()
                  
                  # Kỹ thuật cốt lõi Merge Database của SQLAlchemy: 
                  # Tự động hóa cập nhật toàn bộ trạng thái mà bỏ qua tình huống 
                  # Nổ khóa chính do sự cố trùng lặp bản ghi phát sinh (Upsert).
                  db.merge(FileEntry(**validated)) 
                  
              db.commit()
          await asyncio.sleep(10) # Chu kỳ luân chuyển 10 giây
  ```

### 4.9. Cổng Chuyển Tiếp Tải Xuống (S3 Object Streaming Gateway)
- **Vấn đề:** Khi dữ liệu bị chia nhỏ thành hàng trăm mảnh nhị phân nằm rải rác trên nhiều máy chủ, làm thế nào để Client (người tải về) có thể gộp file lại một cách mượt mà như đang tải một File liên tục thống nhất mà không làm sập bộ nhớ đệm (RAM) của Server trung gian?
- **Giải pháp:** Xây dựng Module Download Generator. NameNode truy vấn "Bản đồ phân phối" (Download Plan) lấy tập hợp IP cục bộ của các DataNode đang giữ mảnh. Thay vì nén lưu vào RAM, Proxy sử dụng toán tử Generator tạo đường ống hẹp ghép nối liên tục Streaming Bytes từ các DataNode trả thẳng luồng về cho Trình duyệt người dùng (Tương tự Streaming của Youtube hay AWS S3).
- **Giải Thích Code Trích Xuất File (`app/api/files.py` - api `/s3/{file_id}`):**
  ```python
  @router.get("/s3/{file_id}")
  async def s3_object_gateway(file_id: str, db: Session = Depends(get_db)):
      # 1. Truy vấn CSDL gọi Bản đồ (IP) đang nắm giữ các rải mảnh Chunk 0, 1, 2...
      plan = get_file_download_plan(db, file_id)
      
      # 2. Xây dựng Trình Tạo Byte Liên tục (Async Generator)
      async def stream_chunks():
          async with httpx.AsyncClient() as client:
              # Quét vòng lặp nối tiếp từng mảnh theo chuẩn chunk_index đúng tuyến tính
              for chunk in plan.chunks:
                  # Rút trích tự động lấy IP DataNode Ưu tiên chịu tải (Status = ALIVE)
                  target_host = chunk.node_ips[0] 
                  url = f"http://{target_host}/api/chunks/download/{chunk.chunk_id}"
                  
                  # 3. Yêu cầu tải Byte băng thông thấp thông qua Streaming
                  async with client.stream("GET", url) as response:
                      if response.status_code == 200:
                          # Bơm luồng nhị phân nhỏ giọt cực nhe thu được từ DataNode 
                          async for content in response.aiter_bytes():
                              yield content
                              
      # 4. FastAPI StreamingResponse đóng gói luồng ảo tự động ghép nối mượt mà
      # Media_type được cấu hình giả lập giống ngõ AWS S3 để Browser kích hoạt tải tệp nhị phân gốc
      return StreamingResponse(stream_chunks(), media_type="application/octet-stream")
  ```
**Giải thích Chu trình hoạt động (Step-by-step):**
1. **Định vị Cấu trúc:** Khi người dùng mở View/Download, NameNode rà soát đối tượng DB chỉ điểm các DataNode khả dụng chứa từng mảnh `chunk_0`, `chunk_1`.
2. **Kích hoạt Generator Vô Hạn `stream_chunks()`:** Vòng lặp tuần tự hỏi thăm từng DataNode một. Lấy DataNode 1 rút `chunk_0` (mảnh đầu của File), dùng định tuyến xuất toán tử `yield` phóng Byte trực tiếp như vòi nước chảy thẳng vào kênh đáp trả HTTP hướng tới Client. Đạt độ trễ tiệm cận ZERO.
3. **Ghép Nối Bypass & Giải Phóng Biến Memory:** Nhờ hai hàm nền cốt lõi `aiter_bytes()` phối hợp với `StreamingResponse()`, ứng dụng hoạt động không khác gì một "Ống Rơ le Phân phối". Sức hút Byte phân luồng từ DataNode sẽ được thoát nước và ngấm xả ngay lập tức xuống Client. Hệ tiêu dùng được lợi ích to lớn: Kể cả File đích thị có dung lượng lên đến hàng trăm Gigabytes, NameNode làm Gateway cũng chỉ tiêu tốn đỉnh điểm chưa đầy 50 Megabytes RAM để duy trì tiến trình Bypass luồng đường ống này bảo vệ kiến trúc siêu vững!

### 4.10. Cơ Chế Khóa Phân Tán (Distributed Locking & Concurrency Control)
- **Vấn đề Xung đột Dữ liệu (Concurrency):** Trong kiến trúc hệ thống phân tán đa giao dịch, nhiều thao tác có thể xảy ra đồng thời trên một tài nguyên. Ví dụ: Người dùng A đang thực thi tiến trình tải xuống (Read) một tập tin dung lượng cao mất 10 phút, ở phút thứ 5, Người dùng B phát động lệnh xóa đè (Delete/Write) tập tin đó. Hệ quả nếu không kiểm soát: Tiến trình A đọc vào chuỗi dữ liệu hỏng dẫn đến hỏng File, hoặc trạng thái CSDL bị sập (Data Corruption).
- **Giải pháp:** Ứng dụng Quản trị Cơ chế Khóa Phân Tán (Distributed Locking) quản lý độc lập từng mã tham chiếu `file_id`. Chia thành hai cấp độ cấm:
  - **Khóa Chia Sẻ (SHARED):** Dành cho tiến trình cấp quyền Truy cập/Tải xuống. Hệ thống ưu việt cho phép vô số luồng hoạt động song quyền cùng sở hữu loại khóa này (10 người cùng tải file không lỗi). Tuy nhiên, khi File đang dính Khóa SHARED, bất kỳ hành vi Yêu cầu Ghi/Xóa (EXCLUSIVE) nào xuất hiện lập tức sẽ bị chặn lại và từ chối.
  - **Khóa Độc Quyền (EXCLUSIVE):** Khởi tạo khi có API thao tác Xóa, Ghi Đè, Đổi đường dẫn tệp. Nắm vai trò phong tỏa hệ sinh thái toàn cục nội hạt của File. Sẽ không một Client nào được cấp Khóa đọc, hoặc Khóa ghi đè nào khác phát sinh. Tránh sinh ra rác nhị phân.
- **Giải Thích Code (Bóc tách logic Lõi `app/services/lock.py`):**
  ```python
  def acquire_lock(db: Session, file_id: str, client_id: str, user_id: str, lock_type: str):
      
      now = datetime.datetime.utcnow()
      
      # 1. Cơ Chế Dọn Rác & TTL (Time To Live): 
      # Cấp khóa chỉ sống sót 30 Giây. Chống rủi ro "Sập Máy Trạm" (Client Disconnect)
      # Ví dụ: Máy A vừa gọi Khóa đè thì Mất Mạng hoàn toàn, không nhả API Release.
      # Hàm tự động Check TTL sẽ càn quét nhả khóa chết, ngăn hệ thống khóa vĩnh viễn tệp.
      expired_locks = db.query(FileLock).filter(FileLock.expire_at < now).all()
      for l in expired_locks:
          l.status = "RELEASED"
          
      # Lấy danh sách Khóa đang cắm ở tệp này
      active_locks = db.query(FileLock).filter(FileLock.file_id == file_id, FileLock.status == "ACQUIRED").all()
      
      # 2. Xử Lý Phân Cấp Khóa Chéo
      if lock_type == "EXCLUSIVE":
          # Áp dụng Độc Quyền nhưng đang có luồng Download -> Bão lỗi Cấm 409
          if len(active_locks) > 0:
              raise HTTPException(status_code=409, detail="File is currently locked")
              
      elif lock_type == "SHARED":
          # Áp dụng Đọc nhưng có Luồng đang cắm Cờ Rạch Đĩa (EXCLUSIVE) -> Dừng đáp ứng Mạng
          for l in active_locks:
              if l.lock_type == "EXCLUSIVE":
                  raise HTTPException(status_code=409, detail="File is exclusively locked for writing")

      # 3. Trao ấn phong Khóa (ACQUIRED) và cộng giờ sống 30s
      new_lock = FileLock(lock_type=lock_type, expire_at=now + datetime.timedelta(seconds=30)...)
      db.add(new_lock)
      return new_lock
  ```

---

## Chương 5: Kết luận & Hướng phát triển

### 5.1. Kết Luận
Dự án đã giải phẫu thành công một Hệ Thống Đồng bộ Tệp Phân Tán thực thụ vận hành dưới lớp mạng Ảo Microservice riêng biệt dựa trên lý thuyết thiết kế Apache HDFS. 
Các tắc nghẽn đặc hữu trong cơ chế mạng phi tập trung đã được giải mã triệt để bằng sự nhịp nhàng giữa Phân khối Trình Duyệt, Loại bỏ Ràng Buộc Cơ Sở Dữ Liệu ngầm và Tiến trình Asynchronous Cấp Server. Chức năng Eventual Consistency phát huy mức độ hoàn hảo, chịu lỗi và tính độc lập toàn vẹn để mở rộng độ mở cho mô hình Storage Cụm ra khỏi cản trở vật lý phần cứng.

### 5.2. Hướng phát triển chuyên sâu tương lai
1. **Dàn Thuật Toán Phục Hồi Chủ Động (Self-Healing Recovery Worker):** Phát triển Hệ quản trị chạy song song tác vụ quét số lượng `ChunkReplica`. Ngay khi hệ thống thiếu số lượng bản sao quy định do có Node gặp nguy kịch hệ thống sẽ lấy dữ liệu Node rảnh để đính thêm Copy mới.
2. **Kỹ Thuật Mã Hoá Gốc Tới Nhọn (End-to-End Encryption):** Ứng dụng giải mã Advanced Encryption Standard (AES) xử lý dữ liệu bảo mật ở mức Client Javascript giúp thông tin chống thâm nhập kể cả từ phía Quản trị viên máy chủ vật lý cuối.
3. **Mở Rộng Kafka Messaging Queue/Broker:** Cắt bỏ luồng API HTTP đồng bộ trực tiếp với các cụm mạng trên trăm Node. Bổ túc cấu trúc định tuyến dữ liệu bất đồng bộ qua hệ sinh thái Data Messaging để phân phối thông điệp Event-Driven an toàn hơn trước lỗi nghẽn cổng kết nối Mạng phân lớp.
