# Hướng dẫn kiểm thử

Chạy từ thư mục gốc repo, dùng Python của venv (3.11).

```powershell
venv\Scripts\python.exe -m pytest -q
```

Lần chạy mặc định là hermetic: không tải model sentence-transformer thật, không gọi Gemini, không cần Neo4j.
`tests/conftest.py` thay embedding bằng `FakeEmbedder` (384 chiều, xác định) và chặn việc tải model thật.
Test tích hợp Postgres tự bỏ qua (skip) khi không kết nối được DB test.

## Marker (`pytest.ini`)

| Marker | Ý nghĩa | Chạy mặc định |
|---|---|---|
| `unit` | Hàm thuần và service với DB mock | Có |
| `api` | Endpoint qua `TestClient`, DB mock | Có |
| `integration` | Cần PostgreSQL + pgvector (`TEST_DATABASE_URL`) | Có, skip nếu không có DB |
| `neo4j` | Cần Neo4j thật | Không |
| `external` | Cần Gemini/mạng/model thật | Không |

Mặc định `addopts = -m "not neo4j and not external"`. Ghi đè bằng `-m`.

## Chạy một phần

```powershell
venv\Scripts\python.exe -m pytest tests/unit -q
venv\Scripts\python.exe -m pytest tests/api -q
venv\Scripts\python.exe -m pytest tests/data_pipeline -q
venv\Scripts\python.exe -m pytest -m integration -q      # cần DB test
venv\Scripts\python.exe -m pytest -m neo4j -q            # cần Neo4j (compose profile graph)
venv\Scripts\python.exe -m pytest tests/api/test_openapi.py -q
```

## Vòng đời DB test

`docker-compose.test.yml` (project `jobmatch-test`) tách hoàn toàn khỏi `docker-compose.yml`. Postgres test dùng
cổng 55432, dữ liệu trên tmpfs, tên DB `jobmatch_test`. Fixture từ chối chạy nếu tên DB không kết thúc bằng `_test`,
rồi `CREATE EXTENSION vector`, `drop_all` và `create_all` trước phiên test.

Thủ công:

```powershell
docker compose -f docker-compose.test.yml up -d --wait postgres-test
$env:TEST_DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:55432/jobmatch_test"
venv\Scripts\python.exe -m pytest -m integration -q
docker compose -f docker-compose.test.yml down -v
```

Tự động (khởi động, chạy pytest với tham số truyền vào, dọn dẹp): `.\scripts\run_tests.ps1 -q`.

Neo4j test: `docker compose -f docker-compose.test.yml --profile graph up -d --wait neo4j-test`.
Biến mẫu nằm ở `.env.test.example` (giá trị giả).

## Smoke test dịch vụ api-test

```powershell
docker compose -f docker-compose.test.yml --profile api up -d --build api-test
curl http://localhost:8081/api/v1/skill-gap/health
curl -I http://localhost:8081/docs
docker compose -f docker-compose.test.yml --profile graph --profile api down -v
```

`api-test` chạy `python -m scripts.upgrade_current_schema` rồi uvicorn.

## Lưu ý về migration

Chuỗi Alembic hiện không tạo các bảng hiện tại (`USER`, `PROFILE`, `JD`, ...); nó chỉ tạo bảng `account` cũ và
index HNSW. Schema hiện tại được tạo bằng `scripts/upgrade_current_schema.py` (`CREATE EXTENSION vector` +
`Base.metadata.create_all`), nên test và `api-test` dùng đường này, không dùng `alembic upgrade head`.

## Test được ghi nhận là xfail

Ba test xfail ghi lại lỗi ứng dụng đã biết: thiếu hai hàm `graph_service` (xem `docs/API.md`) và `/auth/refresh`
trả 401 sau khi đăng ký do `IsVerified=False`.
