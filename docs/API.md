# Tài liệu API

Base URL (chạy local): `http://localhost:8080/api/v1` (đổi theo cấu hình `docker-compose.yml`/uvicorn).
Tài liệu tương tác: `/docs` (Swagger UI) và `/redoc`. Schema máy đọc được: `/openapi.json`,
bản chụp tại [`docs/openapi.json`](openapi.json).

Xuất lại bản chụp sau khi sửa API:

```powershell
venv\Scripts\python.exe -m scripts.export_openapi
```

Test `tests/api/test_openapi.py` kiểm tra `docs/openapi.json` khớp với `app.openapi()`.

## Xác thực

JWT Bearer. Lấy token bằng `POST /auth/login` (form `application/x-www-form-urlencoded`, trường `username` là email),
gửi lại trong header `Authorization: Bearer <access_token>`. Khi `access_token` hết hạn, dùng `POST /auth/refresh`
với `refresh_token`.

Vai trò: `CANDIDATE` (ứng viên) và `ADMIN`. Dependency `require_hr_or_admin` hiện chỉ cho phép `ADMIN`.
"CV access" nghĩa là ADMIN hoặc chủ sở hữu CV.

Phong bì phản hồi `ResponseSchema`: `{"success": true, "message": "Success", "data": ..., "meta": ...}`.
Một số endpoint (profile, jd, graph) trả `{"success": true, "data": ...}` hoặc dict thô, xem bảng.

## Danh sách endpoint

| Method | Đường dẫn | Auth | Mô tả | Lỗi chính |
|---|---|---|---|---|
| POST | `/auth/register` | Không | Đăng ký (201, trả `UserResponse`) | 409 email trùng, 422 |
| POST | `/auth/login` | Không | Đăng nhập, trả `access_token`, `refresh_token` | 401 sai thông tin, 403 tài khoản bị khóa, 422 |
| POST | `/auth/logout` | Bearer | Đăng xuất | 401 |
| POST | `/auth/refresh` | Không (body `refresh_token`) | Làm mới cặp token | 401 token sai loại/hết hạn/chưa xác thực, 422 |
| POST | `/auth/forgot-password` | Không | Yêu cầu đặt lại mật khẩu (luôn 200 theo thiết kế) | 422 |
| POST | `/auth/reset-password` | Không (body `token`) | Đặt lại mật khẩu | 400 token không hợp lệ/hết hạn, 422 |
| GET | `/user/me` | Bearer | Xem hồ sơ bản thân | 401 |
| PUT | `/user/me` | Bearer | Cập nhật `full_name`, `phone` | 401, 422 |
| PUT | `/user/me/password` | Bearer | Đổi mật khẩu | 400/401, 422 |
| GET | `/profile/mine` | Bearer | CV của tôi | 401 |
| GET | `/profile/available` | Bearer | CV khả dụng (ứng viên: của mình; ADMIN: tất cả) | 401 |
| POST | `/profile/upload` | Bearer | Tải CV `pdf/docx/txt` (multipart `file`), 201 | 400 sai định dạng, 401, 422 |
| PATCH | `/profile/{profile_id}` | Bearer, chủ CV | Cập nhật `title`, `skills` | 401, 404, 422 |
| GET | `/jd/available` | Bearer | Danh sách JD | 401 |
| GET | `/graph/` | Không | Health check Skill Matching | - |
| GET | `/graph/match-similarity?profile_id&jd_id` | Không | Đánh giá CV với JD (embedding + KG) | 400, 404, 422 (`profile_id`/`jd_id` >= 1) |
| GET | `/graph/stats` | ADMIN | Thống kê PostgreSQL | 401, 403 |
| POST | `/graph/schema/init` | ADMIN | Khởi tạo schema Neo4j | 401, 403 |
| POST | `/graph/sync/all` | ADMIN | Đồng bộ toàn bộ sang Neo4j | 401, 403 |
| POST | `/graph/sync/cv/{cv_id}` | CV access | Đồng bộ một CV | 401, 403, 404 |
| POST | `/graph/sync/job/{job_id}` | ADMIN | Đồng bộ một JD | 401, 403 |
| GET | `/graph/cvs/{cv_id}/skills` | CV access | Kỹ năng CV từ Neo4j | 401, 403, 404 |
| GET | `/graph/cvs/{cv_id}/education` | CV access | Học vấn CV | 401, 403, 404 |
| GET | `/graph/cvs/{cv_id}/experience` | CV access | Kinh nghiệm CV | 401, 403, 404 |
| GET | `/graph/jobs/{job_id}/skills` | Không | Kỹ năng JD từ Neo4j | - |
| GET | `/graph/jobs/{job_id}/education` | Không | Yêu cầu học vấn JD | - |
| GET | `/graph/jobs/{job_id}/candidates` | ADMIN | Tìm ứng viên (vector + graph) | 401, 403 |
| POST | `/graph/match/{cv_id}/{jd_id}` | CV access | So khớp CV-JD, lưu `MATCHES_JD` | 401, 403, 404 |
| GET | `/graph/skill-gap/{cv_id}/{job_id}` | CV access | Skill gap từ graph | 500 (xem Hạn chế) |
| GET | `/graph/matrix/domain-gap/{cv_id}` | CV access | Ma trận domain gap | 500 (xem Hạn chế) |
| POST | `/semantic-search/skills` | Không | Tìm kỹ năng gần nghĩa (`query`, `top_k`, `min_similarity`, `source`) | 422 |
| POST | `/semantic-search/job-requirements` | Không | Tìm JD theo yêu cầu (`query`, `top_k` 1-50, `min_similarity`) | 422 |
| GET | `/skill-gap/health` | Không | Health check | - |
| POST | `/skill-gap/analyze` | Không | Phân tích skill gap (ids hoặc danh sách kỹ năng) | 400, 404, 422 |
| GET | `/skill-gap/profile/{profile_id}/jd/{jd_id}` | Không | Skill gap nhanh theo ids | 404, 422 |

Lỗi xác thực dữ liệu trả 422 với body mặc định của FastAPI (`{"detail": [...]}`), vì `app/core/exceptions.py`
chưa được đăng ký trong `app/main.py`. Lỗi nghiệp vụ trả `{"detail": "..."}`.

## Ví dụ curl

```bash
BASE=http://localhost:8080/api/v1

# Đăng ký
curl -X POST $BASE/auth/register -H "Content-Type: application/json" \
  -d '{"email":"a@example.com","full_name":"Nguyen Van A","password":"Passw0rd!","confirm_password":"Passw0rd!"}'

# Đăng nhập (form)
curl -X POST $BASE/auth/login -d "username=a@example.com&password=Passw0rd!"

# Gọi endpoint có bảo vệ
curl $BASE/user/me -H "Authorization: Bearer $ACCESS_TOKEN"

# Tải CV
curl -X POST $BASE/profile/upload -H "Authorization: Bearer $ACCESS_TOKEN" -F "file=@cv.pdf"

# Tìm kỹ năng gần nghĩa
curl -X POST $BASE/semantic-search/skills -H "Content-Type: application/json" \
  -d '{"query":"python web framework","top_k":5}'

# Skill gap theo danh sách kỹ năng
curl -X POST $BASE/skill-gap/analyze -H "Content-Type: application/json" \
  -d '{"candidate_skills":["Python","FastAPI"],"required_skills":["Python","Docker"]}'

# Đánh giá CV với JD
curl "$BASE/graph/match-similarity?profile_id=1&jd_id=1"
```

Tên trường chính xác của từng request/response nằm trong `docs/openapi.json` (mục `components.schemas`).

## Hạn chế đã biết (được test ghi nhận)

- `GET /graph/skill-gap/...` và `GET /graph/matrix/domain-gap/...` trả 500 vì `graph_service` thiếu hàm
  `get_skill_gap_analysis_service` và `calculate_domain_skill_gap_matrix_service` (test xfail).
- `/semantic-search/*`, `/skill-gap/*`, `/graph/match-similarity`, `/graph/jobs/{id}/skills|education` không yêu cầu đăng nhập.
- Sau `register`, `IsVerified` là `False` nên `/auth/refresh` trả 401.
