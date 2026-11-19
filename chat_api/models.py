import uuid
from django.db import models
from django.utils import timezone


class ChatSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, default="New Conversation")
    created_at = models.DateTimeField(auto_now_add=True)
    last_active_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session {self.session_id} - {self.title}"


class Document(models.Model):
    MODE_CHOICES = [
        ('FULL', 'Full-Context Mode'),
        ('RAG', 'Retrieval (RAG) Mode'),
    ]
    STATUS_CHOICES = [
        ('UPLOADING', 'Uploading'),
        ('EXTRACTING', 'Extracting'),
        ('INDEXING', 'Indexing'),
        ('READY', 'Ready'),
        ('FAILED', 'Failed'),
    ]

    document_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="documents")
    name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)  # pdf, docx, txt, md, pasted
    size_bytes = models.BigIntegerField(default=0)
    page_count = models.IntegerField(default=1)
    token_count = models.IntegerField(default=0)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='FULL')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='READY')
    is_active = models.BooleanField(default=True)
    raw_text = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.file_type}, {self.page_count} pages)"


class DocumentChunk(models.Model):
    chunk_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.IntegerField(default=0)
    page_start = models.IntegerField(default=1)
    page_end = models.IntegerField(default=1)
    section_heading = models.CharField(max_length=255, blank=True, default="")
    text = models.TextField()

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.name} (p.{self.page_start})"


class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('bot', 'Bot'),
    ]
    STATUS_CHOICES = [
        ('ANSWERED', 'Answered'),
        ('PARTIAL', 'Partial'),
        ('NOT_FOUND', 'Not Found'),
        ('OUT_OF_SCOPE', 'Out Of Scope'),
        ('ERROR', 'Error'),
    ]

    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    text = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True, null=True)
    citations = models.JSONField(default=list, blank=True)
    missing_info = models.TextField(blank=True, null=True)
    tokens_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.role}] {self.text[:40]}"


class Feedback(models.Model):
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name="feedbacks")
    rating = models.CharField(max_length=10)  # up / down
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
