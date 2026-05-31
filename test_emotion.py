"""
test_emotion.py
===============
Test DeepFace với ảnh tĩnh hoặc webcam 1 frame.
Dùng trước khi chạy emotion_detector.py để chắc chắn
DeepFace hoạt động đúng trên máy của bạn.

Cách chạy:
  python test_emotion.py                    # chụp 1 frame từ webcam rồi phân tích
  python test_emotion.py --image foto.jpg   # phân tích ảnh có sẵn
  python test_emotion.py --benchmark        # đo tốc độ detect
"""
import cv2
import time
import argparse
import sys
from deepface import DeepFace
from config import DEEPFACE_BACKEND, ENFORCE_DETECTION, EMOTION_META

# PHÂN TÍCH 1 FRAME
def analyze_frame(frame, verbose: bool = True):
    """
    Phân tích cảm xúc từ 1 frame numpy array.
    Trả về dict kết quả hoặc None nếu lỗi.
    """
    start = time.time()
    try:
        result = DeepFace.analyze(
            frame,
            actions=["emotion"],
            detector_backend=DEEPFACE_BACKEND,
            enforce_detection=ENFORCE_DETECTION,
            silent=True,
        )
        elapsed = time.time() - start

        if isinstance(result, list):
            result = result[0]

        dominant  = result["dominant_emotion"]
        emotions  = result["emotion"]
        meta      = EMOTION_META.get(dominant, {"emoji": "❓", "vi": dominant})

        if verbose:
            print(f"\n{'='*50}")
            print(f"  Kết quả phân tích ({elapsed:.2f}s)")
            print(f"{'='*50}")
            print(f"  Cảm xúc chính: {meta['emoji']}  {dominant} ({meta['vi']})")
            print(f"  Backend: {DEEPFACE_BACKEND}")
            print(f"\n  Chi tiết tất cả cảm xúc:")
            # Sắp xếp theo độ tin cậy giảm dần
            for emotion, score in sorted(emotions.items(), key=lambda x: x[1], reverse=True):
                bar_len = int(score / 5)
                bar     = "█" * bar_len + "░" * (20 - bar_len)
                marker  = " ◀ dominant" if emotion == dominant else ""
                print(f"    {emotion:<10} {bar} {score:5.1f}%{marker}")
            print(f"{'='*50}\n")

        return {
            "dominant":   dominant,
            "confidence": round(emotions[dominant], 2),
            "all":        emotions,
            "elapsed":    elapsed,
        }

    except Exception as e:
        elapsed = time.time() - start
        print(f"\n  ❌ Lỗi phân tích ({elapsed:.2f}s): {e}")
        if "Face could not be detected" in str(e):
            print("     → Không tìm thấy khuôn mặt trong ảnh.")
            print("     → Thử chụp rõ hơn hoặc dùng --image với ảnh có khuôn mặt.")
        return None

# CHỤP FRAME TỪ WEBCAM
def capture_from_webcam(camera_index: int = 0):
    print(f"[CAM] Mở webcam (index={camera_index})…")
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print(f"  ❌ Không mở được webcam index={camera_index}")
        sys.exit(1)

    for _ in range(5):
        cap.read()

    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        print("  ❌ Không đọc được frame từ webcam")
        sys.exit(1)

    print(f"  ✅ Chụp frame: {frame.shape[1]}x{frame.shape[0]} px")
    return frame

# BENCHMARK
def benchmark(camera_index: int = 0, rounds: int = 10):
    print(f"\n[BENCHMARK] {rounds} lần detect — backend={DEEPFACE_BACKEND}")
    print("-" * 50)

    frame = capture_from_webcam(camera_index)
    times = []

    for i in range(rounds):
        start = time.time()
        result = DeepFace.analyze(
            frame,
            actions=["emotion"],
            detector_backend=DEEPFACE_BACKEND,
            enforce_detection=ENFORCE_DETECTION,
            silent=True,
        )
        elapsed = time.time() - start
        times.append(elapsed)

        dominant = result[0]["dominant_emotion"] if isinstance(result, list) else result["dominant_emotion"]
        print(f"  Round {i+1:2d}: {elapsed:.3f}s  →  {dominant}")

    avg = sum(times) / len(times)
    mn  = min(times)
    mx  = max(times)
    fps = 1 / avg

    print("-" * 50)
    print(f"  Trung bình : {avg:.3f}s  ({fps:.1f} FPS)")
    print(f"  Nhanh nhất : {mn:.3f}s")
    print(f"  Chậm nhất  : {mx:.3f}s")

    if avg > 2.0:
        print("\n  ⚠ Máy hơi chậm. Khuyến nghị:")
        print("    - Tăng DETECT_EVERY trong config.py (vd: 3.0)")
        print("    - Hoặc giữ nguyên, DeepFace sẽ chạy background thread")
    else:
        print(f"\n  ✅ Ổn! Có thể detect mỗi {avg:.1f}s")

# MAIN
def main():
    parser = argparse.ArgumentParser(description="Test DeepFace emotion detection")
    parser.add_argument("--image",     type=str, default=None,
                        help="Đường dẫn ảnh để phân tích (jpg/png)")
    parser.add_argument("--camera",    type=int, default=0,
                        help="Camera index (mặc định: 0)")
    parser.add_argument("--benchmark", action="store_true",
                        help="Đo tốc độ detect")
    parser.add_argument("--rounds",    type=int, default=10,
                        help="Số lần đo trong benchmark (mặc định: 10)")
    args = parser.parse_args()

    print("\n[INFO] Đang load DeepFace model lần đầu (có thể mất 10-30s)…")

    if args.benchmark:
        benchmark(args.camera, args.rounds)
        return

    if args.image:
        # ── Phân tích ảnh có sẵn ──────────────────
        print(f"[IMG] Đọc ảnh: {args.image}")
        frame = cv2.imread(args.image)
        if frame is None:
            print(f"  ❌ Không đọc được ảnh: {args.image}")
            sys.exit(1)
        print(f"  ✅ Kích thước: {frame.shape[1]}x{frame.shape[0]} px")
    else:
        # ── Chụp từ webcam ─────────────────────────
        frame = capture_from_webcam(args.camera)

    # Phân tích
    result = analyze_frame(frame)

    if result:
        # Hiển thị frame với kết quả
        label = f"{result['dominant']} ({result['confidence']:.0f}%)"
        cv2.putText(frame, label, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 100), 2)
        cv2.imshow("Emotion Test — press any key to close", frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        # Lưu ảnh kết quả
        out_path = "test_result.jpg"
        cv2.imwrite(out_path, frame)
        print(f"[SAVE] Lưu ảnh kết quả: {out_path}")

if __name__ == "__main__":
    main()
