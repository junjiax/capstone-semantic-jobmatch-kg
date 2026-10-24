# CV Evaluation API

Backend API dùng FastAPI để quản lý hồ sơ ứng viên/CV, tin tuyển dụng, kỹ năng, embedding và kết quả matching. PostgreSQL (image có pgvector) là database chính; Docker Compose có thêm pgAdmin để quản trị database.

## Thành phần chính

- `app/api/v1/routers/`: các API router, được gắn dưới prefix `/api/v1`.
- `app/models/`, `app/crud/`, `app/services/`: model database, thao tác dữ liệu và nghiệp vụ.
- `app/core/config.py`: đọc cấu hình bằng Pydantic Settings và tạo database URL.
- `alembic/`, `alembic.ini`: migration database.
- `scripts/`: các script seed dữ liệu.
- `tests/`: test hiện có.
- `uploads/`: dữ liệu upload; Docker Compose mount thư mục này vào container.
- `DockerFile`, `docker-compose.yml`: build và chạy API cùng PostgreSQL/pgAdmin.

Project dùng Python 3.13 trong Docker image và các dependency được khai báo trong `requirements.txt`.

## Yêu cầu

### Chạy local

- Python 3.13
- PostgreSQL tương thích với pgvector, đang chạy trên máy local hoặc một host có thể truy cập

### Chạy bằng Docker

- Docker Desktop (Windows/macOS) hoặc Docker Engine
- Docker Compose v2 (`docker compose`)

## Cấu hình môi trường

Tạo file `.env` tại thư mục gốc project, cùng cấp với `docker-compose.yml`. File `.env` đang bị loại khỏi Git và Docker build context; không commit file này hoặc ghi secret thật vào README.

Ví dụ cấu hình phát triển:

```dotenv
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change-this-password
POSTGRES_SERVER_DOCKER=postgres
POSTGRES_PORT=5432
POSTGRES_DB=cv_evaluator_db

GEMINI_API_KEY=
PGADMIN_DEFAULT_EMAIL=admin@local.com
PGADMIN_PASSWORD=change-this-password
```

Thay giá trị mẫu bằng giá trị phù hợp với môi trường của bạn.

| Biến | Bắt buộc | Ý nghĩa |
|---|---:|---|
| `POSTGRES_USER` | Có | User PostgreSQL; đồng thời được dùng để khởi tạo container database |
| `POSTGRES_PASSWORD` | Có | Password PostgreSQL |
| `POSTGRES_SERVER_DOCKER` | Có | Host PostgreSQL. Dùng `postgres` khi app chạy trong Compose; dùng `localhost` khi chạy app trực tiếp trên máy |
| `POSTGRES_PORT` | Có | Cổng PostgreSQL, thông thường là `5432` |
| `POSTGRES_DB` | Có | Tên database |
| `GEMINI_API_KEY` | Không | API key cho chức năng tích hợp Gemini nếu sử dụng |
| `PGADMIN_DEFAULT_EMAIL` | Có với service pgAdmin | Email đăng nhập pgAdmin |
| `PGADMIN_PASSWORD` | Có với service pgAdmin | Password đăng nhập pgAdmin |

`app/core/config.py` yêu cầu chính xác tên `POSTGRES_SERVER_DOCKER` (phân biệt chữ hoa/thường). `DATABASE_URL_DOCKER` và `DATABASE_URL_LOCAL` có thể được khai báo trong `.env` để tiện dùng ở nơi khác, nhưng `Settings` hiện tự tạo URL từ các biến PostgreSQL riêng lẻ.

### Phân biệt `.env` của Docker Compose và biến môi trường bên trong container

Compose đọc `.env` ở máy host để thay thế các biểu thức `${TEN_BIEN}` trong `docker-compose.yml`. Việc đó **không tự động nạp toàn bộ `.env` vào container**. Service `web` phải truyền các biến cần thiết trong phần `environment`; file `.env` không được copy vào image do `.dockerignore`.

Tên biến ở hai phía phải khớp. Với cấu hình hiện tại, cần giữ mapping:

```yaml
environment:
  POSTGRES_SERVER_DOCKER: ${POSTGRES_SERVER_DOCKER}
```

Không đổi tên thành `POSTGRES_SERVER`: Pydantic không xem hai tên này là tương đương. Nếu dùng một file Compose khác hoặc đổi tên biến trong `config.py`, hãy cập nhật đồng thời cả `.env` và `environment` trong Compose.

## Chạy bằng Docker Compose

Chạy các lệnh từ thư mục gốc project, nơi có `.env` và `docker-compose.yml`.

```cmd
docker compose config
docker compose up --build -d
docker compose ps
```

`docker compose config` giúp phát hiện biến Compose chưa được khai báo hoặc lỗi cú pháp. Kết quả đã nội suy có thể chứa password; không đăng công khai output này.

Lần đầu chạy, Compose sẽ build image từ `DockerFile`, khởi động PostgreSQL, chờ health check của database rồi chạy API và pgAdmin. Truy cập:

- API: <http://localhost:8080>
- Swagger UI: <http://localhost:8080/docs>
- pgAdmin: <http://localhost:5050>

Các lệnh hữu ích:

```cmd
docker compose logs -f web
docker compose logs -f postgres
docker compose exec web alembic current
docker compose exec web alembic upgrade head
docker compose down
```

Để dùng file Compose có tên khác:

```cmd
docker compose --env-file .env -f file-name.yml up --build -d
```

Lệnh `docker compose down` giữ lại named volumes, bao gồm dữ liệu PostgreSQL. `docker compose down -v` sẽ xóa các volumes và dữ liệu trong đó; chỉ dùng khi chủ động muốn xóa database local.

## Chạy trực tiếp trên máy (Windows)

Mở CMD hoặc PowerShell tại thư mục gốc project.

### Tạo virtual environment và cài dependency

Trong CMD:

```cmd
py -3.13 -m venv venv
venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Trong PowerShell, thay lệnh kích hoạt bằng:

```powershell
.\venv\Scripts\Activate.ps1
```

Nếu PowerShell chặn script activation, có thể dùng CMD hoặc cấu hình execution policy phù hợp với máy của bạn.

### Cấu hình và khởi động

Trong `.env`, đặt `POSTGRES_SERVER_DOCKER=localhost` cho app chạy trực tiếp trên máy. Đảm bảo PostgreSQL đã chạy, database trong `POSTGRES_DB` đã được tạo và các giá trị user/password/port khớp với PostgreSQL.

Từ thư mục gốc project, chạy migration rồi khởi động API:

```cmd
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

Mở <http://localhost:8080/docs> để xem API.

Nếu PostgreSQL cũng chạy trong Compose, khởi động database trước bằng `docker compose up -d postgres`; khi app chạy trên máy host, vẫn dùng `POSTGRES_SERVER_DOCKER=localhost` vì cổng database được publish trên host.

## Migration với Alembic

Các lệnh Alembic phải được chạy từ thư mục gốc để tìm thấy `alembic.ini`, package `app` và `.env`.

```cmd
alembic current
alembic history
alembic upgrade head
```

Khi thay đổi model:

1. Xác nhận mọi model được import trước khi Alembic đọc metadata.
2. Tạo migration:

   ```cmd
   alembic revision --autogenerate -m "describe schema change"
   ```

3. Đọc và kiểm tra file mới trong `alembic/versions/`; autogenerate không thay thế việc review migration.
4. Áp dụng migration:

   ```cmd
   alembic upgrade head
   ```

### Lỗi Alembic thường gặp trong project này

- **Autogenerate tạo migration rỗng hoặc không phát hiện bảng:** `alembic/env.py` hiện đặt `target_metadata = None`. Autogenerate cần metadata thật. Hãy import `Base` từ `app.core.database`, import tất cả module model để các bảng được đăng ký vào metadata, rồi đặt `target_metadata = Base.metadata`. Chỉ import `app.models` là chưa đủ nếu `app/models/__init__.py` chưa import tất cả model.

  Mẫu cấu hình cần có trong `alembic/env.py`:

  ```python
  from app.core.database import Base

  # Import tất cả module model trước khi lấy metadata.
  import app.models.User
  import app.models.application
  import app.models.cv
  import app.models.cv_embedding
  import app.models.cv_skill
  import app.models.education
  import app.models.enum
  import app.models.experience
  import app.models.jd
  import app.models.jd_skill
  import app.models.job
  import app.models.job_embedding
  import app.models.job_skill
  import app.models.match_result
  import app.models.profile
  import app.models.profile_edu
  import app.models.profile_skill
  import app.models.profile_work_exp
  import app.models.result
  import app.models.screen_batch
  import app.models.skill

  target_metadata = Base.metadata
  ```

  Kiểm tra tất cả model dùng cùng `Base` từ `app.core.database`. Nếu sau này thêm model, import module mới tại đây trước khi tạo migration.

- **`alembic upgrade head` không kết nối được database:** kiểm tra PostgreSQL đang chạy, host/port/user/password/database trong `.env`, và chạy lệnh từ thư mục gốc. Host `postgres` chỉ phân giải bên trong Docker network; khi chạy Alembic trên máy host, dùng `localhost`.

- **`Target database is not up to date`:** chạy `alembic upgrade head` trước khi tạo migration mới.

- **Báo `already exists` khi áp dụng migration đầu tiên:** database có thể đã có schema nhưng chưa được Alembic quản lý. Không xóa database hoặc chạy `stamp head` mù quáng. So sánh schema thực tế với toàn bộ migration trước; chỉ dùng `alembic stamp head` khi đã xác minh schema khớp chính xác với migration hiện tại.

Repo hiện có migration `d9de3805454c_create_account_table.py`, tạo bảng `account`. Kiểm tra nội dung migration và schema mong muốn của ứng dụng trước khi áp dụng lên database có dữ liệu quan trọng.

## Sửa lỗi Pydantic Settings

Lỗi dạng:

```text
ValidationError: 1 validation error for Settings
POSTGRES_SERVER_DOCKER
  Field required [type=missing, ...]
```

nghĩa là Pydantic không nhận được biến bắt buộc `POSTGRES_SERVER_DOCKER`. Kiểm tra lần lượt:

1. `.env` nằm ở thư mục làm việc hiện tại khi khởi chạy, và có dòng `POSTGRES_SERVER_DOCKER=...`.
2. Tên biến viết đúng chữ hoa/thường; cấu hình hiện tại bật `case_sensitive=True`.
3. Nếu chạy bằng Docker Compose, service `web` phải truyền `POSTGRES_SERVER_DOCKER: ${POSTGRES_SERVER_DOCKER}`. Compose đọc `.env` để nội suy nhưng `.env` không tự xuất hiện trong container.
4. Chọn đúng host: `postgres` trong container Compose, `localhost` khi chạy ứng dụng trên máy host.
5. Sau khi sửa biến môi trường Compose, tạo lại container:

   ```cmd
   docker compose up --build -d
   ```

Nếu thiếu biến khác, Pydantic sẽ báo tên trường bắt buộc tương ứng; đảm bảo đủ `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_SERVER_DOCKER`, `POSTGRES_PORT` và `POSTGRES_DB`.

## Một số lỗi Docker Compose khác

- **`required variable ... is missing` hoặc giá trị nội suy rỗng:** xác nhận biến có trong `.env` ở thư mục gốc và đúng tên với `${...}` trong Compose. `.env` cần theo cú pháp `TEN_BIEN=gia_tri`.
- **API báo không kết nối được tới database:** khi app ở container, host phải là tên service `postgres`, không phải `localhost`; đợi service PostgreSQL healthy rồi xem `docker compose logs postgres web`.
- **Đổi cấu hình nhưng container vẫn dùng giá trị cũ:** chạy `docker compose up --build -d` để build lại và tạo lại container.
- **Port đã được sử dụng:** giải phóng port `8080`, `5432` hoặc `5050`, hoặc chỉnh port publish bên trái dấu `:` trong Compose.
- **Không thấy thay đổi của schema:** cập nhật model cần migration Alembic; build lại image không tự cập nhật database schema.

## Kiểm tra

Chạy test từ thư mục gốc, với virtual environment đã kích hoạt và database đã cấu hình nếu test cần kết nối:

```cmd
python -m pytest
```

`tests/test_db.py` kiểm tra kết nối database; test này cần database khả dụng và `.env` hợp lệ.


## Schema hiện tại và Neo4j

Source hiện sử dụng các bảng `USER`, `PROFILE`, `JD`, `PROFILE_SKILL`,
`PROFILE_EDU`, `PROFILE_WORK_EXP`, `JD_SKILL` và `RESULT`.
Nếu database còn các bảng cũ `users`, `CVs`, `Jobs`, chạy một lần:

```powershell
.\venv\Scripts\python.exe -m scripts.upgrade_current_schema
.\venv\Scripts\python.exe -m scripts.migrate_pg_to_neo4j
```

Script tạo các bảng mới và sao chép tài khoản, CV, JD và tên kỹ năng; giữ nguyên
các bảng cũ. Lịch sử kết quả, kinh nghiệm, học vấn và embedding cũ vẫn nằm trong
các bảng cũ, chưa được chuyển bởi script này.

Bật Docker Desktop trước khi chạy `docker compose up -d --build`.
Khi chạy Python trực tiếp trên Windows, dùng `NEO4J_URI=bolt://localhost:7687`.
Backend trong Compose dùng `bolt://neo4j:7687` qua mạng container.
Neo4j Browser: <http://localhost:7474>.

Image Docker mặc định cài PyTorch CPU để tránh tải bộ CUDA. Compose gắn `./app` vào `/app/app` ở chế độ chỉ đọc; sau khi sửa source, chạy `docker compose restart web`.

### Đồng bộ và kiểm tra graph

API graph theo CV yêu cầu đăng nhập bằng tài khoản đang hoạt động. Ứng viên chỉ
được truy cập CV của mình; Admin được truy cập mọi CV. Các API quản trị graph
yêu cầu quyền Admin/HR theo enum hiện tại.

Sau khi xóa dữ liệu trong PostgreSQL, chạy `POST /api/v1/graph/sync/all` hoặc
`python -m scripts.migrate_pg_to_neo4j` để dọn CV, JD, JobPosition, User,
MatchResult và SkillRequirement không còn tương ứng trong graph. Đây là đồng bộ
theo yêu cầu, chưa có hàng đợi tự động đồng bộ khi dữ liệu thay đổi.

Điểm kinh nghiệm dùng ngày bắt đầu/kết thúc công việc, gộp các khoảng thời gian
chồng nhau. Điểm học vấn dùng vector học vấn và yêu cầu JD; thiếu vector sẽ trả
0 thay vì gán điểm mặc định. Cần tạo embedding từ dữ liệu hiện tại để có điểm
ngữ nghĩa đầy đủ.

Kiểm thử riêng phần graph:

```powershell
.\venv\Scripts\python.exe -m pytest tests/test_graph_regressions.py -q
# Thêm kiểm thử trên Neo4j local (tạo và dọn dữ liệu test riêng):
$env:RUN_NEO4J_REGRESSIONS='1'
.\venv\Scripts\python.exe -m pytest tests/test_graph_regressions.py -q
```
