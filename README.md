# 🧠 Emotion-Aware Smart Room — IoT

<p align="center">
  <img src="https://img.shields.io/badge/Platform-ESP32-blue?style=for-the-badge&logo=espressif" />
  <img src="https://img.shields.io/badge/AI-DeepFace%20%7C%20FER-purple?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/Protocol-MQTT-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Backend-Python%203.11-yellow?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/Dashboard-WebSocket-green?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-MIT-lightgrey?style=for-the-badge" />
</p>

<p align="center">
  Hệ thống nhận diện cảm xúc khuôn mặt theo thời gian thực bằng <strong>AI kép (DeepFace + FER)</strong>,<br/>
  tự động điều khiển <strong>đèn LED ESP32</strong> qua <strong>MQTT</strong> và hiển thị trên <strong>Web Dashboard</strong> realtime.
</p>

---

## 📌 Giới thiệu

**Emotion-Aware Smart Room** là hệ thống IoT thông minh kết hợp **Computer Vision** và **Embedded System**, sử dụng webcam để nhận diện cảm xúc người dùng và tự động phản hồi qua phần cứng.

Điểm nổi bật của hệ thống:
- 🤖 **AI kép** — FER (Facenet-PyTorch) + DeepFace (TensorFlow) chạy song song, xác nhận chéo kết quả để tăng độ chính xác
- 🗳️ **Majority Vote** — lấy kết quả đa số từ 5 frame liên tiếp, tránh nhảy cảm xúc lung tung
- 📡 **MQTT realtime** — kết quả được publish ngay lập tức đến ESP32 và Dashboard
- 💡 **LED thông minh** — mỗi cảm xúc có pattern nhấp nháy riêng biệt
- 🌐 **Web Dashboard** — giao diện hiện đại hiển thị cảm xúc, confidence, nhật ký theo thời gian thực

---

## 🖥️ Demo

| Web Dashboard | Kết quả Python |
|:---:|:---:|
| ![Giao diện](https://github.com/khanhly-dn/Emotion_Aware_SmartRoom_IoT/blob/main/GD.png?raw=true) | ![Kết quả Python](https://github.com/khanhly-dn/Emotion_Aware_SmartRoom_IoT/blob/main/KQ_PYTHON.png?raw=true) |

| Kết quả Arduino | Sản phẩm thực tế |
|:---:|:---:|
| ![Kết quả INO](https://github.com/khanhly-dn/Emotion_Aware_SmartRoom_IoT/blob/main/KQ_INO.png?raw=true) | ![Sản phẩm](https://github.com/khanhly-dn/Emotion_Aware_SmartRoom_IoT/blob/main/SP.jpg?raw=true) |

---

## 🗺️ Mô hình hoạt động

<p align="center">
  <img width="700" src="https://github.com/khanhly-dn/Emotion_Aware_SmartRoom_IoT/blob/main/SDHD.png?raw=true" />
</p>

```
Webcam (0.8s/frame)
        ↓
  FER (Facenet-PyTorch)   +   DeepFace (TensorFlow/MTCNN)
        ↓                              ↓
         Cross-validation + Majority Vote (5 frames)
                        ↓
              Confidence ≥ 60% → Publish MQTT
                        ↓
     ┌──────────────────┼──────────────────┐
     ↓                  ↓                  ↓
  ESP32 LED       WebSocket Server    Web Dashboard
(GPIO pattern)   ws://localhost:8765   index.html
```

---

## ⚙️ Chức năng chính

- **Nhận diện 7 cảm xúc:** `happy` `sad` `angry` `fear` `surprise` `neutral` `disgust`
- **AI kép xác nhận chéo** — tăng độ chính xác so với dùng 1 model đơn lẻ
- **Majority vote buffer 5 frames** — tránh kết quả nhảy lung tung
- **Ngưỡng confidence tối thiểu 60%** — chỉ publish khi chắc chắn
- **LED nhấp nháy pattern** — mỗi cảm xúc có tần suất và số lần nháy riêng
- **Web Dashboard realtime** — emoji, confidence bar, thống kê phiên, nhật ký
- **MQTT retain** — ESP32 nhận được state mới nhất khi vừa kết nối lại

---

## 🛠️ Phần cứng sử dụng

<p align="center">
  <img width="600" src="https://github.com/khanhly-dn/Emotion_Aware_SmartRoom_IoT/blob/main/TB.png?raw=true" />
</p>

| Linh kiện | Kết nối | Mô tả |
|---|---|---|
| **ESP32 Dev Module** | — | Vi điều khiển chính, WiFi tích hợp |
| **LED 2 chân** | GPIO2 → 220Ω → LED(+) → LED(-) → GND | Nhấp nháy theo cảm xúc |
| **Điện trở 220Ω** | Nối tiếp với LED | Bảo vệ LED |
| **Webcam** | USB máy tính | Chụp khuôn mặt realtime |
| **Nguồn** | USB 5V | Cấp điện ESP32 |

**Sơ đồ đấu dây:**
```
ESP32 GPIO2  →  Điện trở 220Ω  →  LED(chân dài +)  →  LED(chân ngắn -)  →  GND
```

---

## 💡 LED Pattern theo cảm xúc

| Cảm xúc | GPIO | Pattern | Mô tả |
|---|---|---|---|
| 😊 Happy | 2 | 3 lần nhanh (200ms) | Vui vẻ, nháy nhanh |
| 😢 Sad | 4 | 1 lần chậm (800ms) | Buồn, sáng dài |
| 😠 Angry | 5 | 5 lần rất nhanh (80ms) | Tức giận, nháy liên tục |
| 😨 Fear | 18 | 2 lần run (300ms) | Sợ hãi, nháy run |
| 😲 Surprise | 19 | 4 lần nhanh (100ms) | Ngạc nhiên, nháy nhanh |
| 😐 Neutral | 21 | 1 lần trung bình (500ms) | Bình thường |
| 🤢 Disgust | 22 | 2 lần chậm (150ms) | Ghê tởm |

---

## 💻 Công nghệ sử dụng

**Python Backend:**
| Thư viện | Phiên bản | Dùng để |
|---|---|---|
| `deepface` | 0.0.93 | Nhận diện cảm xúc (TensorFlow) |
| `fer` | 22.5.1 | Nhận diện cảm xúc (PyTorch) |
| `opencv-python` | 4.9.x | Đọc webcam, xử lý frame |
| `paho-mqtt` | 1.6.x | Giao tiếp MQTT |
| `websockets` | 12.x | WebSocket server cho dashboard |
| `tensorflow` | 2.15.0 | Backend cho DeepFace |
| `torch` | 2.2.x | Backend cho FER |

**ESP32 Firmware:**
| Thư viện | Dùng để |
|---|---|
| `PubSubClient` | Subscribe MQTT |
| `ArduinoJson` | Parse JSON payload |
| `WiFi.h` | Kết nối WiFi |

**MQTT Broker:** HiveMQ Public — `broker.hivemq.com:1883` (free, không cần đăng ký)

---

## ⚠️ Giới hạn nhận diện

Hệ thống có thể giảm độ chính xác trong các trường hợp sau:

**Ánh sáng:**
- 🔆 Ánh sáng quá mạnh hoặc ngược sáng → mặt bị cháy sáng, model không detect được
- 🌑 Ánh sáng quá tối (dưới 100 lux) → mặt bị tối, confidence giảm mạnh
- 💡 Ánh đèn vàng / đèn huỳnh quang → ảnh hưởng màu da, dễ nhầm cảm xúc

**Camera:**
- 📷 Webcam độ phân giải thấp (< 480p) → thiếu chi tiết khuôn mặt
- 🎥 Camera bị mờ, bẩn ống kính → giảm chất lượng frame
- 📐 Góc nghiêng mặt > 30° → model khó nhận diện landmark
- 👓 Đeo kính → che khuất vùng mắt, dễ nhầm `neutral` ↔ `surprise`

**Người dùng:**
- 😐 Biểu cảm không rõ ràng → model thiên về `neutral`
- 🧔 Râu, tóc che mặt → giảm chính xác
- 👶 Trẻ em, người cao tuổi → dataset train chủ yếu là người trưởng thành
- 🌏 Người Á Đông → model gốc train nhiều dữ liệu người Tây, có thể lệch kết quả

**Khuyến nghị để đạt kết quả tốt nhất:**
- Ngồi trước nguồn sáng trắng từ phía trước mặt
- Khoảng cách 40-60cm từ webcam
- Biểu cảm rõ ràng, giữ nguyên 1-2 giây
- Tháo kính nếu hệ thống nhận diện sai

---

## 🚀 Hướng dẫn cài đặt

### 1. Clone repo
```bash
git clone https://github.com/khanhly-dn/Emotion_Aware_SmartRoom_IoT.git
cd Emotion_Aware_SmartRoom_IoT
```

### 2. Cài thư viện Python
```bash
pip install -r requirements.txt
```

### 3. Nạp firmware vào ESP32
- Mở `esp32_emotion_led.ino` trong Arduino IDE
- Cài thư viện: `PubSubClient` + `ArduinoJson`
- Chỉnh WiFi trong file:
```cpp
const char* WIFI_SSID     = "Tên_WiFi";
const char* WIFI_PASSWORD = "Mật_khẩu";
```
- Chọn board: **ESP32 Dev Module** → Nạp code

### 4. Chỉnh cấu hình (nếu cần)
Mở `config.py` để thay đổi GPIO, broker, camera index...

---

## ▶️ Thứ tự chạy

**Bước 1** — Test ESP32 + LED:
```bash
python test_mqtt.py --loop
```
Thấy LED nhấp nháy → bấm Ctrl+C

**Bước 2** — Mở Web Dashboard:
```
Double click vào web/index.html
```

**Bước 3** — Chạy hệ thống chính:
```bash
python emotion_detector.py
```
Để mặt vào webcam — bấm **Q** để thoát

---

## 📁 Cấu trúc project

```
Emotion_Aware_SmartRoom_IoT/
├── python/
│   ├── config.py               # Cấu hình tập trung
│   ├── emotion_detector.py     # File chính — chạy cái này
│   ├── test_mqtt.py            # Test MQTT + ESP32
│   ├── test_emotion.py         # Test DeepFace đơn lẻ
│   └── requirements.txt        # Thư viện Python
├── esp32/
│   └── esp32_emotion_led.ino   # Firmware ESP32
├── web/
│   └── index.html              # Web Dashboard
└── README.md
```

---

## 🔭 Hướng phát triển

- [ ] Thêm **DFPlayer Mini** để phát nhạc theo cảm xúc
- [ ] Tích hợp **LED RGB** thay LED đơn — đổi màu theo cảm xúc
- [ ] Train lại model trên **dataset người Á Đông** để tăng độ chính xác
- [ ] Thêm **điều khiển âm lượng nhạc** tự động theo cảm xúc
- [ ] Tích hợp **Node-RED / Home Assistant**
- [ ] Hỗ trợ **nhiều người dùng** cùng lúc

---

## 👤 Thực hiện

**Lý Gia Khánh**  
Khoa Công nghệ Thông tin — Trường Đại học Đại Nam

---

<p align="center">
  Using Python · TensorFlow · PyTorch · ESP32 · MQTT · WebSocket
</p>
