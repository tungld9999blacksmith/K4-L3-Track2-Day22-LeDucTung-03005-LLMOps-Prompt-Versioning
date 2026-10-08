# Phân tích kết quả RAGAS — Prompt V1 vs V2

## 1. Thiết lập thí nghiệm

| Thành phần | Cấu hình |
|---|---|
| Bộ đánh giá | 50 cặp QA (`src/qa_pairs.py`), chạy qua **cả 2** prompt |
| Retriever | FAISS, `chunk_size=500`, `chunk_overlap=50`, `k=3` — **dùng chung** cho V1 và V2 |
| LLM sinh câu trả lời + LLM judge của RAGAS | `qwen-plus-character` (Alibaba Cloud Model Studio) |
| Embedding | `qwen3.7-text-embedding` |
| Metric | `faithfulness`, `answer_relevancy`, `context_recall`, `context_precision` |
| Lỗi khi đánh giá | 0 job lỗi / timeout (không có giá trị NaN) |

**Lưu ý về provider:** Bước 1–2 chạy bằng Gemini (`gemini-3.5-flash-lite` + `gemini-embedding-001`). Bước 3 chuyển sang Qwen vì quota miễn phí theo ngày của Gemini đã hết (500 request LLM/ngày, 1000 request embedding/ngày) khi chạy RAGAS. Cả V1 và V2 ở Bước 3 đều được chạy và chấm với **cùng một cấu hình** nên vẫn so sánh được với nhau.

**Hai prompt:**

| | V1 — ngắn gọn | V2 — chuyên gia, có cấu trúc |
|---|---|---|
| Vai trò | Trợ lý thân thiện, đi thẳng vào trọng tâm | Chuyên gia phân tích tài liệu AI/ML |
| Hướng dẫn | Quy tắc: chỉ dùng context, trả lời 2–4 câu | Quy trình 3 bước: xác định facts → trả lời trực tiếp rồi giải thích/nêu ví dụ (3–5 câu) → giữ nguyên thuật ngữ, số liệu |
| Ranh giới chống bịa | Không dùng kiến thức ngoài; thiếu thông tin thì trả lời câu cố định "Tôi không tìm thấy thông tin này trong tài liệu." | Không suy đoán/bổ sung ngoài context; thiếu thông tin thì nói rõ phần nào còn thiếu |

## 2. Kết quả

| Metric | V1 | V2 | Chênh lệch (V1 − V2) |
|---|---|---|---|
| faithfulness | **0.9741** | 0.9708 | +0.0033 |
| answer_relevancy | **0.9542** | 0.9539 | +0.0003 |
| context_recall | 1.0000 | 1.0000 | 0 |
| context_precision | 0.9150 | 0.9150 | 0 |

- Faithfulness ≥ 0.9 ở **cả 2** phiên bản (mục tiêu ≥ 0.8 đạt).
- Cột "Winner" trong `03_ragas_scores.png` ghi `← V2` ở `context_recall` chỉ do code so sánh `s1 > s2` (hai giá trị bằng nhau thì in V2) — **không phải V2 thắng**.

## 3. Phân tích

### 3.1 Hai metric retrieval giống hệt nhau giữa V1 và V2 — đúng như kỳ vọng
`context_recall` và `context_precision` đo chất lượng **retriever** (lấy đủ thông tin chưa, chunk liên quan có được xếp đầu không). V1 và V2 dùng chung FAISS index, chung `k=3` và chung bộ câu hỏi nên nhận về **đúng cùng các chunk** → hai metric này trùng nhau đến 4 chữ số thập phân. Điều này xác nhận prompt **chỉ ảnh hưởng** đến 2 metric phía generator: `faithfulness` và `answer_relevancy`.

- `context_recall = 1.0`: với mọi câu hỏi, 3 chunk lấy về đã chứa đủ thông tin của đáp án chuẩn.
- `context_precision = 0.915` (< 1.0): trong 3 chunk thường có chunk **không cần thiết**. Quan sát trên trace khớp với điều này: với câu hỏi *"What is LangChain?"*, retriever lấy đúng các chunk về LangChain, nhưng chunk thứ 3 nói về **LangSmith** — có liên quan về chủ đề nhưng không giúp trả lời câu hỏi, nên bị trừ điểm precision.

### 3.2 V1 nhỉnh hơn V2, nhưng chênh lệch không đáng kể
Mức chênh 0.0033 (faithfulness) và 0.0003 (answer_relevancy) là rất nhỏ. Với 50 mẫu và LLM judge không hoàn toàn tất định (chạy lại có thể cho điểm khác một chút), mức chênh này **nằm trong sai số**; chưa đủ để khẳng định V1 tốt hơn V2.

Nhận định cá nhân: hai prompt có ý nghĩa tương đương nhau. Cả hai đều yêu cầu trả lời trung thực, chỉ dựa trên tài liệu và có hướng xử lý khi thiếu thông tin — V1 bằng quy tắc và ranh giới, V2 bằng vai trò, quy trình thực hiện và ranh giới. Vì cùng hướng mô hình bám context, cả hai đều tránh được hallucination và trả lời đúng trọng tâm, dẫn tới điểm generator gần như nhau.

Giả thuyết cho việc faithfulness của V2 thấp hơn một chút: V2 yêu cầu câu trả lời **dài hơn** (3–5 câu) và "giải thích chi tiết hoặc nêu ví dụ", còn V1 chỉ 2–4 câu. Câu trả lời dài hơn chứa nhiều claim hơn, nên xác suất có một claim không được context hỗ trợ trực tiếp cao hơn — faithfulness tính bằng *số claim được hỗ trợ / tổng số claim* nên dễ bị kéo xuống hơn.

### 3.3 Quan sát qua tracing (LangSmith)
- **Bám sát câu hỏi và tài liệu:** đánh giá sơ bộ qua trace (không thông qua RAGAS) cho thấy câu trả lời bám vào câu hỏi và nội dung chunk; tuy nhiên một số chunk được lấy về không chứa nội dung cần cho câu trả lời (khớp với `context_precision = 0.915`).
- **Ngôn ngữ trả lời:** một số câu trả lời là **tiếng Việt** dù câu hỏi và tài liệu là tiếng Anh. Nguyên nhân: system prompt viết bằng tiếng Việt, mô hình ưu tiên ngôn ngữ của system prompt thay vì làm theo yêu cầu "trả lời bằng ngôn ngữ của câu hỏi". Hiện tượng này làm giảm `answer_relevancy` (RAGAS sinh ngược câu hỏi từ câu trả lời rồi so với câu hỏi gốc tiếng Anh — lần chạy thử với Gemini trên 2 câu chỉ đạt ~0.73).
- **Độ trễ trung bình** (trên trace): LLM ~1.26 s / lần gọi, embedding ~0.2 s / lần gọi → bước sinh câu trả lời là nút thắt chính về latency.

## 4. Hạn chế
1. **Cùng một model vừa sinh câu trả lời vừa làm judge** (`qwen-plus-character`). LLM judge có xu hướng chấm dễ cho văn bản do chính nó tạo ra (self-preference bias) → điểm faithfulness ~0.97 có thể **cao hơn thực tế**. Nên dùng judge là một model khác, mạnh hơn.
2. `qwen-plus-character` là model tối ưu cho hội thoại/nhập vai, không phải model đa dụng; được chọn vì có quota miễn phí.
3. Bước 1–2 (Gemini) và Bước 3 (Qwen) dùng provider khác nhau → kết quả RAGAS không phản ánh trực tiếp chất lượng câu trả lời trong trace của Bước 1–2.
4. Bộ 50 câu hỏi khá dễ: các câu đều trả lời được trực tiếp từ một đoạn tài liệu (`context_recall = 1.0` ở mọi câu) → chưa phân biệt được hai prompt.
5. Mỗi phiên bản chỉ chạy 1 lần; chưa đo độ dao động của điểm giữa các lần chạy.

## 5. Kết luận và hướng tiếp theo
**Kết luận:** hai prompt cho chất lượng tương đương; V1 nhỉnh hơn rất ít ở faithfulness và answer_relevancy nhưng chênh lệch nằm trong sai số. Xét về cấu trúc và quy tắc, V2 đầy đủ và rõ ràng hơn (có quy trình suy luận, giữ nguyên thuật ngữ, chỉ rõ phần thông tin còn thiếu), nhưng ưu điểm đó **chưa thể hiện được** trên bộ test hiện tại. Nếu phải chọn ngay, V1 hợp lý hơn vì ngắn, rẻ token hơn và faithfulness không thấp hơn.

**Cần thêm bộ test khó hơn** để phân biệt chất lượng hai prompt:
- Câu hỏi **ngoài phạm vi tài liệu** → kiểm tra V1 có trả lời câu cố định "không tìm thấy" và V2 có chỉ rõ phần còn thiếu thay vì bịa.
- Câu hỏi **cần ghép thông tin từ nhiều chunk** (multi-hop).
- Câu hỏi **mơ hồ** hoặc có **tiền đề sai**.
- Bổ sung metric so với đáp án chuẩn (`FactualCorrectness`, `AnswerCorrectness`) và chấm tay một số mẫu.

**Cải tiến khác:**
- Thêm ràng buộc ngôn ngữ rõ ràng (hoặc viết system prompt bằng tiếng Anh, cùng ngôn ngữ với dữ liệu) để tránh trả lời tiếng Việt.
- Giảm chunk không liên quan để tăng `context_precision`: thử MMR, ngưỡng điểm tương đồng, re-ranking, hoặc giảm `k`.
- Dùng judge khác model generator và chạy lặp nhiều lần để có khoảng tin cậy cho điểm.
