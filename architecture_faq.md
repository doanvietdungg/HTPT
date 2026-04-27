# Hỏi đáp Kiến trúc Mini-HDFS

## Câu hỏi:
Tại sao khi upload một file ở `node1` trong lúc `node2` và `node3` đang down. Sau đó bật `node2` và `node3` lên, tắt `node1` đi thì:
- `node2` vẫn view/tải được file.
- `node3` nhìn thấy file trong danh sách, nhưng lại không thể view/tải được file đó?
Tại sao lại code cho file đó hiện trong danh sách của `node3` khi mà nó không thể xem được dữ liệu lúc 2 node kia down?

---

## Trả lời:

Vấn đề này chạm vào một trong những khái niệm cốt lõi nhất của **Hệ thống tệp tin phân tán (Distributed File System)** như HDFS hay kiến trúc Mini-HDFS mà dự án đang xây dựng.

Lý do `node3` thấy tên file trong danh sách nhưng không xem/tải được khi `node1` và `node2` sập là vì kiến trúc phân tán tách biệt hoàn toàn giữa **Metadata (Dữ liệu đặc tả)** và **Physical Data (Dữ liệu vật lý)**:

### 1. Metadata được đồng bộ cho TẤT CẢ các Node (Global Namespace)
- **Metadata** là những thông tin rất nhẹ (Tên file, dung lượng, file đó đang được chia thành mấy chunk, và chunk đó đang nằm ở ổ cứng của Node nào). 
- Cơ chế `Gossip Protocol` trong dự án có nhiệm vụ đồng bộ cái Metadata này cho **tất cả các node trong cụm 100%**. Do đó, bạn truy cập vào bất kỳ node nào (dù là `node3`) cũng sẽ nhìn thấy một danh sách file y hệt nhau. 
- Điều này giúp người dùng kết nối tới bất cứ node nào cũng biết được tổng quan hệ thống (Global View) đang có những file gì, tạo cảm giác như đang dùng một ổ cứng liền mạch thống nhất.

### 2. Dữ liệu vật lý (Physical Data) chỉ lưu giới hạn để tiết kiệm ổ cứng
- File gốc (ví dụ video 1GB) rất nặng. Nếu bắt `node1`, `node2`, `node3` (và giả sử cụm có 100 nodes) đều phải tải 1GB này về máy thì hệ thống sẽ cạn kiệt dung lượng lưu trữ ngay lập tức.
- Đó là lý do hệ thống sử dụng tham số `REPLICATION_FACTOR = 2` (trong `app/core/config.py`). Cụm Server quy định: **Một file nặng chỉ được lưu tối đa 2 bản sao** trên 2 Node rảnh rỗi nhất để cân bằng giữa an toàn dữ liệu và chi phí ổ cứng.
- Trong kịch bản này, sau quá trình tự động phục hồi (Re-replication), `node1` và `node2` đã giữ 2 bản sao đó. `node3` chỉ có "tờ giấy ghi chú" (metadata) báo rằng *"File này đang được cất ở node 1 và 2"*.

### 3. Khả năng chịu lỗi (Fault Tolerance)
- Với `REPLICATION_FACTOR = 2`, hệ thống được thiết kế để chịu đựng được việc **có đúng 1 node sập cùng lúc** mà không làm mất hoặc gián đoạn luồng dữ liệu.
- Khi bạn tắt `node1`, `node2` vẫn gánh được vì nó chứa bản sao còn lại. 
- Nhưng khi bạn tắt CẢ `node1` và `node2`, bạn đã vượt quá giới hạn chịu đựng lỗi của hệ thống. Lúc này `node3` mở "tờ giấy ghi chú" ra, biết là phải qua nhà số 1 và số 2 để lấy file vật lý cho người dùng, nhưng cả 2 server này đều mất kết nối, nên `node3` đành báo lỗi không thể truy xuất.

> **Giải pháp mở rộng:** Nếu hệ thống yêu cầu mức độ khả dụng (availability) cực cao, đòi hỏi hệ thống vẫn sống sót dù 2 trong số 3 node bị sập cùng lúc, bạn chỉ cần cấu hình lại hệ thống và thay đổi `REPLICATION_FACTOR = 3`. Lúc đó tiến trình tự động phục hồi sẽ ra lệnh cho `node3` tải bản sao vật lý thứ 3 về máy của nó!
