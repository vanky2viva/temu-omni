"""AI Provider抽象接口

定义统一的AI Provider接口，支持GPT和DeepSeek等多种实现。
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str  # system, user, assistant
    content: str


class ChatCompletionRequest(BaseModel):
    """聊天完成请求"""
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False


class ChatCompletionResponse(BaseModel):
    """聊天完成响应"""
    content: str
    model: str
    usage: Dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    finish_reason: Optional[str] = None


class AIProvider(ABC):
    """AI Provider抽象基类"""
    
    @abstractmethod
    def chat_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> ChatCompletionResponse:
        """
        聊天完成
        
        Args:
            messages: 消息列表
            model: 模型名称（可选，使用默认模型）
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            聊天完成响应
            
        Raises:
            Exception: API调用失败时抛出
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        获取可用的模型列表
        
        Returns:
            模型名称列表
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        检查Provider是否可用（API密钥是否配置等）
        
        Returns:
            True if available, False otherwise
        """
        pass

