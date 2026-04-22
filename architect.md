# Kiến Trúc Hệ Thống Bookstore Microservice

Tài liệu này tổng hợp kiến trúc tổng thể, cấu trúc thư mục, và các công nghệ được sử dụng trong dự án `bookstore-microservice`.

## 1. Tổng Quan Kiến Trúc (Architecture Overview)

Dự án áp dụng kiến trúc **Microservices (Vi dịch vụ)** kết hợp với mô hình **API Gateway**. Toàn bộ hệ thống được module hóa thành các dịch vụ độc lập, mỗi dịch vụ đảm nhận một miền nghiệp vụ (business domain) riêng biệt. Các dịch vụ giao tiếp với nhau qua HTTP REST API nội bộ và quản lý cơ sở dữ liệu riêng biệt để đảm bảo tính độc lập (Loose Coupling) và dễ dàng mở rộng.

Hệ thống được đóng gói bằng Docker và điều phối thông qua Docker Compose.

## 2. Cấu Trúc Hệ Thống Các Dịch Vụ

Hệ thống bao gồm Front-end, API Gateway, và 11 microservice độc lập:

### Frontend
- **Thư mục:** `frontend/`
- Giao diện người dùng hướng khách hàng và quản trị, tương tác trực tiếp với hệ thống backend thông qua API Gateway.

### API Gateway
- **Thư mục:** `api-gateway/`
- Điểm chạm duy nhất (Single Entry Point) cho mọi request từ Frontend. Xử lý định tuyến (routing), phân luồng request xuống các dịch vụ bên dưới. Xử lý CORS và xác thực (nếu có).

### Các Microservices Nghiệp Vụ
Mỗi service chạy trên một container độc lập và cổng riêng biệt:

1. **Book Service** (`book-service`): Quản lý thông tin sách (CRUD sách, tồn kho).
2. **Cart Service** (`cart-service`): Quản lý giỏ hàng của người dùng. Tương tác với `book-service` để lấy thông tin sách.
3. **Customer Service** (`customer-service`): Quản lý thông tin khách hàng, tài khoản người dùng.
4. **Staff Service** (`staff-service`): Quản lý nhân viên (nhân sự nội bộ).
5. **Manager Service** (`manager-service`): Phục vụ các nghiệp vụ của quản lý cửa hàng.
6. **Order Service** (`order-service`): Đóng vai trò là trung tâm xử lý đơn hàng. Tương tác với rất nhiều service khác: `cart-service` (lấy giỏ hàng), `pay-service` (thanh toán), `ship-service` (vận chuyển) và `book-service`.
7. **Pay Service** (`pay-service`): Xử lý thanh toán đơn hàng.
8. **Ship Service** (`ship-service`): Xử lý quy trình giao hàng, vận chuyển.
9. **Comment Rate Service** (`comment-rate-service`): Quản lý bình luận, đánh giá của khách hàng.
10. **Catalog Service** (`catalog-service`): Quản lý danh mục sản phẩm, phân loại sách.
11. **Recommender AI Service** (`recommender-ai-service`): Hệ thống gợi ý sách thông minh sử dụng AI (RAG Pipeline, Deep Learning). Tương tác với Gemini API và các thư viện Machine Learning.

## 3. Công Nghệ Sử Dụng (Tech Stack)

### Frontend (Giao diện người dùng)
- **Framework/Library:** React 19 (mới nhất).
- **Styling:** Tailwind CSS v4.
- **Routing:** React Router v7.
- **HTTP Client:** Axios.
- **Build Tool:** Vite (đảm bảo tốc độ build và dev nhanh chóng).

### Backend (Microservices)
- **Ngôn ngữ:** Python 3.
- **Web Framework:** Django (>=4.2) và Django REST Framework.
- **Giao tiếp liên dịch vụ (Inter-service Communication):** Synchronous HTTP/REST qua thư viện `requests` mặc định.

### Recommender AI Service (Đặc tả riêng)
Sử dụng các công cụ mạnh mẽ trong lĩnh vực AI/ML:
- **Deep Learning/Tensors:** PyTorch (`torch`).
- **Xử lý ngôn ngữ tự nhiên (NLP):** `sentence-transformers`.
- **Vector Database:** ChromaDB (Lưu trữ và truy xuất vector embeddings).
- **Search Ranking:** `rank_bm25` (Hybrid Retrieval).
- **LLM / Generative AI:** Google Generative AI (Gemini 1.5).
- **Xử lý dữ liệu:** NumPy, Pandas, Scikit-learn.

### Cơ Sở Dữ Liệu (Database)
- **Hệ Quản Trị CSDL:** PostgreSQL 15 (Alpine version).
- **Kiến trúc dữ liệu:** Mô hình Database-per-service. Mỗi microservice sở hữu một database riêng biệt (ví dụ: `book_service_db`, `cart_service_db`, `order_service_db`, v.v.), đảm bảo không có chia sẻ dữ liệu trực tiếp ở mức CSDL giữa các dịch vụ.

### DevOps & Triển khai
- **Containerization:** Docker. Mỗi dịch vụ (bao gồm Frontend) đều có `Dockerfile` riêng để đóng gói.
- **Orchestration:** Docker Compose (`docker-compose.yml`).
- **Môi trường:** Quản lý cấu hình qua biến môi trường (Environment Variables) truyền vào từng container để định tuyến (URL các service khác) và kết nối CSDL (`dj-database-url`).

## 4. Ưu Điểm của Kiến Trúc
1. **Khả năng mở rộng độc lập:** Có thể dễ dàng tăng số lượng container cho `order-service` hay `api-gateway` khi có lưu lượng mua sắm lớn mà không ảnh hưởng tới các service khác.
2. **Dễ bảo trì và cô lập lỗi:** Nếu một service (ví dụ `comment-rate-service`) bị lỗi (crash), toàn bộ hệ thống bán hàng chính (đặt hàng, thanh toán) vẫn có thể hoạt động bình thường.
3. **Phân quyền dữ liệu tốt:** Database riêng cho mỗi service giúp tránh tình trạng nút thắt cổ chai ở CSDL trung tâm (Single point of failure database).
4. **Tích hợp AI dễ dàng:** Nhờ microservices, một service rườm rà về cấu hình mô hình như `recommender-ai-service` được chạy hoàn toàn cô lập, không ảnh hưởng đến code base của các chức năng E-commerce thông thường.
