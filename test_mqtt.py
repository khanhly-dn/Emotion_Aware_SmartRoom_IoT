"""
test_mqtt.py
============
Test gửi MQTT giả — không cần webcam, không cần DeepFace.
Dùng để kiểm tra:
  1. ESP32 có nhận được lệnh không
  2. Web dashboard có cập nhật không
  3. MQTT broker có hoạt động không

Cách chạy:
  python test_mqtt.py
  python test_mqtt.py --emotion happy
  python test_mqtt.py --loop        # tự động chạy vòng tất cả cảm xúc
"""

import json
import time
import argparse
import paho.mqtt.client as mqtt
from config import (
    MQTT_BROKER, MQTT_PORT, MQTT_TOPIC,
    LED_GPIO_MAP, EMOTION_META
)

# MQTT CALLBACKS
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[MQTT] ✅ Connected to {MQTT_BROKER}:{MQTT_PORT}")
    else:
        print(f"[MQTT] ❌ Failed — code {rc}")

def on_publish(client, userdata, mid):
    print(f"[MQTT] ✅ Message published (mid={mid})")

# PUBLISH HELPER
def publish_emotion(client, emotion: str, confidence: float = 90.0):
    gpio = LED_GPIO_MAP.get(emotion, LED_GPIO_MAP["neutral"])
    meta = EMOTION_META.get(emotion, EMOTION_META["neutral"])

    payload = json.dumps({
        "emotion":    emotion,
        "confidence": round(confidence, 2),
        "gpio":       gpio,
        "ts":         time.time(),
    })

    result = client.publish(MQTT_TOPIC, payload, qos=1, retain=True)
    result.wait_for_publish()

    print(f"  {meta['emoji']}  emotion={emotion:<10} "
          f"confidence={confidence:.1f}%  gpio=GPIO{gpio}")
    return result

# MAIN
def main():
    parser = argparse.ArgumentParser(description="Test MQTT publisher")
    parser.add_argument("--emotion", type=str, default=None,
                        help="Gửi 1 cảm xúc cụ thể: happy/sad/angry/fear/surprise/neutral/disgust")
    parser.add_argument("--loop", action="store_true",
                        help="Tự động lặp qua tất cả cảm xúc mỗi 2 giây")
    parser.add_argument("--interval", type=float, default=2.0,
                        help="Giây giữa mỗi cảm xúc khi --loop (mặc định: 2.0)")
    args = parser.parse_args()

    # Kết nối MQTT
    client = mqtt.Client(client_id="test-publisher")
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()
    time.sleep(1)  # chờ kết nối

    print(f"\n[TEST] Topic: {MQTT_TOPIC}")
    print("-" * 50)

    try:
        if args.emotion:
            # ── Gửi 1 cảm xúc cụ thể ──────────────────
            if args.emotion not in LED_GPIO_MAP:
                print(f"❌ Cảm xúc không hợp lệ: {args.emotion}")
                print(f"   Hợp lệ: {', '.join(LED_GPIO_MAP.keys())}")
                return
            publish_emotion(client, args.emotion)

        elif args.loop:
            # ── Loop tất cả cảm xúc ───────────────────
            import random
            emotions = list(LED_GPIO_MAP.keys())
            print(f"[LOOP] Bắt đầu loop — interval={args.interval}s (Ctrl+C để dừng)\n")
            while True:
                for emotion in emotions:
                    conf = round(random.uniform(70.0, 99.0), 1)
                    publish_emotion(client, emotion, conf)
                    time.sleep(args.interval)

        else:
            # ── Interactive mode ───────────────────────
            print("Nhập cảm xúc để gửi (hoặc 'q' để thoát):")
            print(f"  Có thể nhập: {', '.join(LED_GPIO_MAP.keys())}\n")
            while True:
                inp = input(">>> ").strip().lower()
                if inp == "q":
                    break
                if inp not in LED_GPIO_MAP:
                    print(f"  ❌ Không hợp lệ. Thử: {', '.join(LED_GPIO_MAP.keys())}")
                    continue
                publish_emotion(client, inp)

    except KeyboardInterrupt:
        print("\n[TEST] Dừng.")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
