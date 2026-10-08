# Checkpoints — Day 22: LangSmith + Prompt Versioning

Lab gồm 1 checkpoint chuẩn bị + 4 checkpoint ứng với 4 nhiệm vụ. Làm xong checkpoint trước rồi mới sang checkpoint sau. Mỗi checkpoint có 4 phần: **Cần làm** (từng bước, kèm code gợi ý), **Sản phẩm**, **Cần hiểu**, **Tự kiểm tra**.

Tiêu chí chấm ở [RUBRIC.md](RUBRIC.md), cách nộp ở [SUBMISSION.md](SUBMISSION.md).

---

## Checkpoint 0 — Chuẩn bị môi trường (~30 phút)

### Cần làm

**1. Tạo virtual environment và cài thư viện**

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux / Git Bash
# venv\Scripts\activate         # Windows cmd / PowerShell
pip install -r requirements.txt
pip install "langchain-community<0.4"   # bắt buộc: bản 0.4 làm import ragas lỗi
```

> Lần đầu cài mất 5–10 phút. Trong lúc chờ, làm bước 2.

**2. Tạo tài khoản LangSmith và lấy API key**

1. Mở [smith.langchain.com](https://smith.langchain.com) → **Sign up** (đăng nhập bằng Google/GitHub hoặc email). Gói **Developer** miễn phí là đủ cho lab. Xác nhận email nếu được yêu cầu, rồi tạo/chấp nhận workspace mặc định.
2. Ở thanh bên trái, bấm biểu tượng bánh răng **Settings** (góc dưới bên trái) → chọn tab **API Keys**.
3. Bấm **Create API Key** và điền:
   - **Description**: tên tùy ý, ví dụ `day22-lab`.
   - **Key Type**: chọn **Personal Access Token** (khóa dạng `lsv2_pt_...`). Không cần Service Key (`lsv2_sk_...`).
   - **Expiration**: để `Never` hoặc chọn thời hạn dài hơn thời gian làm lab.
4. Bấm **Create**, rồi **sao chép key ngay** — key chỉ hiện **một lần**, đóng hộp thoại là không xem lại được (mất thì phải tạo key mới).
5. Dán key vào dòng `LANGCHAIN_API_KEY=` trong `.env` ở bước 3 bên dưới. Không dán key vào code, chat, log hay ảnh chụp màn hình (xem [RULES.md](RULES.md)).

> Không cần tạo project thủ công: LangSmith tự tạo project tên `day22-lab` (giá trị `LANGCHAIN_PROJECT`) ở lần chạy đầu tiên có trace.
>
> **Chọn đúng `LANGCHAIN_ENDPOINT` theo khu vực tài khoản.** Tài khoản chỉ tồn tại ở khu vực bạn đăng ký, và key chỉ dùng được với API của khu vực đó. Đặt sai endpoint sẽ báo lỗi 401/403 và không có trace nào xuất hiện. Xem địa chỉ trên thanh trình duyệt khi đang đăng nhập LangSmith:
>
> | Địa chỉ web đăng nhập | `LANGCHAIN_ENDPOINT` |
> |---|---|
> | `smith.langchain.com` (US, mặc định) | `https://api.smith.langchain.com` |
> | `eu.smith.langchain.com` (EU) | `https://eu.api.smith.langchain.com` |
> | `apac.smith.langchain.com` (APAC) | `https://apac.api.smith.langchain.com` |
>
> Ví dụ với tài khoản APAC, trong `.env`:
> ```env
> LANGCHAIN_ENDPOINT=https://apac.api.smith.langchain.com
> ```
> `.env.example` mặc định là US; `src/config.py` đọc biến này từ `.env` nên chỉ cần sửa ở `.env`.

**3. Cấu hình `.env`**

```bash
cp .env.example .env
```

Mở `.env` và điền tối thiểu các biến sau (tên biến phải **đúng như `.env.example`**):

```env
LANGCHAIN_TRACING_V2=true            # Bật tracing — đặt sai sẽ mất toàn bộ traces
LANGCHAIN_API_KEY=lsv2_pt_...        # API key LangSmith vừa lấy
LANGCHAIN_PROJECT=day22-lab          # Tên project để nhóm traces trên dashboard
PROVIDER=openai                      # openai | gemini | anthropic | ollama | openrouter
OPENAI_API_KEY=sk-...                # key của provider bạn chọn
```

Chỉ cần điền key cho provider đã chọn:

| `PROVIDER` | Ghi chú |
|---|---|
| `openai` | Ổn định nhất, khuyến nghị. Dùng `gpt-4o-mini` để tiết kiệm chi phí |
| `gemini` | Miễn phí, quota 15 request/phút → Checkpoint 3 sẽ chậm hơn |
| `anthropic` | Không có Embeddings API → **vẫn cần `OPENAI_API_KEY`** cho embeddings |
| `ollama` | Chạy offline, cần cài [ollama.ai](https://ollama.ai) và `ollama pull llama3.1 && ollama pull nomic-embed-text` |
| `openrouter` | Nhiều model qua 1 key; embeddings vẫn dùng `OPENAI_API_KEY` |

**4. Windows: bật UTF-8 cho Python**

Log của lab có emoji. Trên Windows, khi lưu log ra file bằng `tee` sẽ lỗi `UnicodeEncodeError` nếu chưa bật UTF-8. Dùng **Git Bash** và chạy một lần mỗi phiên terminal:

```bash
export PYTHONUTF8=1              # Git Bash
# $env:PYTHONUTF8=1              # PowerShell
```

### Sản phẩm
File `.env` ở máy local (**không commit**).

### Cần hiểu
- Vì sao `LANGCHAIN_TRACING_V2` / `LANGCHAIN_API_KEY` phải có trong môi trường **trước** khi import LangChain. `src/config.py` làm việc này, nên mọi file bước đều `import config` trước tiên.
- `PROVIDER` quyết định LLM và embedding model dùng trong toàn bộ lab (xem `src/utils/llm_factory.py`).

### Tự kiểm tra
```bash
cd src && python config.py      # phải in: ✅ Config OK | Provider: ... | Project: ...
git status                      # KHÔNG thấy .env
```

---

## Checkpoint 1 — RAG Pipeline + LangSmith tracing (25đ, 25–45 phút)

**Mục tiêu:** load dữ liệu → chunk → embed → index FAISS → chain hỏi đáp → gắn `@traceable` để mỗi câu hỏi thành 1 trace trên LangSmith.

### Cần làm
Mở `src/01_langsmith_rag_pipeline.py`, đọc hết file rồi điền các TODO.

**1. `setup_vectorstore()`** — các hàm trong `utils/` đã viết sẵn, chỉ cần gọi đúng thứ tự:

```python
embeddings  = get_embeddings()
text        = load_knowledge_base()
chunks      = split_text(text, chunk_size=500, chunk_overlap=50)
vectorstore = build_vectorstore(chunks, embeddings)
```

**2. `RAG_PROMPT`**

```python
RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Bạn là trợ lý AI hữu ích. Chỉ dùng context sau để trả lời.\n\nContext:\n{context}"),
    ("human", "{question}"),
])
```

**3. `build_rag_chain()`** — nối retriever → prompt → LLM → parser, trả về **cả** `(chain, retriever)`:

```python
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | RAG_PROMPT | llm | StrOutputParser()
)
return chain, retriever
```

**4. `ask()` có `@traceable`** — decorator phải nằm **ngay trên** `def`:

```python
@traceable(name="rag-query", tags=["rag", "step1"])
def ask(chain, question: str) -> str:
    return chain.invoke(question)
```

**5. `main()`** — `SAMPLE_QUESTIONS` là `list[str]`:

```python
vectorstore      = setup_vectorstore()
chain, retriever = build_rag_chain(vectorstore)
# trong vòng lặp:
answer = ask(chain, question)
```

**6. Chạy:** `python 01_langsmith_rag_pipeline.py` (~2 phút với OpenAI).

### Sản phẩm
`evidence/01_langsmith_traces.png` — ảnh chụp danh sách traces trên LangSmith.

### Cần hiểu
- Luồng chunk → embed → FAISS → retrieve → generate.
- `@traceable` tạo trace thế nào; một trace gồm những run con nào (retriever, prompt, LLM, parser).

### Tự kiểm tra
- Script in đủ 50 cặp Q/A, không lỗi.
- Mở [smith.langchain.com](https://smith.langchain.com) → project của bạn: thấy **≥ 50 traces** `rag-query`. Mở 1 trace: thấy câu hỏi, 3 đoạn context được truy xuất và câu trả lời.
- Script luôn in thông báo hoàn thành kể cả khi key sai → **chỉ dashboard mới là bằng chứng**.

---

## Checkpoint 2 — Prompt Hub & A/B Routing (25đ, 20–30 phút)

**Mục tiêu:** viết 2 system prompt khác nhau, push lên Prompt Hub, pull về khi chạy, và định tuyến câu hỏi tất định (cùng `request_id` → luôn cùng prompt).

### Cần làm
Mở `src/02_prompt_hub_ab_routing.py`.

**1. Đổi tên prompt thành tên riêng của bạn**

```python
PROMPT_V1_NAME = "nguyen-van-a-rag-prompt-v1"
PROMPT_V2_NAME = "nguyen-van-a-rag-prompt-v2"
```

**2. Viết 2 system prompt khác nhau rõ rệt.** **Bắt buộc giữ `{context}`** — thiếu nó thì LLM không nhận được tài liệu mà chương trình vẫn chạy bình thường, faithfulness ở Checkpoint 3 sẽ tụt mạnh.

```python
SYSTEM_V1 = (
    "Bạn là trợ lý AI thân thiện. Trả lời ngắn gọn (2-4 câu), chỉ dựa trên context. "
    "Nếu không có thông tin, hãy nói thẳng là không biết.\n\n"
    "Context:\n{context}"
)
SYSTEM_V2 = (
    "Bạn là chuyên gia phân tích thông tin. Đọc kỹ context, xác định các facts liên quan, "
    "rồi viết câu trả lời rõ ràng, có tổ chức (3-5 câu). Không suy đoán ngoài context.\n\n"
    "Context:\n{context}"
)
```

`PROMPT_V1` / `PROMPT_V2` đã được tạo sẵn từ 2 biến này.

**3. Push và pull**

```python
# push_prompts_to_hub(client)
url = client.push_prompt(PROMPT_V1_NAME, object=PROMPT_V1, description="V1 – ngắn gọn")
url = client.push_prompt(PROMPT_V2_NAME, object=PROMPT_V2, description="V2 – có cấu trúc")

# pull_prompts_from_hub(client)
prompts[PROMPT_V1_NAME] = client.pull_prompt(PROMPT_V1_NAME)
prompts[PROMPT_V2_NAME] = client.pull_prompt(PROMPT_V2_NAME)
```

**4. Routing tất định bằng MD5** — trả về **tên prompt** để tra trong dict `prompts`:

```python
hash_int = int(hashlib.md5(request_id.encode()).hexdigest(), 16)
return PROMPT_V1_NAME if hash_int % 2 == 0 else PROMPT_V2_NAME
```

**5. `ask_ab()`**

```python
@traceable(name="ab-rag-query", tags=["ab-test", "step2"])
def ask_ab(retriever, llm, prompt, question: str, version: str) -> dict:
    docs    = retriever.invoke(question)
    context = "\n\n".join(d.page_content for d in docs)
    answer  = (prompt | llm | StrOutputParser()).invoke({"context": context, "question": question})
    return {"question": question, "answer": answer, "version": version}
```

**6. `main()`**

```python
client      = Client(api_key=config.LANGSMITH_API_KEY)
prompts     = pull_prompts_from_hub(client)
retriever   = vectorstore.as_retriever(search_kwargs={"k": 3})
# trong vòng lặp:
version_key = get_prompt_version(request_id)
result      = ask_ab(retriever, llm, prompt, question, version_tag)
```

**7. Chạy và lưu log**

```bash
python 02_prompt_hub_ab_routing.py | tee ../evidence/02_ab_routing_log.txt
```

### Sản phẩm
`evidence/02_ab_routing_log.txt`, `evidence/02_prompt_hub.png` (LangSmith → **Prompt Hub** → chụp 2 prompt vừa push).

### Cần hiểu
- Vì sao cần versioning prompt và tách prompt khỏi code.
- Vì sao routing bằng hash là tất định còn `random` thì không.

### Tự kiểm tra
- Log in `↓ Đã pull ... từ Hub` cho **cả 2** prompt. Nếu thấy dòng báo dùng prompt local (fallback) nghĩa là pull **thất bại** (thường do sai API key) → mất điểm tiêu chí 2.2/2.3.
- Log có cả nhãn `[prompt-v1]` và `[prompt-v2]`.
- Chạy lại lần 2: cùng `request_id` → cùng phiên bản. Lần chạy lại có thể báo `409 ... Nothing to commit` khi push — **không phải lỗi**, chỉ là prompt chưa đổi nên Hub không tạo phiên bản mới.
- Prompt Hub hiển thị cả 2 prompt.

---

## Checkpoint 3 — RAGAS Evaluation (25đ, 45–75 phút — bắt đầu sớm)

**Mục tiêu:** chạy 50 cặp QA qua cả V1 và V2, chấm bằng 4 chỉ số RAGAS, lưu báo cáo JSON.

> Phần chạy mất **15–30 phút** (chạy thử với `gpt-4o-mini`: ~21 phút). Bắt đầu ngay khi xong Checkpoint 2, không đóng terminal.

### Cần làm
Mở `src/03_ragas_evaluation.py`.

**1. Copy `SYSTEM_V1` / `SYSTEM_V2` giống hệt Checkpoint 2** (kể cả `{context}`) để kết quả so sánh được.

**2. `run_rag()`** — `contexts` phải là `list[str]`, **không** ghép thành 1 chuỗi (RAGAS cần từng đoạn riêng để tính context_recall/precision):

```python
docs     = retriever.invoke(question)
contexts = [doc.page_content for doc in docs]
ctx_str  = "\n\n".join(contexts)          # chỉ dùng để truyền vào prompt
answer   = (prompt | llm | StrOutputParser()).invoke({"context": ctx_str, "question": question})
return {"answer": answer, "contexts": contexts}
```

**3. `collect_rag_outputs()`** — `QA_PAIRS` là list các dict có khóa `question` và `reference`:

```python
out = run_rag(retriever, llm, prompt, qa["question"])
# "answer": out["answer"], "contexts": out["contexts"]
```

**4. `build_ragas_dataset()`** — `SingleTurnSample` cần đúng 4 trường:

```python
SingleTurnSample(
    user_input=r["question"],
    response=r["answer"],
    retrieved_contexts=r["contexts"],   # list[str]
    reference=r["reference"],
)
```

**5. `run_ragas_eval()` và `main()`**

```python
dataset = build_ragas_dataset(rag_results)
result  = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
    llm=llm_eval,
    embeddings=emb_eval,
)
# main():
vectorstore = setup_vectorstore()
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
```

**6. Chạy và lưu evidence**

```bash
python 03_ragas_evaluation.py
cp ../data/ragas_report.json ../evidence/03_ragas_report.json
```

Khi bảng so sánh V1 vs V2 hiện ra → chụp màn hình terminal.

### Sản phẩm
`data/ragas_report.json`, `evidence/03_ragas_report.json`, `evidence/03_ragas_scores.png`.

### Cần hiểu
- Ý nghĩa của `faithfulness`, `answer_relevancy`, `context_recall`, `context_precision`.
- Vì sao 2 prompt khác nhau cho ra điểm khác nhau (phân tích này được điểm thưởng).

### Tự kiểm tra
```bash
python -m json.tool ../evidence/03_ragas_report.json
```
- Report có điểm của **cả V1 và V2**, đủ 4 chỉ số.
- Faithfulness ≥ 0.8 ở ít nhất 1 phiên bản. Chưa đạt → kiểm tra `{context}` trong prompt, thử giảm `chunk_size` hoặc tăng `k`.
- Log có nhiều dòng `LLM returned 1 generations instead of requested 3` → bình thường, bỏ qua.

---

## Checkpoint 4 — Guardrails AI Validators (25đ, 20–30 phút)

**Mục tiêu:** tự viết 2 validator: `PIIDetector` (che thông tin cá nhân) và `JSONFormatter` (sửa JSON lỗi từ đầu ra LLM).

### Cần làm
Mở `src/04_guardrails_validator.py`.

> **Quan trọng nhất:** với `on_fail=OnFailAction.FIX`, Guardrails chỉ thay output bằng `fix_value` của **`FailResult`**. Trả về `PassResult(...)` thì output giữ nguyên input — PII **không** bị che dù log vẫn in "Đã redact". Docstring và comment TODO trong file đang gợi ý `PassResult(value_override=...)` — **hãy dùng `FailResult(fix_value=...)` như bên dưới**.

**1. `PIIDetector.validate()`** — duyệt `self.PII_PATTERNS` (đã cho sẵn):

```python
for pii_type, pattern in self.PII_PATTERNS.items():
    for match in re.findall(pattern, value):
        redacted_text = redacted_text.replace(match, f"[{pii_type}_REDACTED]")
        found_pii.append((pii_type, match))

if found_pii:
    return FailResult(error_message="Phát hiện PII", fix_value=redacted_text)
return PassResult()
```

**2. `JSONFormatter._repair()`** — phần gỡ markdown fences đã có sẵn:

```python
text = text.replace("'", '"')                     # nháy đơn → nháy đôi
text = re.sub(r',\s*([}\]])', r'\1', text)        # xóa dấu phẩy thừa trước } hoặc ]
```

**3. `JSONFormatter.validate()`**

```python
try:                                   # 1) hợp lệ sẵn
    json.loads(value)
    return PassResult()
except json.JSONDecodeError:
    pass
try:                                   # 2) sửa được → JSON đã chuẩn hóa
    parsed = json.loads(self._repair(value))
    return FailResult(error_message="JSON lỗi, đã tự sửa", fix_value=json.dumps(parsed, indent=2))
except json.JSONDecodeError:           # 3) không sửa được → JSON dự phòng (tiêu chí 4.7)
    fallback = json.dumps({"error": "Không thể phân tích JSON", "raw": value[:200]}, ensure_ascii=False)
    return FailResult(error_message="Không thể sửa JSON", fix_value=fallback)
```

**4. Tạo Guard** — `on_fail` truyền vào **constructor của validator**, không phải `Guard.use()`:

```python
guard  = Guard().use(PIIDetector(on_fail=OnFailAction.FIX))      # ĐÚNG
# Guard().use(PIIDetector(), on_fail=OnFailAction.FIX)           # SAI
result = guard.validate(text)
```

**5. Chạy và lưu log** — script in cả 2 demo, nên ghi ra **cả 2 file evidence** trong 1 lần chạy:

```bash
python 04_guardrails_validator.py | tee ../evidence/04_pii_demo_log.txt ../evidence/04_json_demo_log.txt
```

### Sản phẩm
`evidence/04_pii_demo_log.txt`, `evidence/04_json_demo_log.txt`.

### Cần hiểu
- Vòng đời validate → fail → fix trong Guardrails, và vì sao `FailResult(fix_value=...)` mới thay được output.
- Khác biệt giữa truyền `on_fail` vào constructor và vào `Guard.use()`.

### Tự kiểm tra
- PII: dòng `Output:` chứa `[EMAIL_REDACTED]`, `[PHONE_REDACTED]`, `[SSN_REDACTED]`, `[CREDIT_CARD_REDACTED]`; case sạch giữ nguyên. **Output giống hệt Input** → bạn đang trả về `PassResult` thay vì `FailResult`.
- JSON: case sửa được in ra JSON đã format lại; case không sửa được in ra `{"error": ...}`.
- Cảnh báo `opentelemetry ... Failed to export spans` (telemetry của Guardrails) → bỏ qua được.

---

## Checkpoint cuối — Nộp bài

Chạy lại toàn bộ để chắc chắn mọi bước không lỗi:

```bash
cd src && python run_all.py            # hoặc: python run_all.py --step 3
```

Rồi làm theo [SUBMISSION.md](SUBMISSION.md): đặt tên repo đúng quy ước, chạy phần "Kiểm tra trước khi nộp", push và nộp link trước deadline.
