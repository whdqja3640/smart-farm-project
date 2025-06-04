import pymysql
import os
from flask import Flask, render_template, request, session, jsonify
from datetime import datetime

from routes.user import user_bp
from routes.admin import admin_bp
from routes.farm import farm_bp
from routes.weather import weather_bp
from config import DB_CONFIG
from routes.post import post_bp
from routes.product import product_bp
from routes.crop import crop_bp
from routes.chart import chart_bp
from routes.greenhouse import greenhouse_bp
from flask_cors import CORS

def get_db_conn():
    return pymysql.connect(**DB_CONFIG)
conn = get_db_conn()
cur = conn.cursor()
UPLOAD_FOLDER = 'static/uploads/farms'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_url_path='/static', static_folder='static')

app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True

CORS(app, resources={r"/*": {"origins": [
    "https://mature-grub-climbing.ngrok-free.app"
]}}, supports_credentials=True)

app.register_blueprint(user_bp)
app.register_blueprint(farm_bp, url_prefix='/api/farms')
app.register_blueprint(post_bp)
app.register_blueprint(crop_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(weather_bp)
app.register_blueprint(product_bp)
app.register_blueprint(chart_bp)
app.register_blueprint(greenhouse_bp, url_prefix='/api/greenhouses')

def get_db_connection():
    try:
        return pymysql.connect(**DB_CONFIG)
    except pymysql.MySQLError as e:
        print(f"DB 연결 실패: {e}")
        return None

@app.route('/')
def home():
    username = session.get('user_id')  #로그인한 유저 이름
    usernickname = session.get('nickname')

    farms = []

    if username:
        conn = get_db_connection()
        cur = conn.cursor(pymysql.cursors.DictCursor)
        sql = "SELECT * FROM farms WHERE owner_username = %s"
        cur.execute(sql, (username,))
        farms = cur.fetchall()
        conn.close()

    return render_template('my_farms.html',farms=farms)

app.secret_key = 'your_secret_key'  # 세션에 필요한 비밀키 (랜덤한 문자열)


# 센서 및 추론 테스트 페이지
@app.route("/sensor")
def sensor_page():
    return render_template("sensor.html")


#GPS 데이터 수신
@app.route('/upload-gps', methods=['POST'])
def upload_gps():
    data = request.get_json()
    device_id = data.get('device_id')
    lat = data.get('lat')
    lon = data.get('lon')

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            if not all([device_id, lat, lon]):
                return jsonify({"status": "fail", "message": "invalid data"}), 400

            sql = """
                INSERT INTO gps_data (device_id, latitude, longitude)
                VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (device_id, lat, lon))
            conn.commit()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "meesage": str(e)}), 500


#지도에 마커 표시
@app.route('/get-latest', methods=['GET'])
def get_latest():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT latitude, longitude FROM gps_data 
                ORDER BY received_at DESC LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                return jsonify({'lat': row[0], 'lon': row[1]})
            else:
                return jsonify({"message": "No data"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)