"""
config.py
=========
Toàn bộ cấu hình tập trung tại đây.
Chỉ cần chỉnh file này, không cần đụng file khác.
"""

# ─────────────────────────────────────────────
# MQTT
# ─────────────────────────────────────────────
MQTT_BROKER    = "broker.hivemq.com"
MQTT_PORT      = 1883
MQTT_TOPIC     = "smartroom/emotion"
MQTT_CLIENT_ID = "emotion-detector-py"

# ─────────────────────────────────────────────
# WEBSOCKET (dashboard)
# ─────────────────────────────────────────────
WS_HOST = "0.0.0.0"
WS_PORT = 8765

# ─────────────────────────────────────────────
# CAMERA
# ─────────────────────────────────────────────
CAMERA_INDEX  = 0
DETECT_EVERY  = 0.8   # detect nhanh hơn

# ─────────────────────────────────────────────
# MAPPING: cảm xúc → GPIO ESP32
# ─────────────────────────────────────────────
LED_GPIO_MAP = {
    "happy":    2,
    "sad":      4,
    "angry":    5,
    "fear":     18,
    "surprise": 19,
    "neutral":  21,
    "disgust":  22,
}

# ─────────────────────────────────────────────
# DEEPFACE
# ─────────────────────────────────────────────
DEEPFACE_BACKEND  = "mtcnn"   # mtcnn chính xác hơn opencv nhiều
DEEPFACE_MODEL    = "Emotion"
ENFORCE_DETECTION = False

# Chỉ publish khi confidence đủ cao — tránh kết quả sai
MIN_CONFIDENCE = 60.0

# ─────────────────────────────────────────────
# EMOTION METADATA
# ─────────────────────────────────────────────
EMOTION_META = {
    "happy":    {"vi": "Vui vẻ",      "emoji": "😊"},
    "sad":      {"vi": "Buồn bã",     "emoji": "😢"},
    "angry":    {"vi": "Tức giận",    "emoji": "😠"},
    "fear":     {"vi": "Sợ hãi",      "emoji": "😨"},
    "surprise": {"vi": "Ngạc nhiên",  "emoji": "😲"},
    "neutral":  {"vi": "Bình thường", "emoji": "😐"},
    "disgust":  {"vi": "Ghê tởm",     "emoji": "🤢"},
}
