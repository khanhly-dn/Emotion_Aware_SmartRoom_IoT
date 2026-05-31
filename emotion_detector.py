"""
emotion_detector.py
====================
Emotion-Aware Smart Room — Python Client
Dùng cả FER + DeepFace để xác nhận chéo, tăng độ chính xác
"""

import cv2
import json
import time
import threading
import asyncio
import collections
import websockets
from fer import FER
from deepface import DeepFace
import paho.mqtt.client as mqtt
from config import (
    MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, MQTT_CLIENT_ID,
    WS_HOST, WS_PORT,
    CAMERA_INDEX, DETECT_EVERY,
    LED_GPIO_MAP, DEEPFACE_BACKEND, ENFORCE_DETECTION,
    MIN_CONFIDENCE,
)

# ── Khởi tạo FER detector ──────────────────────
fer_detector = FER(mtcnn=True)

connected_ws_clients: set = set()
latest_state: dict = {
    "emotion":    "neutral",
    "confidence": 0.0,
    "gpio":       21,
    "timestamp":  time.time(),
}

# Buffer lưu 5 kết quả gần nhất để lấy majority vote
emotion_buffer = collections.deque(maxlen=5)


# ══════════════════════════════════════════════
# MQTT
# ══════════════════════════════════════════════
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[MQTT] Connected to {MQTT_BROKER}")
    else:
        print(f"[MQTT] Failed — code {rc}")

mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_ID)
mqtt_client.on_connect = on_connect


def publish_emotion(emotion: str, confidence: float):
    gpio = LED_GPIO_MAP.get(emotion, 21)
    payload = json.dumps({
        "emotion":    emotion,
        "confidence": round(confidence, 2),
        "gpio":       gpio,
        "ts":         time.time(),
    })
    mqtt_client.publish(MQTT_TOPIC, payload, qos=1, retain=True)
    print(f"[MQTT] {emotion} ({confidence:.1f}%) → GPIO{gpio}")


# ══════════════════════════════════════════════
# WEBSOCKET
# ══════════════════════════════════════════════
async def ws_handler(websocket):
    connected_ws_clients.add(websocket)
    try:
        await websocket.send(json.dumps(latest_state))
        async for _ in websocket:
            pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_ws_clients.discard(websocket)


async def broadcast(data: dict):
    if not connected_ws_clients:
        return
    msg = json.dumps(data)
    await asyncio.gather(
        *[ws.send(msg) for ws in connected_ws_clients],
        return_exceptions=True,
    )


def ws_broadcast_sync(data: dict):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast(data), loop)
    except Exception as e:
        print(f"[WS] Broadcast error: {e}")


async def start_ws_server():
    async with websockets.serve(ws_handler, WS_HOST, WS_PORT):
        print(f"[WS] Server running on ws://{WS_HOST}:{WS_PORT}")
        await asyncio.Future()


def run_ws_server():
    asyncio.run(start_ws_server())


# ══════════════════════════════════════════════
# DETECT BẰNG FER
# ══════════════════════════════════════════════
def detect_fer(frame):
    """Dùng FER để detect cảm xúc. Trả về (emotion, confidence) hoặc None."""
    try:
        result = fer_detector.detect_emotions(frame)
        if not result:
            return None
        emotions = result[0]["emotions"]
        dominant = max(emotions, key=emotions.get)
        confidence = emotions[dominant] * 100
        return dominant, confidence
    except Exception as e:
        print(f"[FER] Error: {e}")
        return None


# ══════════════════════════════════════════════
# DETECT BẰNG DEEPFACE
# ══════════════════════════════════════════════
def detect_deepface(frame):
    """Dùng DeepFace để detect cảm xúc. Trả về (emotion, confidence) hoặc None."""
    try:
        result = DeepFace.analyze(
            frame,
            actions=["emotion"],
            detector_backend=DEEPFACE_BACKEND,
            enforce_detection=ENFORCE_DETECTION,
            silent=True,
        )
        if isinstance(result, list):
            result = result[0]
        dominant = result["dominant_emotion"]
        confidence = result["emotion"][dominant]
        return dominant, confidence
    except Exception as e:
        print(f"[DeepFace] Error: {e}")
        return None


# ══════════════════════════════════════════════
# MAJORITY VOTE — lấy cảm xúc xuất hiện nhiều nhất
# ══════════════════════════════════════════════
def get_majority_emotion():
    if not emotion_buffer:
        return "neutral", 0.0
    count = collections.Counter(emotion_buffer)
    dominant = count.most_common(1)[0][0]
    confidence = (count[dominant] / len(emotion_buffer)) * 100
    return dominant, confidence


# ══════════════════════════════════════════════
# DETECTION LOOP
# ══════════════════════════════════════════════
def detection_loop():
    global latest_state

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("[CAM] Cannot open camera!")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print(f"[CAM] Started — FER + DeepFace dual detection")
    last_detect = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.5)
            continue

        now = time.time()

        if now - last_detect >= DETECT_EVERY:
            last_detect = now

            fer_result      = detect_fer(frame)
            deepface_result = detect_deepface(frame)

            print(f"[FER]      → {fer_result}")
            print(f"[DeepFace] → {deepface_result}")

            # ── Logic xác nhận chéo ───────────────────
            final_emotion    = None
            final_confidence = 0.0

            if fer_result and deepface_result:
                fer_emotion, fer_conf         = fer_result
                df_emotion,  df_conf          = deepface_result

                if fer_emotion == df_emotion:
                    # Cả 2 đồng ý → rất chắc chắn
                    final_emotion    = fer_emotion
                    final_confidence = (fer_conf + df_conf) / 2
                    print(f"[AGREE] Cả 2 đồng ý: {final_emotion} ({final_confidence:.1f}%)")
                else:
                    # Không đồng ý → lấy cái có confidence cao hơn
                    if fer_conf >= df_conf:
                        final_emotion, final_confidence = fer_emotion, fer_conf
                    else:
                        final_emotion, final_confidence = df_emotion, df_conf
                    print(f"[DISAGREE] Chọn: {final_emotion} ({final_confidence:.1f}%)")

            elif fer_result:
                final_emotion, final_confidence = fer_result
            elif deepface_result:
                final_emotion, final_confidence = deepface_result

            # ── Majority vote buffer ──────────────────
            if final_emotion and final_confidence >= MIN_CONFIDENCE:
                emotion_buffer.append(final_emotion)
                majority, majority_conf = get_majority_emotion()

                # Chỉ publish khi majority vote đủ mạnh (>= 60%)
                if majority_conf >= 60:
                    latest_state = {
                        "emotion":    majority,
                        "confidence": round(final_confidence, 2),
                        "gpio":       LED_GPIO_MAP.get(majority, 21),
                        "timestamp":  now,
                    }
                    publish_emotion(majority, final_confidence)
                    ws_broadcast_sync(latest_state)
            else:
                print(f"[SKIP] Confidence quá thấp hoặc không detect được mặt")

        # ── Hiển thị frame ────────────────────────────
        emotion_text = f"{latest_state['emotion']} ({latest_state['confidence']:.1f}%)"
        cv2.putText(frame, emotion_text, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 100), 2, cv2.LINE_AA)

        bar_w = int(latest_state['confidence'] * 2)
        cv2.rectangle(frame, (20, 55), (20 + bar_w, 65), (0, 255, 100), -1)

        cv2.imshow("Emotion Detector — press Q to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# ══════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════
if __name__ == "__main__":
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    mqtt_client.loop_start()

    ws_thread = threading.Thread(target=run_ws_server, daemon=True)
    ws_thread.start()

    time.sleep(1)
    detection_loop()

    mqtt_client.loop_stop()
    mqtt_client.disconnect()
