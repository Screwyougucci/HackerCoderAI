from functools import lru_cache
from .config import settings

@lru_cache(maxsize=1)
def load_model():
    path = settings.model_file
    if path is None:
        return None
    try:
        from llama_cpp import Llama
    except ImportError as exc:
        raise RuntimeError("Install llama-cpp-python to enable local inference.") from exc
    return Llama(model_path=str(path), n_ctx=settings.n_ctx,
                 n_threads=settings.n_threads, n_gpu_layers=0, verbose=False)

def generate(messages: list[dict]) -> str:
    model = load_model()
    if model is None:
        raise RuntimeError("No model configured. Set MODEL_PATH in .env.")
    result = model.create_chat_completion(
        messages=messages, max_tokens=settings.max_tokens, temperature=0.2
    )
    return result["choices"][0]["message"]["content"].strip()
