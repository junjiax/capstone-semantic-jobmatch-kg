# Tóm tắt kết quả đánh giá (tiếng Việt)

Mọi con số bên dưới được sao chép từ các file kết quả đã lưu trong thư mục này: `eval_summary.md`, `eval_metrics.csv`, `latency_summary.md`. Chạy ngày 2026-11-19 (UTC), model `sentence-transformers/all-MiniLM-L6-v2`, CPU Intel i5-11300H, 15.8 GB RAM, Python 3.11.8, torch 2.10.0+cpu.

## Cảnh báo về nguồn gốc nhãn (bắt buộc đọc trước khi trích dẫn)

- Toàn bộ nhãn (độ phù hợp 0/1/2 của 40 cặp CV–JD, danh sách kỹ năng chuẩn, nhãn matched/partial/missing) do **AI coding agent** gán bằng cách đọc văn bản CV/JD theo `data/eval/ANNOTATION_GUIDELINE.md`. Mỗi dòng nhãn ghi `annotator=ai-agent`, `human_verified=false`.
- **Đây không phải nhãn do con người gán.** Chỉ có một "người" gán nhãn, không có độ đồng thuận giữa nhiều người gán (inter-annotator agreement). Bạn cần tự rà soát và sửa nhãn trước khi viết "tập nhãn do con người gán" trong báo cáo. Có thể ghi là "tập nhãn tham chiếu do AI gán, đã/chưa được người kiểm tra" tùy thực tế.
- Quy mô nhỏ: 40 cặp, 8 JD (mỗi JD 5 CV), 34 CV và 15 JD có nhãn kỹ năng. Các cặp được chọn thủ công (chủ yếu vị trí IT), không phải mẫu ngẫu nhiên. Khoảng tin cậy 95% (bootstrap) rất rộng.

## Phương pháp đã chạy và không chạy

Đã chạy: `cv_rules` (trích xuất kỹ năng CV của dự án), `dictionary` (từ điển), `jd_tags` (trường `JobSkills`, chỉ là thẻ có sẵn, không phải bộ trích xuất), `keyword`, `vector_only`, `project_match` (`calculate_cv_jd_matching`, dùng DB giả và bỏ qua ghi đồ thị), `project_gap`, `project_smart`.

Không chạy (`not_run`):
- `matching/graph_hybrid` và `gap/graph_neo4j`: Neo4j/Postgres không kết nối được trên localhost (kiểm tra TCP).
- Truy vấn pgvector `ORDER BY cosine_distance` và truy vấn đồ thị Neo4j trong benchmark độ trễ: cùng lý do. Phần "vector_search" bên dưới là numpy trong bộ nhớ, **không phải** đo pgvector.
- Gemini không dùng.

## Xếp hạng CV theo từng JD (trung bình 8 JD, 5 CV/JD)

| phương pháp | P@1 | P@3 | MRR | nDCG@5 |
|---|---|---|---|---|
| keyword | 0.750 | 0.708 | 0.854 | 0.828 |
| vector_only | 0.875 | 0.750 | 0.938 | 0.859 |
| project_match | 0.875 | 0.750 | 0.938 | 0.858 |
| random_order (kỳ vọng) | 0.725 | 0.725 | 0.856 | 0.817 |

Nhận xét trung thực: khoảng tin cậy chồng lấn mạnh (ví dụ P@1 của vector_only 0.875, CI [0.62, 1.00]; random_order 0.725, CI [0.65, 0.80]), nên với 8 JD không thể khẳng định phương pháp nào vượt trội so với thứ tự ngẫu nhiên. Theo ngôn ngữ JD (n=4 mỗi nhóm), nDCG@5 của keyword là 0.9251 (en) và 0.7305 (vi); của vector_only là 0.9251 (en) và 0.7938 (vi).

## Phân loại phù hợp / không phù hợp (nhãn rel>=1 là dương tính)

| phương pháp | ROC AUC [CI] | ngưỡng mặc định của dự án P / R / F1 |
|---|---|---|
| keyword | 0.724 [0.63, 0.82] | không có |
| vector_only | 0.511 [0.27, 0.72] | không có |
| project_match | 0.614 [0.43, 0.78] | 1.000 / 0.138 / 0.242 (ngưỡng match_score >= 0.40) |

- Với rel>=2, project_match tại ngưỡng 0.70 cho P/R/F1 = 0.500 / 0.077 / 0.133.
- Mốc tham chiếu "luôn dự đoán dương tính" (rel>=1) đạt P 0.725, R 1.000, F1 0.841, cao hơn mọi phương pháp ở ngưỡng mặc định. F1 tốt nhất khi dò ngưỡng cũng là 0.841 (tối ưu trên chính 40 cặp nên lạc quan, không dùng làm kết quả chính).
- Kết luận: ngưỡng 0.70/0.40 của dự án chưa được hiệu chỉnh cho model MiniLM trên dữ liệu này (recall chỉ 0.138 ở ngưỡng 0.40).

## Trích xuất kỹ năng (micro, so với nhãn kỹ năng chuẩn)

CV (34 tài liệu):

| phương pháp | khớp | P | R | F1 [CI] |
|---|---|---|---|---|
| cv_rules | exact | 0.228 | 0.085 | 0.124 [0.06, 0.20] |
| cv_rules | soft | 0.429 | 0.181 | 0.255 [0.17, 0.34] |
| dictionary | exact | 0.585 | 0.194 | 0.291 [0.24, 0.34] |
| dictionary | soft | 0.676 | 0.261 | 0.377 [0.31, 0.43] |

JD (15 tài liệu):

| phương pháp | khớp | P | R | F1 [CI] |
|---|---|---|---|---|
| jd_tags | exact | 0.241 | 0.078 | 0.118 [0.05, 0.20] |
| jd_tags | soft | 0.349 | 0.133 | 0.193 [0.13, 0.27] |
| dictionary | exact | 0.577 | 0.192 | 0.288 [0.18, 0.38] |
| dictionary | soft | 0.612 | 0.220 | 0.323 [0.23, 0.42] |

Đầu ra `cv_rules` trùng với `skilltitle` đã lưu ở 34/34 CV (xác nhận đã gọi đúng đường mã). Recall thấp ở mọi phương pháp: dữ liệu CV là văn bản trích từ PDF, nhiễu, trộn Việt–Anh.

## Phân tích khoảng trống kỹ năng (skill gap), micro, 40 cặp

Cỡ lớp nhãn chuẩn: matched 114, partial 57, missing 534.

Đầu vào là kỹ năng chuẩn (`gold_inputs`):

| phương pháp | lớp | P | R | F1 |
|---|---|---|---|---|
| keyword | matched | 1.000 | 0.965 | 0.982 |
| project_gap | matched | 0.991 | 0.974 | 0.982 |
| project_gap | partial | 0.308 | 0.210 | 0.250 |
| project_gap | missing | 0.917 | 0.951 | 0.934 |
| project_smart | partial | 0.545 | 0.105 | 0.176 |

Đầu vào là kỹ năng CV do hệ thống trích xuất (`pipeline_cv_skills`):

| phương pháp | lớp | P | R | F1 |
|---|---|---|---|---|
| project_gap | matched | 1.000 | 0.149 | 0.260 |
| project_gap | partial | 0.091 | 0.018 | 0.029 |
| project_gap | missing | 0.786 | 0.996 | 0.879 |

Điểm yếu: kết quả `gold_inputs` lạc quan vì cùng một người gán viết cả hai danh sách theo cùng cách đặt tên nên khớp tên chính xác dễ. Lớp `partial` (thông tin nhất) chỉ đạt F1 0.250 với project_gap. Ngưỡng 0.82/0.60 chưa hiệu chỉnh cho MiniLM (ví dụ MySQL so với PostgreSQL có cosine 0.547, thấp hơn ngưỡng 0.60 nên không được tính partial). Khi dùng kỹ năng CV tự trích xuất, recall lớp matched chỉ 0.149 do lỗi trích xuất lan sang.

## Độ trễ (ms, 30 lần đo sau 5 lần khởi động; `latency_summary.md`)

Tải model lần đầu: 400.1 ms (một lần đo).

| giai đoạn | trường hợp | p50 | p95 | mean |
|---|---|---|---|---|
| embedding | 1 kỹ năng | 8.561 | 9.981 | 8.709 |
| embedding | 1 văn bản CV | 47.567 | 55.076 | 47.911 |
| embedding | 1 văn bản JD | 44.157 | 56.608 | 43.281 |
| embedding | lô 32 kỹ năng | 42.653 | 46.265 | 42.43 |
| vector_search (numpy, không phải pgvector) | N=69 JD thật | 0.014 | 0.014 | 0.014 |
| vector_search (numpy) | N=300 CV thật | 0.021 | 0.023 | 0.022 |
| vector_search (numpy, vector ngẫu nhiên) | N=20000 | 0.997 | 2.31 | 1.202 |
| matching | `calculate_cv_jd_matching` (10 cặp) | 86.546 | 104.097 | 88.133 |
| skill_gap | 5 ứng viên x 5 yêu cầu | 94.809 | 114.872 | 98.556 |
| skill_gap | 20 x 20 | 401.673 | 425.352 | 402.148 |
| skill_gap | 50 x 20 | 721.877 | 769.177 | 731.264 |
| end-to-end | CV -> encode -> top-10 trong 69 JD -> match top 3 -> gap top 1 | 523.357 | 913.378 | 584.579 |

Giới hạn: đo trên một máy CPU, không gồm Postgres/pgvector, Neo4j, mạng hay HTTP; `matching` dùng DB giả. Cần ghi rõ trong báo cáo đây là độ trễ thành phần tính toán, không phải độ trễ API production.

## Các điểm yếu cần nêu trong báo cáo

1. Quy mô nhỏ (40 cặp, 8 JD), khoảng tin cậy rộng; chưa đủ để kết luận về ưu thế của phương pháp nào trong xếp hạng.
2. Nhãn do AI gán, chưa có người kiểm tra, một người gán duy nhất.
3. Ngưỡng của dự án (match 0.70/0.40, gap 0.82/0.60) chưa hiệu chỉnh cho `all-MiniLM-L6-v2`; mốc "luôn dương tính" đạt F1 0.841.
4. Dữ liệu trộn tiếng Việt và tiếng Anh trong khi model thiên về tiếng Anh; nhóm JD tiếng Việt có nDCG@5 thấp hơn ở keyword (0.7305 so với 0.9251).
5. `jd_tags` chỉ là thẻ crawler, không phải trích xuất; nhiều JD có thẻ rỗng hoặc không liên quan.
6. Model cắt đầu vào ở 256 word piece, CV dài chỉ được mã hóa phần đầu.
7. Graph/hybrid (Neo4j) và pgvector chưa được đo trong lần chạy này.

## Lệnh tái lập (từ thư mục gốc repo, PowerShell)

```powershell
venv\Scripts\python.exe -m scripts.eval.evaluate --out data/eval/results
venv\Scripts\python.exe -m scripts.eval.latency
venv\Scripts\python.exe -m pytest -q
```

Sau khi sửa nhãn trong `data/eval/*.csv|jsonl`, chạy lại lệnh đầu để tính lại điểm. Kết quả pytest ở lần chạy này: 308 passed, 31 skipped, 10 deselected, 3 xfailed (không có DB).
