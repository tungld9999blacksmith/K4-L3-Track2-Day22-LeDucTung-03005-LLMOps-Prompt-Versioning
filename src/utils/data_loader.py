"""
Tiện ích để tải và xử lý dữ liệu cho RAG pipeline.

Cách dùng:
    from utils.data_loader import load_knowledge_base, split_text, build_vectorstore

    text        = load_knowledge_base()
    chunks      = split_text(text, chunk_size=500, chunk_overlap=50)
    vectorstore = build_vectorstore(chunks, embeddings)
"""
from pathlib import Path


def load_knowledge_base(path: str = None) -> str:
    """
    Đọc file knowledge base và trả về nội dung dạng chuỗi.

    Args:
        path: đường dẫn tới file text.
              Mặc định: data/knowledge_base.txt (thư mục gốc của project)

    Returns:
        Nội dung file dưới dạng str
    """
    if path is None:
        path = Path(__file__).parent.parent.parent / "data" / "knowledge_base.txt"
    return Path(path).read_text(encoding="utf-8")


def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list:
    """
    Chia văn bản thành các đoạn nhỏ (chunks) để index.

    Dùng RecursiveCharacterTextSplitter — tách ưu tiên theo đoạn văn, câu, rồi ký tự.

    Args:
        text         : văn bản cần chia
        chunk_size   : số ký tự tối đa mỗi chunk (mặc định: 500)
        chunk_overlap: số ký tự chồng lên nhau giữa 2 chunks liên tiếp (mặc định: 50)

    Returns:
        list[str] — danh sách các chuỗi chunk
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.split_text(text)


def _is_rate_limit(error: Exception) -> bool:
    """Nhận diện lỗi vượt quota/rate limit (HTTP 429) của provider embeddings."""
    msg = str(error)
    if "PerDay" in msg:   # hết quota theo ngày → không retry
        return False
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg or "rate limit" in msg.lower()


def build_vectorstore(chunks: list, embeddings, batch_size: int = 50,
                      wait_seconds: int = 60, max_retries: int = 5):
    """
    Tạo FAISS vectorstore từ danh sách chunks và embeddings.

    Embed theo từng lô `batch_size` chunks; nếu provider báo vượt rate limit
    (vd. Gemini free tier: 100 request embed/phút) thì chờ `wait_seconds` rồi thử lại lô đó.

    Args:
        chunks      : list[str] — danh sách text chunks đã chia
        embeddings  : Embeddings instance (từ get_embeddings())
        batch_size  : số chunks embed mỗi lô
        wait_seconds: thời gian chờ khi bị rate limit
        max_retries : số lần thử tối đa cho mỗi lô

    Returns:
        FAISS vectorstore đã được index và sẵn sàng dùng để retrieve
    """
    import time
    from langchain_community.vectorstores import FAISS

    print(f"🔨 Đang tạo FAISS index từ {len(chunks)} chunks ...")
    vectorstore = None
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        for attempt in range(1, max_retries + 1):
            try:
                if vectorstore is None:
                    vectorstore = FAISS.from_texts(batch, embeddings)
                else:
                    vectorstore.add_texts(batch)
                break
            except Exception as e:
                if not _is_rate_limit(e) or attempt == max_retries:
                    raise
                print(f"⏳ Bị rate limit khi embed chunks {start}-{start + len(batch)}, "
                      f"chờ {wait_seconds}s rồi thử lại ({attempt}/{max_retries}) ...")
                time.sleep(wait_seconds)
    print("✅ FAISS vectorstore đã sẵn sàng.")
    return vectorstore
