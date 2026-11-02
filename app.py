"""Ứng dụng Flask mẫu cho demo CI/CD với Jenkins (Đề tài 37 - Nhóm 3GIT)."""
from flask import Flask, jsonify, request

app = Flask(__name__)
app.json.ensure_ascii = False  # hiển thị tiếng Việt có dấu trên trình duyệt

# Khi demo: sửa dòng này rồi push lên GitHub để thấy Jenkins tự triển khai bản mới
APP_VERSION = "1.0.0"
MESSAGE = "Xin chào từ Jenkins CI/CD - Nhóm 3GIT!"


def add(a, b):
    """Hàm cộng đơn giản, được kiểm thử trong test_app.py."""
    return a + b


@app.route("/")
def index():
    return jsonify(message=MESSAGE, version=APP_VERSION)


@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/api/sum")
def api_sum():
    try:
        a = float(request.args.get("a", 0))
        b = float(request.args.get("b", 0))
    except ValueError:
        return jsonify(error="a và b phải là số"), 400
    return jsonify(a=a, b=b, result=add(a, b))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
