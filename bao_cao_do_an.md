# Báo Cáo Đồ Án: Hệ Thống Phân Tán Mini-HDFS

## 1. Project Giải Quyết Vấn Đề Gì?
Trong thời đại bùng nổ dữ liệu, việc lưu trữ các tệp tin kích thước lớn trên một máy chủ đơn lẻ đối mặt với ba rủi ro chí mạng:
- **Giới hạn không gian (Scalability):** Ổ cứng của một máy chủ sẽ bị đầy, không thể lưu trữ vô hạn.
- **Điểm mù hệ thống (Single Point of Failure):** Nếu máy chủ duy nhất bị hỏng, toàn bộ dữ liệu sẽ không thể truy cập.
- **Nút thắt cổ chai (Bottleneck):** Khi nhiều người tải file cùng lúc, băng thông mạng và I/O đĩa của một máy sẽ bị quá tải.

**Mini-HDFS** là một hệ thống tệp phân tán (lấy cảm hứng từ Hadoop HDFS) được xây dựng để giải quyết các vấn đề này bằng cách:
1. **Phân mảnh (Chunking):** Chia nhỏ các file lớn thành các khối (chunks) nhỏ (ví dụ 20MB) và phân tán chúng qua nhiều máy chủ khác nhau để phá vỡ giới hạn ổ cứng phần cứng.
2. **Nhân bản (Replication):** Lưu trữ mỗi chunk trên nhiều máy chủ (Node) khác nhau (Replication Factor = 2 hoặc 3). Nếu một máy tính bị cháy ổ cứng, dữ liệu vẫn còn nguyên vẹn ở máy khác.
3. **Tự trị và Tự phục hồi (Data Autonomy & Self-Healing):** Mỗi node hoạt động độc lập với Cơ sở dữ liệu riêng; ứng dụng giao thức Gossip để tự động cập nhật mạng lưới khi có máy mới tham gia hoặc máy cũ bị hỏng, đảm bảo tính sẵn sàng cao (High Availability).

---

## 2. Các Công Nghệ Sử Dụng
- **Backend Framework:** `Python` + `FastAPI`. Được chọn vì FastAPI hỗ trợ Asynchronous (Bất đồng bộ) mạnh mẽ qua `async/await`, cực kỳ quan trọng đối với các hệ thống phân tán cần liên tục gọi HTTP (I/O Bound) sang các Node khác mà không bị block luồng xử lý.
- **Database & ORM:** `MySQL 8.0` + `SQLAlchemy`. Hệ quản trị CSDL quan hệ ổn định nhất. ORM SQLAlchemy được dùng để biểu diễn cấu trúc bảng và hỗ trợ tính năng xáo trộn dữ liệu linh hoạt (`db.merge()`).
- **Containerization & Network:** `Docker` + `Docker Compose`. Triển khai dễ dàng đa môi trường; sử dụng mạng nội bộ `bridge` để giả lập Cluster nội bộ (Cluster Virtualization).
- **Inter-node Communication:** `HTTP/REST (httpx)`. Các node giao tiếp, truyền tải Heartbeat và truyền file (Pipelining) trực tiếp qua giao thức HTTP bất đồng bộ.
- **Frontend:** Vanilla JS (`HTML/CSS/JS thuần`). Xử lý API File trực tiếp trên trình duyệt, có khả năng chẻ nhỏ file bằng cấp thấp (Byte-level slicing) để tải lên mượt mà bằng AJAX.

---

## 3. Cách Cài Đặt và Cấu Hình Hệ Thống Nhiều Node
Hệ thống linh hoạt hỗ trợ 2 mô hình triển khai thông qua Docker Compose.

### A. Môi Trường Test (Chạy 3 Node trên 1 Máy Tính)
Sử dụng file `docker-compose-test.yml` cung cấp môi trường Cluster Demo:
- Hệ thống dựng lên 3 container FastAPI ứng với 3 Node (`minihdfs_node1`, `2`, `3`).
- Dựng lên 3 container MySQL ứng với 3 DB tự trị (`mysql_node1`, `2`, `3`).
- Các ports giao tiếp được Map từ `8001`, `8002`, `8003` ra ngoài.
**Cách chạy:** `docker-compose -f docker-compose-test.yml up --build -d`

### B. Môi Trường Production (Chạy nhiều máy vật lý)
Sử dụng file `docker-compose.yml` nguyên bản, mỗi máy vật lý chỉ chạy 1 Node và 1 DB. Cấu hình được đưa ra ngoài vỏ thông qua tệp `.env`.
1. Copy dự án sang Máy tính 1 (Ví dụ IP Lan: `192.168.1.101`). Tạo tệp `.env`:
   ```env
   NODE_ID=node1
   MY_IP=192.168.1.101
   PEER_IPS=192.168.1.102:8000,192.168.1.103:8000
   ```
2. Copy dự án sang Máy tính 2 (IP Lan: `192.168.1.102`). Tạo tệp `.env`:
   ```env
   NODE_ID=node2
   MY_IP=192.168.1.102
   PEER_IPS=192.168.1.101:8000,192.168.1.103:8000
   ```
3. Chạy `docker-compose up -d` trên từng máy để tạo Cluster.

---

## 4. Phân Tích Chuyên Sâu Giải Pháp Cốt Lõi Và Logic Source Code

### 4.1. Cắt File Trực Tiếp Tại Trình Duyệt (Client-side Chunking)
- **Vấn đề (Pain point):** Phải làm sao khi người dùng tải lên file vài GB trong khi hệ thống chỉ có RAM giới hạn? Nếu ném thẳng 1 khối lên Server, nguy cơ rớt gói tin và đầy bộ đệm (Buffer Overflow) là chắc chắn.
- **Giải Pháp (Solution):** Băm nhỏ tệp tại ngay Trình Duyệt máy Khách (Client) thành các gói tin nhỏ (VD: 20MB). Gửi từng cục riêng lẻ và ráp lại bản đồ siêu dữ liệu ở hệ thống mây.
- **Giải Thích Code (`frontend/js/app.js`):**
  ```javascript
  // Lặp qua tổng dung lượng vật lý của File cần upload
  // Mỗi vòng lặp sẽ tịnh tiến biến start thêm một khoảng bằng CHUNK_SIZE
  for (let start = 0; start < file.size; start += placement.chunk_size) {
      
      // Chặn biên: Đảm bảo điểm kết thúc không vọt quá kích cỡ file
      let end = Math.min(start + placement.chunk_size, file.size);
      
      // Lệnh Cốt Lõi: Đọc vào File System của ổ cứng người dùng, 
      // rạch ra chính xác một lát cắt nhị phân (Blob) mà không cần bốc toàn bộ File vào RAM
      let chunkBlob = file.slice(start, end);
      
      let formData = new FormData();
      formData.append('file', chunkBlob);
      // Gửi ngầm (AJAX) cục mảnh này lên IP mà NameNode đã phân luồng
      uploadPromises.push(uploadChunk(targetUrl, formData));
  }
  ```

### 4.2. Placement Plan (Thuật Toán Cân Bằng Tải - Load Balancing)
- **Vấn đề:** Nếu file có 100 mảnh, đổ cả 100 mảnh này vào Node 1 thì Node 1 hỏng ổ cứng. Làm sao chia đều cho cả 3 Nodes?
- **Giải pháp:** Khi Frontend yêu cầu init Upload, NameNode sẽ tính toán điểm (Score) từng máy. Máy nào ổ đĩa đang rảnh rỗi sẽ ưu tiên nhét nhiều mảnh vào hơn.
- **Giải Thích Code (`app/services/metadata.py` - hàm `generate_placement_plan`):**
  ```python
  # (1) Chấm điểm Node rảnh rỗi:
  def score_node(n: ClusterNode):
      # Sử dụng công thức: (Tổng dung lượng - Đã dùng) = Dung lượng rảnh. 
      free_space = n.storage_capacity_total - n.storage_capacity_used
      return free_space * n.network_score

  # Sắp xếp mảng chứa các Node đang sống theo độ Mập mạp rảnh rỗi giảm dần
  valid_nodes.sort(key=lambda x: score_node(x), reverse=True)
  
  # (2) Suy Thoái Duyên Dáng (Graceful Degradation)
  # Nếu config yêu cầu nhân bản 3 máy, nhưng mạng rớt còn sống 2 máy.
  # Lệnh min() tự động ép chuẩn lưu trữ xuống hệ số 2 để tránh treo vĩnh viễn hệ thống.
  effective_rf = min(replication_factor, len(valid_nodes))

  # (3) Phân phát bằng cơ chế xoay vòng Round-Robin 
  for i in range(total_chunks):
      # Pép chia lấy dư %: Chunk 0->Node 1, Chunk 1->Node 2, Chunk 2->Node 3...
      primary_idx = i % len(valid_nodes)
      #...
  ```

### 4.3. Thống Kê Dung Lượng I/O Bất Đồng Bộ (Asynchronous Capacity Polling)
- **Vấn đề:** Để có biến số cho hàm Cân Bằng Tải ở mục 4.2, CSDL phải liên tục biết ổ đĩa các Node còn trống bao nhiêu. Nếu ta gài lệnh Update DB vào ngay sau hàm Upload File, hệ thống sẽ gặp "Nút Thắt Cổ Chai", vì các luồng Upload đồng thời sẽ tranh nhau khóa (Lock) Table trong SQL.
- **Giải pháp:** Áp dụng "Bất Đồng Bộ Liều Cao". Quá trình upload tệp không trực tiếp cập nhật DB. Thay vào đó, một luồng chạy ngầm liên tục hỏi thăm ổ đĩa vật lý để khai báo chéo cho nhau bằng Heartbeat.
- **Giải Thích Code (`app/services/heartbeat.py`):**
  ```python
  # Daemon chạy lặp Vĩnh viễn không bao giờ dừng (Background Process)
  while True:
      # Sát thủ cốt lõi: Sử dụng shutil của hệ điều hành 
      # Bóc sát phần cứng thư mục chứa Data để moi ra dung lượng Bytes thật
      total, used, free = shutil.disk_usage(settings.DATA_DIR)
      
      async with httpx.AsyncClient() as client:
          for peer in peers:
              # Đẩy gói thông tin này sang API cập nhật CSDL của toàn mạng lưới 
              # với Tốc độ làm mới là 1 GIÂY MỘT LẦN (Real-time).
              await client.post(url, params={"host": settings.MY_IP, "used": used...})
              
      await asyncio.sleep(1) # Nghỉ ngơi 1 giây rồi vòng lặp lại
  ```
  => *Nhờ bóc tách như vậy, hàng ngàn request upload file sẽ không bao giờ làm kẹt Database.*

### 4.4. Pipeline Replication (Truyền Nước Phân Tán)
- **Vấn đề:** Nếu bắt thiết bị khách (Điện thoại) tải cả mảnh Gốc (Sang Node 1) lẫn mảnh Dự Băng (Sang Node 2), người dùng sẽ tốn x2 tiền cước 4G và x2 thời gian.
- **Giải pháp:** Trình duyệt chỉ nén đúng 1 lần lên Master Node (Node Mũi nhọn). Khi Master lưu vô đĩa xong, nó sẽ dùng cổng Cáp Quang LAN nội bộ của Server để tống bản Copy sang cục Slave (Node Phụ) một cách bất đồng bộ.
- **Giải Thích Code (`app/api/chunks.py` - hàm `upload_chunk`):**
  ```python
  # Bước 1: Lưu cục Chunk vào ổ cứng của chính máy chủ này
  with open(file_path, "wb") as buffer:
      shutil.copyfileobj(upload_file.file, buffer)
  db.commit()

  # Bước 2: Kích hoạt Forwarder (Người chuyển phát nhanh âm thầm)
  if secondary_nodes:
      for idx, next_node in enumerate(nodes):
          # Lệnh await sẽ bắn tín hiệu nhị phân sang nhà mạng của "next_node"
          # Gửi ngầm bên dưới lòng đất (Backend to Backend) thay vì rớt vào Client
          success = await forward_chunk_to_replica(...)
  ```

### 4.5. Tự Trị Dữ Liệu (Data Autonomy & Mềm Hoá DBMS)
- **Vấn đề:** Master Node (Node 1) cầm quyển bản đồ (File Metadata), khi nó ném cục nhị phân Sang Slave Node (Node 2), Node 2 có nhiệm vụ rạch Database lưu cục nhị phân đó vào sổ. Nếu áp dụng Foreign Key thuần SQL truy cập chéo, SQL Node 2 sẽ văng lỗi `IntegrityError` "Tôi không thấy File Map mà anh đòi insert mảnh con này!".
- **Giải pháp:** Gỡ bỏ `Relationships SQL` vật lý, làm mềm CSDL bằng việc lưu Blind ID.
- **Giải Thích Code (`app/models/domain.py`):**
  ```python
  class ChunkReplica(Base):
      __tablename__ = "chunk_replica"
      # Chỗ này LẼ RA là: ForeignKey("chunk_entry.chunk_id"). 
      # NHƯNG ta đã chuyển cạn sang chuỗi trơn String để đánh chặn việc SQL báo lỗi
      chunk_id = Column(String(100), index=True)
  ```
  => *Kết quả: Máy phục vụ nào cũng sẽ tiếp nhận mọi cục rác nhị phân nếu được ném qua mà không cần thắc mắc lai lịch của cục nhị phân đó. Giúp Nodes có thể tự ngắt kết nối mà vẫn sống.*

### 4.6. Đồng Bộ Chữa Lành Gossip (Eventual Consistency)
- **Vấn đề:** Hậu Quả của mục (4.5) là Máy phụ 2 lưu cục File nhưng không biết hình dáng File nên không thể xuất ra cho người tải. Hệ thống sẽ khuyết tật nếu Máy Chính Mất đi quyển Sổ Bản Đồ (Mất FileEntry & ChunkEntry).
- **Giải pháp:** Gossip Protocol (Giao thức lan truyền tin đồn). Giống như Zombie cắn nhau, máy này truyền Sổ Bản đồ sang máy láng giềng.
- **Giải Thích Code (`app/services/gossip.py`):**
  ```python
  async def sync_metadata_daemon():
      # Luồng ẩn vòng lặp Vĩnh Cửu (Infinite Loop)
      while True:
          # Sang hàng xóm copy JSON đống số liệu 
          resp = await client.get(f"http://{peer}/api/nodes/metadata/dump")
          data = resp.json()
          
          # Hứng được đống Map (File/Chunks) -> Đập thẳng vào CSDL Nhà Minh
          for f_data in data.get("files", []):
              # Ép kiểu dữ liệu (Validation) chuẩn hoá rủi ro ngày tháng năm
              validated = FileEntryDump(**f_data).dict()
              
              # Lệnh MERGE thần thánh của SQLAlchemy: 
              # Cơ Chế Hoả Mù: UPSERT (Khớp Khoá=Ghi Đè, Không Khớp=Tạo Mới)
              # Triệt tiêu tình huống trùng lặp khoá chính gây nổ DB
              db.merge(FileEntry(**validated)) 
              
          db.commit() # Chốt sổ toàn bộ Map bản đồ vào DB
          await asyncio.sleep(10) # 10 giây đi dọn dẹp cống thoát nước 1 lần
  ```
  => *Đây là lá bùa Hồi Sinh Hệ Thống tối thượng. Dù máy Chủ Rút Phích Cắm Bất Đắc Kì Tử. Hệ thống Data Node 2 đã tự lén ôm toàn bộ CSDL của Máy Chủ 1 cách đó vài giây. Lên trình duyệt vào Node 2 ngắm, ta vẫn mở PDF, tải Video sướng mượt mà cứ thế chạy qua Pipeline!*

---

## 5. Kiến Trúc Kháng Lỗi (Fault Tolerance) & Dàn Xếp Sự Cố (Failover)

Một hệ thống phân tán thực thụ không phải là hệ thống không bao giờ chết, mà là hệ thống biết **tự động dàn xếp công việc khi có Node chết**. Dưới đây là 3 bước phản ứng dây chuyền của hệ thống khi rủi ro xảy ra:

### Bước 1: Nhận diện sự kiện "Kẻ phản bội" bằng Heartbeat (Bắt mạch)
Hệ thống mạng LAN không có một "Máy Chủ Trung Tâm" nào làm lớp trưởng để điểm danh. Thay vào đó, chúng tự điểm danh chéo nhau.
- **Cơ chế:** Mỗi Node cứ đúng 1 giây sẽ kêu lên một tiếng (Bắn tín hiệu HTTP `/heartbeat`) cho toàn bộ anh em biết "Tôi còn sống".
- **Phát hiện:** Nếu Node 2 cúp điện. Vòng lặp `detect_failures_daemon()` (trong `heartbeat.py`) của Node 1 và Node 3 sẽ liên tục lấy `Thời_Gian_Hiện_Tại - Thời_Gian_Kêu_Cuối_Cùng`. Giao thức quy định giới hạn sống `ELECTION_TIMEOUT = 4 giây`.
  - Vượt quá 4 giây im lặng, DB của Node 1 lập tức cập nhật trạng thái Node 2 thành `DEAD` (Tử hình).

### Bước 2: Sơ Tán Khách Hàng (Traffic Rerouting & Graceful Degradation)
Ngay khi DB ghi nhận Node 2 chết, hệ thống lập tức tiến hành chống tràn:
- Cờ `status == "ALIVE"` ở hàm thuật toán Rải File `generate_placement_plan` (trong `metadata.py`) sẽ gạch tên Node 2 khỏi mâm bốc thăm.
- Nhờ hàm suy thoái duyên dáng `effective_rf = min(replication_factor, len(valid_nodes))`, nếu yêu cầu cắt làm 3 bản mà rớt mạng mất 1. File mới up lên sẽ tự hiểu và dồn vào 2 máy còn sống thay vì ném lỗi Timeout.

### Bước 3: Thuật Toán Phục Hồi Nhân Bản Đã Mất (Re-Replication Self-Healing)
Đây là nước đi cao cấp nhất xử lý số Data cũ đang nằm trên vỏ ổ cứng Node 2 vừa cháy:
```python
# Code trong app/services/recovery.py
# (1) Đếm số Node CÒN SỐNG đang giữ mảnh (Chunk X)
alive_replicas = db.query(ChunkReplica).join(ClusterNode).filter(... Node.status == "ALIVE").count()

# (2) Đối chiếu với Số bản phải giữ (replication_factor). VD cần 2 bản, mà Node 2 chết làm tụt xuống còn 1 bản.
if alive_replicas < file_entry.replication_factor:
    print(f"Warning: Chunk {ck.chunk_id} is under-replicated... Re-replication needed.")
```
**Options Giải Quyết:**
1. Trạng thái hiện tại: Đưa ra thông báo `Cảnh Báo Mất Bản Sao`. Khách hàng hoàn toàn **không biết** và quá trình Download tệp vẫn diễn ra bình thường do thuật toán Download thông minh tự móc Data của Node 1/3 thay thế Node 2.
2. Hướng mở rộng Triển Phiên (Self-healing Trigger): 
   - Hàm `re_replication_daemon()` này sẽ gọi API `Phục Hỏi`.
   - Node 3 (máy sống có giữ bản sao) sẽ lôi mảnh Chunk 1 đó ra, bắn văng sang một máy dập phòng Node 4 mới cắm vào.
   - Thao tác này giúp mức độ che chắn của file PDF trở lại mức 3/3 (Hoàn thiện giáp như chưa từng có cuộc tấn công nào).
