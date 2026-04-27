# MÔ TẢ HỆ THỐNG LƯU TRỮ PHÂN TÁN (MINI-HDFS)

## 1. Mô hình kiến trúc
Hệ thống được thiết kế theo mô hình **Master-Slave phân tán** (tương tự kiến trúc Hadoop HDFS). Mỗi máy tính tham gia vào mạng (Node) đóng vai trò như một "chi nhánh" độc lập trong một chuỗi cung ứng dữ liệu.

## 2. Tính tự trị tại mỗi chi nhánh (Node Autonomy)
*   Mỗi Node là một ứng dụng riêng biệt chạy trên nền tảng FastAPI.
*   Mỗi chi nhánh có **cơ sở dữ liệu cục bộ riêng (SQLite)** và phân vùng ổ cứng vật lý riêng để lưu trữ dữ liệu. 
*   Các chi nhánh hoàn toàn không sử dụng chung database. Nếu một chi nhánh mất kết nối, dữ liệu tại đó vẫn được bảo toàn và ứng dụng tại đó vẫn có thể hoạt động độc lập.

## 3. Chức năng động của các Node
Tất cả các Node trong chuỗi có mã nguồn giống nhau nhưng chức năng được phân hóa động dựa trên trạng thái hệ thống:
*   **Thủ lĩnh (NameNode):** Thông qua thuật toán bầu cử Bully, Node mạnh nhất sẽ được bầu làm thủ lĩnh để điều phối, quản lý Metadata và cấp phép giao dịch (Lock) cho toàn hệ thống.
*   **Nhân viên (DataNode):** Các node còn lại đóng vai trò chi nhánh lưu trữ, thực hiện việc ghi dữ liệu và nhân bản bảo mật.

## 4. Giao dịch trên toàn hệ thống (Global Transactions)
Hệ thống xử lý các giao dịch phức tạp đi xuyên suốt qua các chi nhánh:
*   **Giao dịch Lưu trữ & Nhân bản (Replication):** Khi một chi nhánh tiếp nhận dữ liệu, hệ thống tự động thực hiện tiến trình Pipelining để nhân bản dữ liệu đó sang chi nhánh khác, đảm bảo file luôn có ít nhất 2 bản sao ở 2 máy vật lý khác nhau.
*   **Giao dịch Đồng bộ & Bầu cử:** Các chi nhánh liên tục gửi tín hiệu "nhịp tim" (Heartbeat) để giám sát lẫn nhau. Khi thủ lĩnh gặp sự cố, các chi nhánh tự động kích hoạt giao dịch bầu cử toàn hệ thống để tìm người thay thế mà không cần can thiệp thủ công.
*   **Giao dịch Khóa phân tán (Distributed Lock):** Đảm bảo tại một thời điểm chỉ có một chi nhánh được quyền chỉnh sửa một tệp tin nhất định, tránh xung đột dữ liệu trên toàn chuỗi.

## 5. Mục tiêu hướng tới
Xây dựng một hệ thống lưu trữ có tính sẵn sàng cao (High Availability) và khả năng mở rộng ngang (Horizontal Scaling), cho phép ghép nối thêm nhiều "chi nhánh" vào hệ thống một cách dễ dàng.
