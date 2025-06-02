from flask import Blueprint, request, session, jsonify
from utils.database import get_db_connection, get_dict_cursor_connection
import os
import json
from datetime import datetime
from yolo_predictor import run_inference

product_bp = Blueprint('product', __name__, url_prefix='/product')

# 구독하기 (IOT 설정)
@product_bp.route('/subscribe', methods=['POST'])
def subscribe_iot():
    if 'user_id' not in session:
        return jsonify({"message": "로그인이 필요합니다", "success": False}), 401

    try:
        data = request.get_json()
        iot_name = data.get('iot_name')
        gh_id = data.get('gh_id')
        capture_interval = data.get('capture_interval', '15')
        direction = data.get('direction', 'both')
        resolution = data.get('resolution', '1280x720')
        camera_on = data.get('camera_on', True)

        conn = get_db_connection()
        if not conn:
            return jsonify({"message": "DB 연결 실패", "success": False}), 500

        try:
            with conn.cursor() as cur:
                sql = """
                    INSERT INTO iot (iot_name, owner_id, gh_id, capture_interval, direction, resolution, camera_on)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cur.execute(sql, (
                    iot_name, session['user_id'], gh_id, capture_interval, direction, resolution, camera_on
                ))
                conn.commit()
                return jsonify({"message": "IOT 구독이 완료되었습니다", "success": True}), 200
        finally:
            conn.close()

    except Exception as e:
        print(f"[에러] IOT 구독 중 오류 발생: {e}")
        return jsonify({"message": "서버 내부 오류", "success": False}), 500

# 내 구독 목록 조회
@product_bp.route('/my_devices', methods=['GET'])
def my_devices():
    if 'user_id' not in session:
        return jsonify({"message": "로그인이 필요합니다"}), 401

    conn, cursor = get_dict_cursor_connection()
    if not conn or not cursor:
        return jsonify({"message": "DB 연결 실패"}), 500

    try:
        cursor.execute("""
            SELECT i.*, g.greenhouse_name
            FROM iot i
            LEFT JOIN greenhouses g ON i.gh_id = g.id
            WHERE i.owner_id = %s
        """, (session['user_id'],))
        devices = cursor.fetchall()
        return jsonify({"devices": devices})
    finally:
        cursor.close()
        conn.close()

# 내 비닐하우스 목록 조회
@product_bp.route('/my_greenhouses', methods=['GET'])
def my_greenhouses():
    if 'user_id' not in session:
        return jsonify({"message": "로그인이 필요합니다"}), 401

    conn, cursor = get_dict_cursor_connection()
    if not conn or not cursor:
        return jsonify({"message": "DB 연결 실패"}), 500

    try:
        sql = """
            SELECT g.id, g.greenhouse_name, g.farm_id
            FROM greenhouses g
            JOIN farms f ON g.farm_id = f.id
            WHERE f.owner_username = %s
        """
        cursor.execute(sql, (session['user_id'],))
        greenhouses = cursor.fetchall()
        return jsonify({"greenhouses": greenhouses})
    finally:
        cursor.close()
        conn.close()

# 설정 읽기용 get api
@product_bp.route('/camera-config', methods=['GET'])
def get_camera_config():
    try:
        with open("camera_config.json", "r") as f:
            config = json.load(f)
        return jsonify(config), 200
    except Exception as e:
        return jsonify({"error": f"설정 파일을 읽을 수 없습니다: {str(e)}"}), 500

# IOT 카메라 설정 저장
@product_bp.route('/camera-config', methods=['POST'])
def save_camera_config():
    config = request.get_json()
    with open("camera_config.json", "w") as f:
        json.dump(config, f)
    return jsonify({"message": "설정 저장 완료"}), 200

#이미지 파일 업로드
@product_bp.route('/upload-image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return "파일 없음", 400

    file = request.files['file']
    filename = file.filename
    save_path = os.path.join("static", "images", filename)
    file.save(save_path)

    return f"저장 완료: {filename}", 200

# 센서 데이터 수신
@product_bp.route('/upload-sensor', methods=['POST'])
def upload_sensor():
    data = request.get_json()
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    timestamp = data.get('timestamp', datetime.now().isoformat())
    iot_id = data.get('iot_id')
    gh_id = data.get('gh_id')

    print(f"[DEBUG] 수신 데이터: temp={temperature}, hum={humidity}, iot_id={iot_id}, gh_id={gh_id}")


    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO sensor_log (temperature, humidity, timestamp, iot_id, gh_id)
                VALUES (%s, %s, %s,%s,%s)
            """
            cursor.execute(sql, (temperature, humidity, timestamp,iot_id,gh_id))
            conn.commit()  
        return jsonify({"status": "success"}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


@product_bp.route("/last-sensor", methods=["GET"])
def get_last_sensor():
    try:
        # 최신 센서 데이터 가져오기
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT temperature, humidity, timestamp FROM sensor_log ORDER BY timestamp DESC LIMIT 1")
            row = cursor.fetchone()
        
        # 센서 데이터 준비
        if row:
            temperature, humidity, timestamp = row
        else:
            temperature, humidity, timestamp = None, None, None

        # 모델 추론 수행 (last.jpg에 대해)
        image_path = "test_images/last.jpg"  # 실제 추론 대상 이미지 경로
        class_counts, _ = run_inference(image_path)

        # 결과에서 썩은 것 / 건강한 것 추출
        rotten_count = class_counts.get("straw_rotten", 0)
        healthy_count = class_counts.get("straw_healthy", 0)

        # JSON 응답 구성
        response = {
            "temperature": temperature,
            "humidity": humidity,
            "timestamp": timestamp.isoformat() if timestamp else None,
            "image_url": "/static/images/last.jpg",
            "rotten_count": rotten_count,
            "healthy_count": healthy_count,
            "predicted_image_url": "/static/images/last_pred.jpg"
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


#구독 취소
@product_bp.route('/unsubscribe/<int:iot_id>', methods=['DELETE'])
def unsubscribe_iot(iot_id):
    if 'user_id' not in session:
        return jsonify({"message": "로그인이 필요합니다"}), 401

    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "DB 연결 실패"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM iot WHERE id = %s AND owner_id = %s", (iot_id, session['user_id']))
            conn.commit()
            return jsonify({"message": "구독이 취소되었습니다"}), 200
    finally:
        conn.close()

#iot 설정 수정
@product_bp.route('/update/<int:iot_id>', methods=['POST'])
def update_iot(iot_id):
    if 'user_id' not in session:
        return jsonify({"message": "로그인이 필요합니다"}), 401

    data = request.get_json()
    iot_name = data.get('iot_name')
    gh_id = data.get('gh_id')
    capture_interval = data.get('capture_interval')
    direction = data.get('direction')
    resolution = data.get('resolution')
    camera_on = data.get('camera_on')

    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "DB 연결 실패"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE iot
                SET iot_name = %s, gh_id = %s, capture_interval = %s,
                    direction = %s, resolution = %s, camera_on = %s
                WHERE id = %s AND owner_id = %s
            """, (iot_name, gh_id, capture_interval, direction, resolution, camera_on, iot_id, session['user_id']))
            conn.commit()
            return jsonify({"message": "IOT 정보가 수정되었습니다"}), 200
    finally:
        conn.close()

#iot 조회
@product_bp.route('/my_devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    if 'user_id' not in session:
        return jsonify({"message": "로그인이 필요합니다"}), 401

    conn, cursor = get_dict_cursor_connection()
    if not conn or not cursor:
        return jsonify({"message": "DB 연결 실패"}), 500

    try:
        cursor.execute("""
            SELECT i.*, g.greenhouse_name, g.farm_id
            FROM iot i
            LEFT JOIN greenhouses g ON i.gh_id = g.id
            WHERE i.id = %s AND i.owner_id = %s
        """, (device_id, session['user_id']))
        device = cursor.fetchone()

        if not device:
            return jsonify({"message": "디바이스를 찾을 수 없습니다"}), 404

        return jsonify({"device": device}), 200
    except Exception as e:
        print(f"[에러] IoT 디바이스 조회 중 오류 발생: {e}")
        return jsonify({"message": "서버 내부 오류"}), 500
    finally:
        cursor.close()
        conn.close()