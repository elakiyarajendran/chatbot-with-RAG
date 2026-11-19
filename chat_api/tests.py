import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from .models import ChatSession, Document, ChatMessage
from .college_policy_data import POLICY_PAGES, get_full_policy_text
from .services.rag_engine import verify_citation


class DocuChatBackendTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_session_loads_default_policy(self):
        """Test that new session attaches the Meridian College Policy Handbook."""
        url = reverse('sessions-create')
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn('session_id', data)
        self.assertIn('active_document', data)
        self.assertEqual(data['active_document']['name'], "Meridian College Policy Handbook 2026-2027")
        self.assertEqual(data['active_document']['page_count'], len(POLICY_PAGES))
        self.assertEqual(data['active_document']['status'], 'READY')

    def test_pasted_text_document_upload(self):
        """Test pasting raw text as knowledge source (FR-05, UC-05)."""
        session_resp = self.client.post(reverse('sessions-create'))
        session_id = session_resp.json()['session_id']

        doc_url = reverse('documents-upload')
        sample_text = "[Page 1]\nLab Safety Regulations:\nSafety goggles must be worn at all times."
        resp = self.client.post(doc_url, {
            "session_id": session_id,
            "pasted_text": sample_text,
            "doc_name": "Lab Safety Guideline"
        })
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['name'], "Lab Safety Guideline")
        self.assertEqual(data['page_count'], 1)
        self.assertEqual(data['status'], 'READY')

    def test_citation_verification(self):
        """Test citation verification logic against document text (FR-42)."""
        doc_text = get_full_policy_text()
        # Real quote from handbook
        real_quote = "A student must have at least 75 per cent attendance in each course"
        self.assertTrue(verify_citation(real_quote, doc_text))

        # Fabricated quote
        fake_quote = "Students are allowed to bring flying carpets to exam halls"
        self.assertFalse(verify_citation(fake_quote, doc_text))

    def test_college_policy_handbook_endpoint(self):
        """Test endpoint providing full handbook metadata and starter questions."""
        url = reverse('college-policy')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('summary', data)
        self.assertEqual(data['summary']['sections_count'], 26)
        self.assertTrue(len(data['starter_questions']) > 0)

    def test_delete_session_data(self):
        """Test UC-06: Remove data deletes session, messages, and documents."""
        session_resp = self.client.post(reverse('sessions-create'))
        session_id = session_resp.json()['session_id']

        delete_url = reverse('sessions-delete', kwargs={'session_id': session_id})
        resp = self.client.delete(delete_url)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(ChatSession.objects.filter(session_id=session_id).exists())
        self.assertFalse(Document.objects.filter(session__session_id=session_id).exists())
