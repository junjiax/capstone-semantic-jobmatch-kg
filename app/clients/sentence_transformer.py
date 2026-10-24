from sentence_transformers import util, SentenceTransformer
import torch
from typing import List, Optional, Union
import logging
import threading

logger = logging.getLogger(__name__)


class SentenceTransformerClient:
    """
    Lớp quản lý phiên làm việc với mô hình Sentence Transformers theo Singleton pattern.
    Đảm bảo an toàn đa luồng (Thread-safe) và tối ưu hóa tài nguyên phần cứng.
    """
    _instance: Optional["SentenceTransformerClient"] = None
    _lock = threading.Lock()
    _initialized = False
    _model: Optional[SentenceTransformer] = None
    embedding_dimension: int = 384

    def __new__(cls, *args, **kwargs):
        # Kiểm tra nếu đã có instance, nếu chưa thì tạo mới, đảm bảo thread-safe
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        if self._initialized:
            return

        try:
            # Tự động phát hiện phần cứng tăng tốc xử lý
            if torch.cuda.is_available():
                self.device = "cuda"
            elif torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"

            self.model_name = model_name
            logger.info(f"Loading SentenceTransformer model: {model_name}")
            logger.info(f"Using device: {self.device}")

            # Tải mô hình từ cache cục bộ / Hugging Face
            self._model = SentenceTransformer(model_name, device=self.device)
            self.embedding_dimension = self._model.get_sentence_embedding_dimension()
            self._initialized = True

            logger.info(f"Model loaded. Embedding dimension: {self.embedding_dimension}")

        except Exception as e:
            logger.exception("Failed to initialize SentenceTransformerClient")
            raise RuntimeError("SentenceTransformer initialization failed") from e

    @property
    def model(self) -> SentenceTransformer:
        """Truy xuất trực tiếp đến mô hình SentenceTransformer đã được tải."""
        if self._model is None:
            raise RuntimeError("Model is not initialized")
        return self._model

    def encode(
            self,
            text: str,
            *,
            convert_to_tensor: bool = False,
            normalize: bool = True) -> Union[List[float], torch.Tensor]:
        """Chuyển đoạn văn bản thành vector embedding 384
        Tham số:
            text: Chuỗi ký tự cần tạo vector.
            convert_to_tensor: Nếu True trả về torch.Tensor, ngược lại trả về list float.
            normalize: Nếu True, vector được chuẩn hóa L2 norm = 1.0 (phục vụ tính Cosine Similarity).
        """
        if not isinstance(text, str):
            raise TypeError("encode() expects a single string")

        text_cleaned = text.strip() or " "
        
        embedding = self.model.encode(
            text_cleaned,
            convert_to_tensor=convert_to_tensor,
            normalize_embeddings=normalize,
            show_progress_bar=False,
        )
        return embedding if convert_to_tensor else embedding.tolist()

    def encode_batch(
            self,
            texts: List[str],
            *,
            batch_size: int = 32,
            convert_to_tensor: bool = False, 
            normalize: bool = True) -> Union[List[List[float]], torch.Tensor]:
        """
        Xử lý mã hóa hàng loạt nhiều câu văn bản cùng lúc để tối ưu thông lượng (Batch Processing).
        """
        if not texts:
            return [] if not convert_to_tensor else torch.empty(0)
            
        cleaned_texts = [(t.strip() if isinstance(t, str) and t.strip() else " ") for t in texts]
        
        embeddings = self.model.encode(
            cleaned_texts,
            batch_size=batch_size,
            convert_to_tensor=convert_to_tensor,
            normalize_embeddings=normalize,
            show_progress_bar=False,
        )
        return embeddings if convert_to_tensor else embeddings.tolist()

    def get_embedding_dimension(self) -> int:
        return self.embedding_dimension

    @staticmethod
    def cosine_similarity(emb1: Union[List[float], torch.Tensor], emb2: Union[List[float], torch.Tensor]) -> float:
        """
        Tính toán độ tương đồng Cosine giữa hai vector embedding.
        Trả về giá trị số thực từ -1.0 đến 1.0 (càng gần 1.0 càng tương đồng).
        """
        v1 = emb1 if isinstance(emb1, torch.Tensor) else torch.tensor(emb1, dtype=torch.float)
        v2 = emb2 if isinstance(emb2, torch.Tensor) else torch.tensor(emb2, dtype=torch.float)
        if v1.shape != v2.shape:
            raise ValueError(f"Embedding dimensions do not match: {v1.shape} vs {v2.shape}")
        return float(util.cos_sim(v1, v2).item())


# ✅ Lazy singleton — chỉ load khi gọi lần đầu
_client: Optional[SentenceTransformerClient] = None
_client_lock = threading.Lock()

def get_sentence_transformer() -> SentenceTransformerClient:
    """
    Hàm Dependency / Helper lấy thể hiện Singleton của client.
    Chỉ khởi tạo mô hình khi có lời gọi đầu tiên.
    """
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = SentenceTransformerClient()
    return _client