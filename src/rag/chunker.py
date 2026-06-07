def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    """Split text into simple overlapping chunks for future RAG indexing."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be greater than or equal to 0 and smaller than chunk_size")

    chunks: list[str] = []
    start = 0
    clean_text = text.strip()
    while start < len(clean_text):
        end = start + chunk_size
        chunks.append(clean_text[start:end])
        start = end - overlap
    return chunks
