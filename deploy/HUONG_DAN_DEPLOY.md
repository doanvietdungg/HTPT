# HƯỚNG DẪN DEPLOY TRÊN NHIỀU MÁY THẬT (LAN/WiFi)

## Kiến trúc triển khai thực tế

```
[Máy 1 - 192.168.1.101]          [Máy 2 - 192.168.1.102]          [Máy 3 - 192.168.1.103]
┌──────────────────────┐          ┌──────────────────────┐          ┌──────────────────────┐
│  FastAPI node1 :8000 │◄────────►│  FastAPI node2 :8000 │◄────────►│  FastAPI node3 :8000 │
│  MySQL mysql_node1   │          │  MySQL mysql_node2   │          │  MySQL mysql_node3   │
│  data/  (chunks)     │          │  data/  (chunks)     │          │  data/  (chunks)     │
└──────────────────────┘          └──────────────────────┘          └──────────────────────┘
         ▲                                   ▲                                  ▲
         └───────────────────────────────────┴──────────────────────────────────┘
                                    LAN / WiFi
```

---

## Yêu cầu mỗi máy

- Docker Desktop (Windows/Mac) hoặc Docker Engine (Linux)
- Cổng `8000` và `3306` được mở trong Firewall
- Cùng mạng LAN / WiFi với các máy khác

---

## Các bước deploy (làm trên TỪN MÁY)

### Bước 1: Lấy project

Copy toàn bộ thư mục project lên mỗi máy (USB, Git clone, SCP...).

```bash
git clone <repo_url>
cd HTPT
```

### Bước 2: Xác định IP của máy này trong mạng LAN

**Windows:**
```powershell
ipconfig
# Tìm dòng "IPv4 Address" của card mạng đang dùng
```

**Linux/Mac:**
```bash
ip addr show   # hoặc ifconfig
```

### Bước 3: Tạo file .env từ template

**Trên Máy 1:**
```bash
cp deploy/.env.node1 .env
```
Mở file `.env` và sửa các IP cho đúng:
```env
NODE_ID=node1
MY_IP=192.168.1.101          # IP thật của Máy 1
PEER_IPS=192.168.1.102:8000,192.168.1.103:8000  # IP Máy 2 và Máy 3
```

**Trên Máy 2:**
```bash
cp deploy/.env.node2 .env
# Sửa MY_IP=<IP máy 2> và PEER_IPS=<IP máy 1>,<IP máy 3>
```

**Trên Máy 3:**
```bash
cp deploy/.env.node3 .env
# Sửa MY_IP=<IP máy 3> và PEER_IPS=<IP máy 1>,<IP máy 2>
```

### Bước 4: Build và chạy (trên từng máy)

```bash
docker-compose up --build -d
```

Kiểm tra container đang chạy:
```bash
docker-compose ps
```

Kết quả mong đợi:
```
NAME                     STATUS
minihdfs_node1          Up
minihdfs_mysql_node1    Up (healthy)
```

### Bước 5: Kiểm tra kết nối liên node

Trên Máy 1, kiểm tra xem Node 1 có ping được Node 2/3 không:
```bash
curl http://192.168.1.102:8000/api/nodes/heartbeat
```

---

## Truy cập giao diện Web

Sau khi cả 3 máy đã chạy, mở trình duyệt trên bất kỳ máy nào:

| Node | URL Giao diện | URL API Docs |
|------|--------------|-------------|
| Node 1 | `http://192.168.1.101:8000/ui/` | `http://192.168.1.101:8000/docs` |
| Node 2 | `http://192.168.1.102:8000/ui/` | `http://192.168.1.102:8000/docs` |
| Node 3 | `http://192.168.1.103:8000/ui/` | `http://192.168.1.103:8000/docs` |

---

## Kiểm tra MySQL từng node (để demo tự trị dữ liệu)

Kết nối vào MySQL của Máy 1 từ bất kỳ máy nào trong LAN:
```bash
mysql -h 192.168.1.101 -P 3306 -u hdfs_user -phdfs_pass hdfs_meta
```

So sánh bảng `file_entry` giữa 3 máy → Chỉ máy upload mới có record → **Chứng minh tính tự trị!**

---

## Dừng và dọn dẹp

```bash
# Dừng containers
docker-compose down

# Dừng và xóa cả data MySQL (reset hoàn toàn)
docker-compose down -v
```
