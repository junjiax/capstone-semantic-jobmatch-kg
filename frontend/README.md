# Semantic JobMatch KG - Frontend UI

Giao diện người dùng cho đề tài tốt nghiệp: **"Ứng dụng kết hợp Đồ thị tri thức (Neo4j) và Vector Embedding (pgvector) trong so khớp kỹ năng và hỗ trợ phát triển kỹ năng nghề nghiệp trên ngữ liệu tiếng Việt"**.

---

## 1. CÔNG NGHỆ SỬ DỤNG
* **Framework:** Next.js 16 (App Router) + React 19 + TypeScript.
* **Styling:** Tailwind CSS v4 + Lucide Icons.
* **Biểu đồ & Trực quan hóa dữ liệu:**
  - `Recharts`: Biểu đồ ngũ giác Radar Chart 5 khía cạnh so khớp (`RadarChart5Aspects`).
  - `Cytoscape.js`: Trực quan hóa mạng lưới đồ thị tri thức tương tác (`GraphCanvas`).
  - Ma trận nhiệt Heatmap phân tích khoảng cách kỹ năng (`DomainMatrixHeatmap`).
* **Kết nối Backend:** Axios (với Bearer Token Interceptor) kết nối tới FastAPI (`http://localhost:8080/api/v1`).

---

## 2. CÁC MÀN HÌNH CHÍNH
1. **Trang chủ (`/`):** Giới thiệu đề tài, kiến trúc lưu trữ đa mô hình (Polyglot Persistence), tóm tắt 3 bài toán khoa học.
2. **So khớp 1 CV vs 1 JD - Bài toán 1 (`/candidate/match`):**
   - Điểm đối sánh tổng hợp $TotalResult \in [0, 1]$ (ngưỡng phù hợp $\ge 65\%$).
   - Biểu đồ Radar 5 tiêu chí: Kỹ năng (40%), Lĩnh vực (20%), Chuyên môn (20%), Kinh nghiệm (10%), Học vấn (10%).
   - Bảng phân rã 4 nhóm kỹ năng: Đạt (Xanh), Một phần (Vàng), Còn thiếu (Đỏ), Bổ trợ (Tím).
   - Lộ trình đào tạo gợi ý bù đắp khoảng cách kỹ năng (Actionable Learning Roadmap).
3. **Ma trận Định hướng 8 Domains IT - Bài toán 2 (`/candidate/career-matrix`):**
   - Bảng ma trận nhiệt (Heatmap Matrix) giữa 4 thuộc tính CV và 8 Domains / Expertises.
   - Bảng xếp hạng lĩnh vực tiềm năng nhất kèm lời khuyên phát triển nghề nghiệp.
4. **Tuyển dụng Lai - Bài toán 3 (`/recruiter/hybrid-search`):**
   - Dành cho HR: Xếp hạng Top-K ứng viên phù hợp với vị trí tuyển dụng qua kết hợp Vector ANN + Graph Skill Coverage.
5. **Knowledge Graph Explorer (`/admin/graph-explorer`):**
   - Trực quan hóa tương tác các nút Domain, Expertise, Skill, Job, Candidate trên Canvas đồ thị và bảng Node Inspector.
6. **Đồng bộ Dữ liệu ETL (`/admin/system-sync`):**
   - Bảng điều khiển khởi tạo Schema Neo4j và chạy ETL Sync toàn bộ dữ liệu PostgreSQL sang Neo4j.

---

## 3. CÁCH CHẠY LOCAL

### Bước 1: Di chuyển vào thư mục frontend
```bash
cd frontend
```

### Bước 2: Khởi động Development Server
```bash
npm run dev
```

Mở trình duyệt tại: **`http://localhost:3000`**

### Bước 3: Build Production & Kiểm thử
```bash
npm run build
npm run start
```
