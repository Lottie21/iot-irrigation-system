# camera_server.py (带人脸检测+拍照保存版本)
from flask import Flask, Response, jsonify, send_file
from picamera2 import Picamera2
import cv2
import socket
import time
import threading
import os
from datetime import datetime

app = Flask(__name__)

# 创建照片保存目录
PHOTO_DIR = '/home/pi5/Desktop/face_photos'
os.makedirs(PHOTO_DIR, exist_ok=True)

# 摄像头初始化
camera = Picamera2()
config = camera.create_video_configuration(main={"size": (640, 480)})
camera.configure(config)

# 设置自动白平衡和自动曝光
camera.set_controls({"AwbEnable": True, "AeEnable": True})

camera.start()
time.sleep(2)  # 等待2秒让相机自动调整

# 加载人脸检测器
face_cascade = cv2.CascadeClassifier('/home/pi5/Desktop/haarcascade_frontalface_default.xml')

# 人脸检测状态
last_detection_time = 0
detection_cooldown = 5  # 5秒内不重复检测

def send_notification_to_tablet():
    """发送人脸检测通知到平板"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        message = "FACE_DETECTED"
        s.sendto(message.encode(), ("172.20.10.3", 8888))
        s.close()
        print("[人脸检测] 已通知平板")
    except Exception as e:
        print(f"[人脸检测] 通知失败: {e}")

def save_face_photo(frame):
    """保存人脸照片"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{PHOTO_DIR}/face_{timestamp}.jpg"
    cv2.imwrite(filename, frame)
    print(f"[人脸检测] 照片已保存: {filename}")
    return filename

def generate_frames():
    global last_detection_time
    
    while True:
        # 捕获画面（RGB格式）
        frame = camera.capture_array()
        
        # 转换为BGR格式（OpenCV需要）
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # 转换为灰度图（用于人脸检测）
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        
        # 检测人脸
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        # 如果检测到人脸
        if len(faces) > 0:
            current_time = time.time()
            if current_time - last_detection_time > detection_cooldown:
                last_detection_time = current_time
                # 保存照片（保存BGR格式）
                threading.Thread(target=save_face_photo, args=(frame_bgr.copy(),)).start()
                # 通知平板
                threading.Thread(target=send_notification_to_tablet).start()
            
            # 在画面上画框
            for (x, y, w, h) in faces:
                cv2.rectangle(frame_bgr, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame_bgr, "Face", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        
        # 编码为JPEG
        ret, buffer = cv2.imencode('.jpg', frame_bgr)
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/face_photos')
def face_photos():
    """返回人脸照片列表"""
    photos = sorted([f for f in os.listdir(PHOTO_DIR) if f.endswith('.jpg')], reverse=True)
    photo_list = []
    for photo in photos[:20]:  # 最近20张
        photo_list.append({
            'filename': photo,
            'timestamp': photo.replace('face_', '').replace('.jpg', ''),
            'url': f'http://172.20.10.2:5000/photo/{photo}'
        })
    return jsonify(photo_list)

@app.route('/photo/<filename>')
def get_photo(filename):
    """获取单张照片"""
    return send_file(f"{PHOTO_DIR}/{filename}", mimetype='image/jpeg')

@app.route('/delete_photo/<filename>', methods=['POST'])
def delete_photo(filename):
    """删除照片"""
    try:
        filepath = f"{PHOTO_DIR}/{filename}"
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({"status": "ok", "message": "删除成功"})
        else:
            return jsonify({"status": "error", "message": "文件不存在"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("摄像头服务器启动（带人脸检测+拍照）")
    print(f"照片保存路径: {PHOTO_DIR}")
    app.run(host='0.0.0.0', port=5000, threaded=True)