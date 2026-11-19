import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.conf import settings

from .models import ChatSession, Document, DocumentChunk, ChatMessage, Feedback
from .college_policy_data import POLICY_PAGES, get_full_policy_text, get_policy_summary
from .services.document_processor import (
    extract_from_pdf,
    extract_from_docx,
    extract_from_plain_text,
    count_tokens,
    chunk_document
)
from .services.rag_engine import build_prompt_and_query


def ensure_default_college_policy(session: ChatSession) -> Document:
    """Ensure session has the Meridian College Policy Handbook 2026-2027 loaded."""
    existing = session.documents.filter(is_active=True).first()
    if existing:
        return existing

    full_text = get_full_policy_text()
    tokens = count_tokens(full_text)
    
    doc = Document.objects.create(
        session=session,
        name="Meridian College Policy Handbook 2026-2027",
        file_type="pdf",
        size_bytes=len(full_text.encode('utf-8')),
        page_count=len(POLICY_PAGES),
        token_count=tokens,
        mode='FULL',
        status='READY',
        is_active=True,
        raw_text=full_text
    )

    # Also generate chunks for reference
    chunks = chunk_document(full_text, chunk_size=800, overlap=120)
    chunk_objs = [
        DocumentChunk(
            document=doc,
            chunk_index=c["chunk_index"],
            page_start=c["page_start"],
            page_end=c["page_end"],
            section_heading=c["section_heading"],
            text=c["text"]
        )
        for c in chunks
    ]
    DocumentChunk.objects.bulk_create(chunk_objs)
    return doc


class SessionView(APIView):
    """POST /api/sessions, DELETE /api/sessions/<id>"""

    def post(self, request):
        session = ChatSession.objects.create()
        # Automatically attach the Meridian College Policy Handbook as default knowledge base
        default_doc = ensure_default_college_policy(session)

        return Response({
            "session_id": str(session.session_id),
            "created_at": session.created_at.isoformat(),
            "active_document": {
                "document_id": str(default_doc.document_id),
                "name": default_doc.name,
                "file_type": default_doc.file_type,
                "page_count": default_doc.page_count,
                "token_count": default_doc.token_count,
                "mode": default_doc.mode,
                "status": default_doc.status,
            }
        }, status=status.HTTP_201_CREATED)

    def delete(self, request, session_id):
        session = get_object_or_404(ChatSession, session_id=session_id)
        session.delete()
        return Response({"message": "Session and all associated data deleted successfully."})


class DocumentUploadView(APIView):
    """POST /api/documents, GET /api/documents/<id>, DELETE /api/documents/<id>"""

    def post(self, request):
        session_id = request.data.get("session_id")
        if not session_id:
            return Response({"error": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        session = get_object_or_404(ChatSession, session_id=session_id)
        config = getattr(settings, 'DOCUCHAT_CONFIG', {})
        max_file_size = config.get("MAX_FILE_SIZE_MB", 20) * 1024 * 1024
        max_pages = config.get("MAX_PAGES", 300)
        max_paste_chars = config.get("MAX_PASTE_CHARS", 100000)

        # Check if raw text was pasted (UC-05)
        pasted_text = request.data.get("pasted_text")
        uploaded_file = request.FILES.get("file")

        if not uploaded_file and not pasted_text:
            return Response(
                {"error": "Please provide an uploaded file or pasted text."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Deactivate old documents for this session
        session.documents.all().update(is_active=False)

        if pasted_text:
            if len(pasted_text) > max_paste_chars:
                return Response(
                    {"error": f"Pasted text exceeds maximum character limit of {max_paste_chars}."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            raw_text, page_count = extract_from_plain_text(pasted_text, "Pasted Content")
            file_name = request.data.get("doc_name") or "Pasted Text Document"
            file_type = "txt"
            size_bytes = len(pasted_text.encode('utf-8'))
        else:
            file_name = uploaded_file.name
            size_bytes = uploaded_file.size
            if size_bytes > max_file_size:
                return Response(
                    {"error": f"File size exceeds limit of {config.get('MAX_FILE_SIZE_MB', 20)} MB."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            ext = file_name.split(".")[-1].lower() if "." in file_name else ""
            if ext not in ["pdf", "docx", "txt", "md"]:
                return Response(
                    {"error": f"Unsupported file type .{ext}. Allowed: PDF, DOCX, TXT, MD."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            file_bytes = uploaded_file.read()
            file_type = ext

            try:
                if ext == "pdf":
                    raw_text, page_count = extract_from_pdf(file_bytes)
                elif ext == "docx":
                    raw_text, page_count = extract_from_docx(file_bytes)
                else:
                    raw_text, page_count = extract_from_plain_text(
                        file_bytes.decode('utf-8', errors='ignore'), file_name
                    )
            except Exception as e:
                return Response(
                    {"error": f"Failed to extract document text: {str(e)}"},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY
                )

        if not raw_text.strip():
            return Response(
                {"error": "No readable text found in document. Please upload a machine-readable document."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if page_count > max_pages:
            return Response(
                {"error": f"Document has {page_count} pages, exceeding the limit of {max_pages} pages."},
                status=status.HTTP_400_BAD_REQUEST
            )

        tokens = count_tokens(raw_text)
        mode = 'FULL' if tokens <= config.get("FULL_CONTEXT_TOKEN_THRESHOLD", 100000) else 'RAG'

        doc = Document.objects.create(
            session=session,
            name=file_name,
            file_type=file_type,
            size_bytes=size_bytes,
            page_count=page_count,
            token_count=tokens,
            mode=mode,
            status='READY',
            is_active=True,
            raw_text=raw_text
        )

        # Chunk document
        chunks = chunk_document(raw_text, chunk_size=config.get("CHUNK_SIZE", 800), overlap=config.get("CHUNK_OVERLAP", 120))
        chunk_objs = [
            DocumentChunk(
                document=doc,
                chunk_index=c["chunk_index"],
                page_start=c["page_start"],
                page_end=c["page_end"],
                section_heading=c["section_heading"],
                text=c["text"]
            )
            for c in chunks
        ]
        DocumentChunk.objects.bulk_create(chunk_objs)

        return Response({
            "document_id": str(doc.document_id),
            "name": doc.name,
            "file_type": doc.file_type,
            "size_bytes": doc.size_bytes,
            "page_count": doc.page_count,
            "token_count": doc.token_count,
            "mode": doc.mode,
            "status": doc.status,
            "chunks_count": len(chunks)
        }, status=status.HTTP_201_CREATED)

    def get(self, request, document_id):
        doc = get_object_or_404(Document, document_id=document_id)
        return Response({
            "document_id": str(doc.document_id),
            "name": doc.name,
            "file_type": doc.file_type,
            "size_bytes": doc.size_bytes,
            "page_count": doc.page_count,
            "token_count": doc.token_count,
            "mode": doc.mode,
            "status": doc.status,
            "is_active": doc.is_active,
        })

    def delete(self, request, document_id):
        doc = get_object_or_404(Document, document_id=document_id)
        doc.delete()
        return Response({"message": "Document removed successfully."})


class ChatView(APIView):
    """POST /api/chat"""

    def post(self, request):
        session_id = request.data.get("session_id")
        question = request.data.get("question", "").strip()

        if not session_id:
            return Response({"error": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not question:
            return Response({"error": "Question cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

        config = getattr(settings, 'DOCUCHAT_CONFIG', {})
        max_q_chars = config.get("MAX_QUESTION_CHARS", 2000)
        if len(question) > max_q_chars:
            return Response(
                {"error": f"Question exceeds maximum length of {max_q_chars} characters"},
                status=status.HTTP_400_BAD_REQUEST
            )

        session = get_object_or_404(ChatSession, session_id=session_id)
        
        # Check active document or ensure default
        active_doc = session.documents.filter(is_active=True).first()
        if not active_doc:
            active_doc = ensure_default_college_policy(session)

        if active_doc.status != 'READY':
            return Response(
                {"error": f"Document is still in {active_doc.status} state. Please wait."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Retrieve last N turns of history
        history_turns = config.get("HISTORY_TURNS", 10)
        past_msgs = session.messages.order_by('-created_at')[:history_turns * 2]
        history_list = []
        for m in reversed(past_msgs):
            history_list.append({
                "role": m.role,
                "text": m.text
            })

        # Save user message
        user_msg = ChatMessage.objects.create(
            session=session,
            role="user",
            text=question
        )

        # Call RAG engine with prompt and document
        ai_resp = build_prompt_and_query(active_doc, question, history_list)

        # Save bot response
        bot_msg = ChatMessage.objects.create(
            session=session,
            role="bot",
            text=ai_resp.get("answer", ""),
            status=ai_resp.get("status", "ANSWERED"),
            citations=ai_resp.get("citations", []),
            missing_info=ai_resp.get("missing_info")
        )

        return Response({
            "session_id": str(session.session_id),
            "user_message_id": str(user_msg.message_id),
            "message_id": str(bot_msg.message_id),
            "status": bot_msg.status,
            "answer": bot_msg.text,
            "citations": bot_msg.citations,
            "missing_info": bot_msg.missing_info,
            "created_at": bot_msg.created_at.isoformat()
        })


class MessagesHistoryView(APIView):
    """GET /api/sessions/<id>/messages"""

    def get(self, request, session_id):
        session = get_object_or_404(ChatSession, session_id=session_id)
        messages = session.messages.all().order_by('created_at')
        
        data = [
            {
                "message_id": str(m.message_id),
                "role": m.role,
                "text": m.text,
                "status": m.status,
                "citations": m.citations,
                "missing_info": m.missing_info,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]
        return Response({"session_id": str(session.session_id), "messages": data})


class FeedbackView(APIView):
    """POST /api/feedback"""

    def post(self, request):
        message_id = request.data.get("message_id")
        rating = request.data.get("rating")  # up or down
        comment = request.data.get("comment", "")

        if not message_id or rating not in ["up", "down"]:
            return Response({"error": "message_id and valid rating ('up' or 'down') required"}, status=status.HTTP_400_BAD_REQUEST)

        message = get_object_or_404(ChatMessage, message_id=message_id)
        Feedback.objects.create(
            message=message,
            rating=rating,
            comment=comment
        )
        return Response({"message": "Feedback submitted successfully."})


class CollegePolicyView(APIView):
    """GET /api/college-policy, POST /api/reset-to-policy"""

    def get(self, request):
        summary = get_policy_summary()
        sections = [
            {"page": p["page"], "title": p["title"]}
            for p in POLICY_PAGES
        ]
        starter_questions = [
            "What is the minimum attendance requirement and condonation rules?",
            "What is the grading scale, SGPA/CGPA classification, and passing mark?",
            "What are the hostel entry and exit timings for men and women?",
            "What is the fee refund policy if a student withdraws after 15 days?",
            "What is the college anti-ragging policy and disciplinary action?",
            "Summarise the examination malpractice penalties."
        ]
        return Response({
            "summary": summary,
            "sections": sections,
            "pages": POLICY_PAGES,
            "starter_questions": starter_questions
        })

    def post(self, request):
        session_id = request.data.get("session_id")
        if not session_id:
            return Response({"error": "session_id required"}, status=status.HTTP_400_BAD_REQUEST)
        
        session = get_object_or_404(ChatSession, session_id=session_id)
        # Deactivate any other document and activate default policy
        session.documents.all().update(is_active=False)
        doc = ensure_default_college_policy(session)
        doc.is_active = True
        doc.save()

        return Response({
            "message": "Session reset to Meridian College Policy Handbook 2026-2027",
            "document": {
                "document_id": str(doc.document_id),
                "name": doc.name,
                "file_type": doc.file_type,
                "page_count": doc.page_count,
                "token_count": doc.token_count,
                "mode": doc.mode,
                "status": doc.status
            }
        })
