"""
GPU Acceleration Module for ML Models
Provides utilities for GPU-accelerated inference and training
"""

import torch
import numpy as np
from typing import Optional, List, Dict, Any
import os


class GPUAccelerator:
    """Manages GPU resources for ML model inference"""
    
    def __init__(self):
        self.device = None
        self.available_gpus = 0
        self.current_gpu = 0
        self._initialize_gpu()
    
    def _initialize_gpu(self):
        """Initialize GPU configuration"""
        if torch.cuda.is_available():
            self.device = "cuda"
            self.available_gpus = torch.cuda.device_count()
            print(f"GPU available: {self.available_gpus} device(s)")
            
            # Set GPU from environment variable if specified
            gpu_id = os.getenv("CUDA_VISIBLE_DEVICES")
            if gpu_id is not None:
                self.current_gpu = int(gpu_id)
                torch.cuda.set_device(self.current_gpu)
            
            # Print GPU info
            for i in range(self.available_gpus):
                print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
                print(f"  Memory: {torch.cuda.get_device_properties(i).total_memory / 1e9:.2f} GB")
        else:
            self.device = "cpu"
            print("GPU not available, using CPU")
    
    def get_device(self):
        """Get the current device (cuda or cpu)"""
        return self.device
    
    def get_memory_info(self) -> Dict[str, float]:
        """Get GPU memory information"""
        if self.device == "cuda":
            allocated = torch.cuda.memory_allocated(self.current_gpu) / 1e9
            reserved = torch.cuda.memory_reserved(self.current_gpu) / 1e9
            total = torch.cuda.get_device_properties(self.current_gpu).total_memory / 1e9
            return {
                "allocated_gb": allocated,
                "reserved_gb": reserved,
                "total_gb": total,
                "free_gb": total - reserved
            }
        return {"device": "cpu", "memory_gb": "N/A"}
    
    def clear_cache(self):
        """Clear GPU cache"""
        if self.device == "cuda":
            torch.cuda.empty_cache()
    
    def set_gpu(self, gpu_id: int):
        """Set the current GPU device"""
        if gpu_id < self.available_gpus:
            self.current_gpu = gpu_id
            torch.cuda.set_device(gpu_id)
        else:
            raise ValueError(f"GPU {gpu_id} not available. Only {self.available_gpus} GPU(s) available.")


class ModelManager:
    """Manages loading and inference of ML models"""
    
    def __init__(self, accelerator: GPUAccelerator):
        self.accelerator = accelerator
        self.models = {}
    
    def load_sentence_transformer(self, model_name: str, model_key: str = "default"):
        """Load a sentence transformer model"""
        from sentence_transformers import SentenceTransformer
        
        if model_key not in self.models:
            print(f"Loading sentence transformer: {model_name}")
            model = SentenceTransformer(model_name, device=self.accelerator.get_device())
            self.models[model_key] = model
            print(f"Model loaded on {self.accelerator.get_device()}")
        
        return self.models[model_key]
    
    def load_transformer_model(self, model_name: str, model_key: str = "default"):
        """Load a transformer model for classification/generation"""
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        
        if model_key not in self.models:
            print(f"Loading transformer model: {model_name}")
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(model_name)
            model.to(self.accelerator.get_device())
            self.models[model_key] = {
                "model": model,
                "tokenizer": tokenizer
            }
            print(f"Model loaded on {self.accelerator.get_device()}")
        
        return self.models[model_key]
    
    def get_model(self, model_key: str):
        """Get a loaded model by key"""
        return self.models.get(model_key)
    
    def unload_model(self, model_key: str):
        """Unload a model from memory"""
        if model_key in self.models:
            del self.models[model_key]
            self.accelerator.clear_cache()


# Global instances
gpu_accelerator = GPUAccelerator()
model_manager = ModelManager(gpu_accelerator)


def get_gpu_accelerator() -> GPUAccelerator:
    """Get the global GPU accelerator instance"""
    return gpu_accelerator


def get_model_manager() -> ModelManager:
    """Get the global model manager instance"""
    return model_manager


def batch_encode_texts(
    model,
    texts: List[str],
    batch_size: int = 32,
    show_progress: bool = False
) -> np.ndarray:
    """Batch encode texts using a sentence transformer"""
    return model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        convert_to_numpy=True
    )


def compute_similarity_matrix(
    embeddings1: np.ndarray,
    embeddings2: np.ndarray
) -> np.ndarray:
    """Compute cosine similarity matrix between two sets of embeddings"""
    from sentence_transformers import util
    import torch
    
    tensor1 = torch.from_numpy(embeddings1)
    tensor2 = torch.from_numpy(embeddings2)
    
    if gpu_accelerator.get_device() == "cuda":
        tensor1 = tensor1.cuda()
        tensor2 = tensor2.cuda()
    
    similarity_matrix = util.cos_sim(tensor1, tensor2)
    
    return similarity_matrix.cpu().numpy()


if __name__ == "__main__":
    # Test GPU acceleration
    accelerator = get_gpu_accelerator()
    print(f"Device: {accelerator.get_device()}")
    print(f"Memory Info: {accelerator.get_memory_info()}")
    
    # Test model loading
    manager = get_model_manager()
    model = manager.load_sentence_transformer(
        "sentence-transformers/all-MiniLM-L6-v2",
        "test_model"
    )
    
    # Test encoding
    texts = ["This is a test sentence.", "Another test sentence."]
    embeddings = batch_encode_texts(model, texts)
    print(f"Embeddings shape: {embeddings.shape}")
