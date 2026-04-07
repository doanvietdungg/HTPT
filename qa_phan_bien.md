# TÀI LIỆU ÔN TẬP PHẢN BIỆN ĐỒ ÁN (Q&A)

Tài liệu này tổng hợp các câu hỏi hóc búa mang tính kiến trúc hệ thống mà hội đồng giáo viên có thể đặt ra. Các câu trả lời được thiết kế để bật lên sự hiểu biết sâu sắc của bạn về Distributed Systems.

---

### Câu hỏi 1: Tại sao data của Node 3 lại trống không có Metadata (FileEntry)?
**Q:** *Khi dùng trình duyệt cơ sở dữ liệu kiểm tra `metadata.db` ở thư mục của Node 3 (hoặc Node 2), tại sao bảng `FileEntry` lại không có dòng nào, nhưng mở `chunk_replicas` lại có? Các em có làm lỗi không?*

**A:** Dạ thưa thầy/cô, hệ thống không hề bị lỗi. Đây là thiết kế kiến trúc chuẩn phân chia giữa **Control Plane** (Điều khiển) và **Data Plane** (Dữ liệu), tương tự như NameNode và DataNode trong Hadoop HDFS.
1. Khách hàng gọi API Upload vào cổng mạng của Node 1. Hệ thống ngầm định lấy Node 1 làm **NameNode**. NameNode là người duy nhất thao tác với khái niệm "File", nên nó lưu bản đồ file vào bảng `FileEntry` trên Local DB của Node 1.
2. Node 2 và Node 3 tham gia giao dịch với tư cách là **DataNode**. Nghĩa vụ của DataNode không phải là "nhớ file tên gì", mà là "bám lấy các luồng Byte (Chunk) người ta gửi xuống và lưu thẳng vào ổ cứng". 
3. Vì vậy, DB của Node 3 chỉ chứa báo cáo nhật ký ở bảng `chunk_replicas` (Ghi lại IP và trạng thái của Mảnh 1, Mảnh 2...). Đảm bảo an toàn bảo mật, bị hack vào DataNode cũng không truy xuất được cấu trúc file.

---

### Câu hỏi 2: Sự Tự Trị ở các Chi Nhánh (Autonomy)
**Q:** *Dự án có thỏa mãn tiêu chí: Mỗi node mạng là một chi nhánh của chuỗi, tại mỗi chi nhánh tự trị dữ liệu và quyết định các chức năng (giống hoặc khác nhau) không?*

**A:** Dạ có, hệ thống tuân thủ nghiêm ngặt 100% mẫu hình Phân tán đa nhiệm:
1. **Tự trị dữ liệu:** Mỗi Node vận hành trên một phiên bản SQLite độc lập nội bộ (`metadata.db`) và phân vùng vật lý riêng (`data_nodeX`). Không hề có chung một Máy chủ Database tập trung. Node nào ngắt mạng thì nó tự thủ thân cục dữ liệu của nó ở nhà.
2. **Chức năng Giống/Khác Nhau Động (Dynamic Roles):** Quá trình phân chia chức năng không code cứng (Hardcode) từ đầu. Mọi Node chạy chung một mã nguồn `FastAPI` (Bản chất giống nhau). Tuy nhiên, dựa qua thuật toán **Bầu cử (Bully Algorithm Election)**, sơ đồ tổ chức tự tách hàm chức năng ra:
   - Node Thắng Cử: Lên nắm quyền NameNode. Mang chức năng vĩ mô (Tạo File, Phát Map, Làm Quản lý Lock).
   - Node Thua: Biến thành Follower. Mang chức năng vi mô (Nhận byte tải xuống đĩa cứng, Tự động đẩy Pipepline dự phòng sang máy khác).

---

### Câu hỏi 3: Phân Mảnh Ở Đâu (Chunk Slicing)
**Q:** *Thế thì trong hệ thống thực tế với file cực lớn, Client (Khách hàng) phải tự chia nhỏ file ra à? Tại sao không ném cho NameNode chia?*

**A:** Dạ đúng! Trong kiến trúc HDFS, **Client bắt buộc là người chia file**.
1. **Tránh Bottleneck ở Server:** Nếu 100 User đẩy 100 File nặng 50GB lên NameNode tập trung để nó tự cắt. NameNode sẽ bị tắc nghẽn Băng thông (Bị nổ card mạng) và tràn RAM do xử lý dữ liệu Memory.
2. **Tính phân tán thuần túy:** Bằng việc xin NameNode cái Sổ Đỏ (Placement Plan). Client đứng ở nhà mình, dùng Mã nguồn (Javascript/Python) cắt khúc file ném theo hình mẻ lưới quăng đều ra thẳng 10 cái DataNodes xung quanh mạng. Việc này giúp luồng dữ liệu 50GB đi rải rác P2P (Peer-to-peer) không đánh sập hệ thống trung tâm.
3. *Thực tế ngoài đời:* Người dùng bình thường không biết điều này vì **Thư viện Lập trình (SDK) hoặc Mã nguồn giao diện Trình duyệt JS (như Google Drive / AWS S3 SDK)** đã hì hục âm thầm loop cái luồng "Cắt file - Quăng đi" thay cho con người! Đồ án của bọn em cũng viết ra 1 file Trình Duyệt Thông minh Javascript tự bóc tách việc đó cho người dùng.
