from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=12000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=30)


class ChatResponse(BaseModel):
    answer: str
    configured: bool


class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    pages: int
    extracted_characters: int
    has_text: bool


class DocumentChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=12000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)


class DocumentChatResponse(BaseModel):
    answer: str
    references: list[int]
    configured: bool
