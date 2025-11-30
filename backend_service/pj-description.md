DỰ ÁN INNOVATION: FLOOD-AI
Tên đầy đủ: Nền tảng Dẫn đường Thông minh và Cảnh báo Ngập lụt Đô thị dựa trên Thị giác Máy tính & Dữ liệu Cộng đồng.

I. Bối cảnh & Vấn đề (The Problem)
Nỗi đau thị trường (Market Pain Point):
Google Maps: Dựa vào ảnh vệ tinh và mô hình toán học, nên chỉ phù hợp cho dự báo diện rộng, không phù hợp cho hiện trạng đường phố hiện 
Ứng dụng hiện tại (UDI/HSDC): Phụ thuộc vào con người báo cáo thủ công hoặc cảm biến đắt tiền. Độ trễ cao, độ phủ thấp (bỏ sót các ngõ ngách).
Khoảng trống: Thiếu một giải pháp Dẫn đường thời gian thực chuyên biệt cho Xe máy tại Việt Nam, có khả năng phát hiện ngập tức thời.
II. Giải pháp & Điểm Đột phá (Solution & Innovation)
Mô hình "Cảm biến mềm" (Software-defined Sensors): Thay vì lắp cảm biến vật lý, sử dụng AI để biến Camera giao thông và Camera nhà dân thành hàng nghìn điểm đo ngập tự động.
Mạng lưới Cộng đồng Bảo mật (Privacy-preserving Edge AI): Cho phép người dân chia sẻ dữ liệu từ camera an ninh thông qua xử lý tại biên (Edge AI), đảm bảo video riêng tư không bao giờ rời khỏi nhà họ.
Điều hướng Động (Dynamic Routing): Không chỉ cảnh báo "Có ngập", hệ thống tự động coi điểm ngập là "Vật cản" và vẽ lại lộ trình an toàn, tối ưu riêng cho từng loại xe (Xe máy vs Ô tô gầm cao).
III. Chi tiết Công nghệ & Kiến trúc (Technical Architecture)
1. Thu thập Dữ liệu Đa nguồn (Input Layer)
Nguồn 1: Camera Giao thông (Public): Truy cập luồng video hoặc ảnh chụp nhanh (snapshot) từ các cổng thông tin giao thông.
Nguồn 2: Camera Cộng đồng (Private Nodes): Kết nối với camera nhà dân, gửi snapshot về, che ảnh nếu được yêu cầu.
Nguồn 3: Dữ liệu Khí tượng (API): Lấy dữ liệu mưa hiện tại và dự báo từ OpenWeatherMap/AccuWeather.
2. Lõi Xử lý AI (Core Processing Layer) - Chiến thuật "Chia để trị"
Module A: AI Vision (Xác thực Thực tế - Ground Truth):
Nhiệm vụ: Trả lời câu hỏi "Đường có đang ngập không?" (Yes/No).
Công nghệ: Mạng nơ-ron CNN nhẹ (MobileNet/YOLO) phân loại ảnh.
Ưu điểm: Xử lý nhanh, không cần đo độ sâu phức tạp, chạy mượt trên thiết bị cấu hình thấp.
Module B: Statistical Prediction (Dự báo Sớm - Warning):
Nhiệm vụ: Trả lời câu hỏi "Sắp ngập chưa?".
Công nghệ: Thuật toán Thống kê (Logistic Regression).
Logic: Dựa trên Lượng mưa (API) + Hệ số rủi ro từng Quận (District Coefficient - tự xây dựng dựa trên lịch sử ngập).
3. Giao diện & Điều hướng (Output Layer)
Bản đồ Ngập lụt (Live Map): Hiển thị các điểm ngập đã được AI xác thực (Màu đỏ) và các điểm dự báo nguy cơ (Màu vàng).
Engine Tìm đường: Sử dụng thuật toán tìm đường (A* hoặc Dijkstra) có trọng số:
Đường khô = Trọng số 1.
Đường ngập = Trọng số Vô cực (Cấm đi cho xe máy).
IV. Chiến lược Dữ liệu (Data Strategy - Cách xử lý việc thiếu Data)
Loại Dữ liệu
Thách thức
Giải pháp của Dự án
Hệ thống cống ngầm
Không có (Bảo mật).
Sử dụng "Hệ số Rủi ro Quận" (District Coefficient) làm biến số thay thế (Proxy Variable). Ví dụ: Gán Quận trũng hệ số 1.5, Quận cao hệ số 0.8.
Camera nhà dân
Đa dạng hãng, khó kết nối.
Sử dụng chuẩn ONVIF/RTSP để kết nối vạn năng.
Nhãn dán (Labels)
Thiếu dữ liệu lịch sử chi tiết.
Giai đoạn đầu: Label thủ công dựa trên tin tức báo chí (Data Mining).

Giai đoạn sau: Dùng chính kết quả từ AI Vision để tự động cập nhật và huấn luyện lại mô hình (Self-learning Loop).

V. Kịch bản Demo 
Bước 1 - Kết nối: Show màn hình phần mềm kết nối thành công với 2 camera khác hãng (1 cái Imou, 1 cái Xiaomi) qua giao thức RTSP.
Bước 2 - Vision AI: Đưa hình ảnh/video đường ngập ra trước camera. Hệ thống báo động đỏ ngay lập tức: "DETECTED: FLOOD".
Bước 3 - Dự báo (Simulation): Giả lập API thời tiết báo mưa to 50mm. Bản đồ trên màn hình xuất hiện cảnh báo vàng: "Dự báo ngập sau 15 phút".
Bước 4 - Dẫn đường:
Chọn lộ trình từ A đến B (đang đi qua điểm ngập).
Hệ thống tự động "bẻ lái", vẽ đường vòng khác an toàn hơn.
Thông báo: "Phát hiện ngập trên đường X, đã chuyển sang lộ trình Y an toàn cho xe máy".
VI. Tiềm năng & Hướng phát triển (Future Work)
Mở rộng: Tích hợp với Google Home/Tuya để mở rộng mạng lưới camera gia đình.
Kinh doanh: Bán API dữ liệu ngập thời gian thực cho các công ty giao hàng (Grab/ Shopee Food) để tối ưu vận chuyển.
Cộng đồng: Cơ chế "Flood Points" - Tích điểm đổi quà cho người dân chia sẻ dữ liệu camera.

