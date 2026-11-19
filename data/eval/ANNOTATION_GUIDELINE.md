# Hướng dẫn gán nhãn – tập đánh giá CV–JD (v1)

## 1. Mục đích và phạm vi

Tập nhãn nhỏ này dùng để đo Precision/Recall/F1 (và P@k, MRR, nDCG) cho ba tác vụ của hệ thống: trích xuất kỹ năng, xếp hạng/đối sánh CV–JD, và phân tích khoảng cách kỹ năng (skill gap). Dữ liệu lấy từ `app/dataset` (300 CV, 69 JD, tiếng Anh và tiếng Việt lẫn lộn).

| File | Nội dung |
|---|---|
| `pairs.csv` | 40 cặp CV–JD = 8 JD × 5 CV. Cột `relevance` ∈ {0,1,2}. |
| `skills_gold.jsonl` | Danh sách kỹ năng chuẩn cho 34 CV (mọi CV trong các cặp) và 15 JD (8 JD trong cặp + 7 JD khác). |
| `gap_gold.jsonl` | Với mỗi cặp: kỹ năng JD được chia thành `matched` / `partial` / `missing`. |

## 2. Ai gán nhãn (đọc kỹ)

- **Toàn bộ nhãn do một AI coding agent gán** sau khi đọc toàn văn từng CV/JD. Mỗi dòng nhãn có `annotator = ai-agent` và `human_verified = false`.
- **Không có nhãn nào được con người xác minh độc lập.** Đây không phải là "nhãn do chuyên gia gán"; khi trích dẫn trong báo cáo phải ghi rõ "nhãn do AI gán, chưa kiểm chứng bởi con người, một người gán duy nhất".
- Không có chỉ số đồng thuận giữa các người gán (inter-annotator agreement) vì chỉ có một người gán.
- Nhãn được gán **chỉ từ văn bản gốc**, không nhìn vào đầu ra của bất kỳ phương pháp nào (keyword, vector, graph, dịch vụ matching). Việc chọn cặp cũng dựa vào tiêu đề/từ khóa vai trò và ngôn ngữ, không dựa vào điểm tương đồng.
- Ngoại lệ đã khai báo: trường `JobSkills` của JD là dữ liệu có sẵn (tag từ trang tuyển dụng), không phải nhãn. Kỹ năng chuẩn của JD được viết từ phần `requirements`/`responsibilities`.

Khi người kiểm tra sửa nhãn, hãy đổi `human_verified` thành `true` **chỉ cho dòng đã được người đó xem lại**, và ghi tên người sửa vào cột/trường `annotator` (ví dụ `ai-agent+reviewer:<tên>`). Lưu ý `scripts/eval/validate_labels.py` hiện yêu cầu `annotator = ai-agent`; khi có người duyệt, cần cập nhật validator và guideline này cho khớp.

## 3. Quy trình chọn cặp

1. In chỉ mục (id, tiêu đề, ngôn ngữ, độ dài) của 300 CV và 69 JD.
2. Chọn 8 JD thuộc các nhóm vai trò khác nhau, 4 tiếng Anh và 4 tiếng Việt: Frontend (`jd-18`), Fullstack Java/Vue (`jd-15`), Data Engineer (`jd-09`), DevOps (`jd-14`), Tester (`jd-06`), AI Engineer (`jd-41`), Kinh doanh giải pháp CNTT (`jd-26`), IT Business Analyst (`jd-63`).
3. Với mỗi JD chọn 5 CV khác nhau theo tiêu đề/từ khóa vai trò: ít nhất một CV có khả năng phù hợp và một CV rõ ràng không phù hợp (khác lĩnh vực).
4. Tập là **mẫu chọn thủ công, không phải mẫu ngẫu nhiên**, nên không đại diện cho toàn bộ 300 CV. CV `1814dc83…` bị trùng `file_url` trong corpus nên không được chọn.
5. `jd_id = jd-NN` với NN là chỉ số dòng (bắt đầu từ 0) trong `app/dataset/JDs/ready/processed-20261104-151737.txt`. `cv_id` là tên file (không đuôi) của `file_url`. `text_sha1` là SHA-1 của `rawtext` (CV) hoặc `RawText` (JD) để phát hiện corpus thay đổi.

## 4. Thang `relevance` (mức phù hợp CV–JD)

| Mức | Ý nghĩa | Ví dụ trong tập |
|---|---|---|
| 2 | Cùng nhóm vai trò và có phần lớn kỹ năng cốt lõi JD yêu cầu. | `jd-15` + CV Java/Spring Boot/PostgreSQL/REST (p06) |
| 1 | Cùng lĩnh vực rộng hoặc có kỹ năng chuyển đổi được, còn thiếu rõ rệt. | `jd-15` + CV fullstack PHP/React (p08) |
| 0 | Khác lĩnh vực hoặc gần như không có kỹ năng JD yêu cầu. | `jd-15` + CV Marketing Manager (p10) |

Nhị phân: dương tính khi `relevance ≥ 1` (có báo cáo thêm `≥ 2`). Mỗi JD có ít nhất một CV mức ≥ 1 và một CV mức 0 (validator kiểm tra). Một số cặp biên giữa mức 1 và 2 được ghi chú trong cột `notes`; các ranh giới này mang tính chủ quan.

## 5. Quy tắc kỹ năng chuẩn (`skills_gold.jsonl`)

- Kỹ năng = công nghệ, công cụ, ngôn ngữ lập trình, phương pháp, chứng chỉ hoặc năng lực nghề nghiệp cụ thể được nêu **tường minh** trong văn bản (ví dụ `python`, `docker`, `software testing`, `negotiation`).
- Không tính: kỹ năng mềm chung chung (giao tiếp, làm việc nhóm, chủ động), ngoại ngữ, bằng cấp/số năm kinh nghiệm, tên công ty/dự án.
- Với JD, ghi cả kỹ năng "bắt buộc" lẫn "ưu tiên/nice to have" nếu được nêu tên; không phân biệt mức bắt buộc.
- Chuẩn hóa về một dạng: chữ thường, không dấu câu ở hai đầu. Dùng tên tiếng Anh nếu có thuật ngữ chuẩn (vd. `kiểm thử phần mềm` → `software testing`); giữ tiếng Việt chỉ khi không có thuật ngữ chuẩn.
- Bí danh gộp về một dạng: `k8s` → `kubernetes`, `reactjs`/`react.js` → `react`, `vuejs` → `vue`, `nodejs`, `mssql` → `sql server`, `apache2` → `apache http server`, `iac` → `infrastructure as code`.
- Không suy diễn kỹ năng không được nêu (ví dụ CV viết "GitHub" thì ghi `github`, không tự thêm `git`).
- Văn bản CV là kết quả trích từ PDF nên có nhiễu (mất dấu, chữ bị tách, ký tự `C/C++` bị mất `+`); khi nghi ngờ, người gán chọn cách đọc hợp lý nhất và ghi chú.

## 6. Quy tắc `matched` / `partial` / `missing` (`gap_gold.jsonl`)

Xét từng kỹ năng trong danh sách kỹ năng chuẩn của JD:

- `matched`: CV có đúng kỹ năng đó hoặc một bí danh hiển nhiên.
- `partial`: CV có kỹ năng liên quan rõ ràng/chuyển đổi được (ví dụ MySQL cho PostgreSQL, Angular cho Vue, `github` cho `git`, `azure devops` cho `github actions`, thấy bằng chứng gián tiếp trong mô tả công việc).
- `missing`: CV không có gì liên quan.

Ba tập rời nhau và hợp của chúng bằng đúng tập kỹ năng chuẩn của JD. Người gán chỉ liệt kê `matched` và `partial`; `missing` được tính bù. Kỹ năng thừa của CV (extra) có thể suy ra từ `skills_gold.jsonl`, không lưu riêng.

## 7. Hạn chế đã biết

- Chỉ 40 cặp, 8 JD, 34 CV khác nhau: khoảng tin cậy rất rộng; không đủ để kết luận thống kê mạnh.
- Một người gán duy nhất (AI), không có đồng thuận giữa người gán, không kiểm chứng bởi con người.
- Mẫu chọn thủ công, thiên về CV ngành CNTT; không đại diện cho toàn bộ dữ liệu.
- Ranh giới giữa mức 1 và 2, và giữa `partial` và `missing`, mang tính chủ quan.
- `lang` được phát hiện tự động bằng biểu thức chính quy ký tự có dấu tiếng Việt (≥ 5 ký tự có dấu → `vi`), nên CV song ngữ có thể bị gán nhãn ngôn ngữ chưa chính xác.
- 7 JD ngoài các cặp chỉ dùng cho đánh giá trích xuất kỹ năng.

## 8. Cách người kiểm tra sửa nhãn và chạy lại

1. Sửa trực tiếp `pairs.csv`, `skills_gold.jsonl`, `gap_gold.jsonl` (giữ `missing` = kỹ năng JD trừ `matched` và `partial`).
2. Kiểm tra: `venv\Scripts\python.exe -m scripts.eval.validate_labels` (in lỗi và bảng độ phủ theo cặp).
3. Chạy đánh giá: `venv\Scripts\python.exe -m scripts.eval.evaluate --out data/eval/results`.
4. Chạy test: `venv\Scripts\python.exe -m pytest tests/test_eval_labels.py tests/test_eval_metrics.py -q`.
