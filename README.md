# Demo CI/CD với Jenkins: Flask app (Đề tài 37, Nhóm 3GIT)

Pipeline: **git push → Checkout → Build → Test → Deploy**, tự động chạy khi push lên GitHub.

## Cấu trúc

| File | Vai trò |
|---|---|
| `app.py` | Ứng dụng Flask: `/`, `/health`, `/api/sum?a=&b=` |
| `test_app.py` | Test pytest (Jenkins chạy ở stage Test) |
| `requirements.txt` | Thư viện Python |
| `Jenkinsfile` | Định nghĩa pipeline 4 stage |
| `deploy/flask-demo.service` | Dịch vụ systemd để chạy app sau khi deploy |
| `deploy/activate-release.sh` | Kích hoạt bản đã qua test và khôi phục bản trước khi kiểm tra khởi động thất bại |

## 1. Cài Jenkins trên Ubuntu 24.04 LTS

```bash
sudo apt update
sudo apt install -y fontconfig openjdk-21-jre python3-venv git curl
sudo install -d -m 0755 /etc/apt/keyrings
sudo curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2026.key \
  -o /etc/apt/keyrings/jenkins-keyring.asc
sudo chmod 0644 /etc/apt/keyrings/jenkins-keyring.asc
echo "deb [signed-by=/etc/apt/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" \
  | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt update
sudo apt install -y jenkins
sudo systemctl enable --now jenkins
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

Mở `http://<IP>:8080`, dán mật khẩu, chọn **Install suggested plugins**, tạo tài khoản admin.

## 2. Chuẩn bị thư mục phát hành và dịch vụ

```bash
sudo install -d -o jenkins -g jenkins -m 0755 /opt/flask-demo /opt/flask-demo/releases
sudo install -m 0644 deploy/flask-demo.service /etc/systemd/system/flask-demo.service
sudo systemctl daemon-reload
sudo systemctl enable flask-demo
sudo visudo -f /etc/sudoers.d/jenkins-flask-demo
```

Lưu dòng sau vào file sudoers. Nếu đã cài theo hướng dẫn cũ, hãy thay dòng cũ bằng dòng này.

```sudoers
jenkins ALL=(root) NOPASSWD: /usr/bin/systemctl restart flask-demo.service, /usr/bin/systemctl stop flask-demo.service
```

Nếu nâng cấp từ bản cũ chạy trong workspace Jenkins, thực hiện lại bước này trước khi chạy build đầu tiên. Nếu build đầu tiên thất bại hoặc máy khởi động lại trước khi có bản phát hành, hoàn tất một build thành công để dịch vụ có bản chạy từ `/opt/flask-demo/current`.

## 3. Đẩy code lên GitHub

Tạo một repo trống trên GitHub (ví dụ `flask-demo`), rồi trong thư mục này chạy:

```bash
git init
git add .
git commit -m "Demo CI/CD Jenkins"
git branch -M main
git remote add origin https://github.com/<tai-khoan>/flask-demo.git
git push -u origin main
```

Nếu repo để **private**, Jenkins cần Credentials (GitHub Personal Access Token) để lấy code. Để **public** cho đơn giản.

## 4. Tạo job Pipeline

1. Đảm bảo code đã nằm trên GitHub (bước 3).
2. Jenkins → **New Item** → đặt tên **`flask-demo`** → chọn **Pipeline**. Job chạy trên node `built-in` của máy đã cài service. Bật ít nhất một executor cho node này.
3. Chọn trigger theo bước 5.
4. **Pipeline**: *Pipeline script from SCM* → Git → URL repo, branch `*/main`, Script Path `Jenkinsfile`.
5. Bấm **Build Now** một lần để chạy thử.

## 5. Kích hoạt tự động khi push

Chọn **một** trong hai cách:

**Cách A: Webhook (chạy ngay khi push).** Cần Jenkins có địa chỉ mà GitHub gọi tới được.
Trong Jenkins, tick *GitHub hook trigger for GITScm polling*.
Repo → **Settings → Webhooks → Add webhook**:
- Payload URL: `http://<IP-public>:8080/github-webhook/` (có dấu `/` ở cuối)
- Content type: `application/json`, sự kiện *Just the push event*

Máy không có IP public (laptop, máy ảo, mạng trường) thì dùng ngrok:
```bash
sudo snap install ngrok
ngrok config add-authtoken <token lấy trên ngrok.com>
ngrok http 8080
```
Lấy URL `https://....ngrok-free.app` + `/github-webhook/` làm Payload URL. Mỗi lần chạy lại ngrok URL sẽ đổi, phải cập nhật webhook.

**Cách B: Poll SCM (không cần IP public, đơn giản nhất).**
Job → Configure → Triggers → tick **Poll SCM**, Schedule: `H/2 * * * *`.
Jenkins tự kiểm tra GitHub khoảng 2 phút/lần, có commit mới thì chạy. Demo sẽ trễ tối đa ~2 phút sau khi push.

## 6. Chạy demo

**Checklist trước khi lên thuyết trình**
- [ ] Đã chạy job thành công ít nhất 1 lần (ứng dụng đang chạy ở cổng 5000)
- [ ] Mở sẵn: VS Code/terminal ở repo, trang Stage View của job, trang `http://<IP>:5000`
- [ ] Đã thử push thật một lần và thấy Jenkins tự chạy
- [ ] Có sẵn video quay màn hình hai kịch bản để dự phòng mạng lỗi

**Kịch bản 1: thành công**
1. Ghi lại version hiện tại trên trang ứng dụng.
2. Tăng `APP_VERSION` trong `app.py`, ví dụ từ `1.1.0` lên `1.1.1`.
3. `git commit -am "Cap nhat version" && git push`
4. Jenkins tự chạy build mới, 4 stage Checkout → Build → Test → Deploy đều xanh.
5. Tải lại trang ứng dụng để kiểm tra version mới.

**Kịch bản 2: test lỗi, không triển khai**
1. Trong `test_app.py`, bỏ dấu `#` ở 2 dòng `test_demo_fail`.
2. `git commit -am "Them test loi" && git push`
3. Stage Test báo đỏ, pipeline dừng, Deploy bị bỏ qua.
4. Tải lại trang ứng dụng: vẫn là bản cũ.
5. Mở **Test Result** trong build để chỉ ra test sai. Comment lại 2 dòng đó, push để pipeline xanh trở lại.

## Lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| Stage Build lỗi `ensurepip is not available` | `sudo apt install python3-venv` |
| Stage Checkout yêu cầu chuẩn bị bản phát hành | Thực hiện bước 2 và chạy `sudo systemctl daemon-reload` |
| Stage Deploy lỗi `sudo: a password is required` | Kiểm tra hai lệnh và tên `flask-demo.service` trong file sudoers ở bước 2 |
| Deploy xong nhưng `curl` báo lỗi | Xem log: `sudo journalctl -u flask-demo -n 50` |
| Push mà Jenkins không chạy | Kiểm tra webhook (Recent Deliveries trên GitHub) hoặc dùng Poll SCM |
| Ứng dụng không mở được từ máy khác | `sudo ufw allow 5000` |

## Chạy thử trên máy cá nhân

```bash
python3 -m venv venv && venv/bin/pip install -r requirements.txt
venv/bin/pytest -v
venv/bin/python app.py   # http://localhost:5000
```
