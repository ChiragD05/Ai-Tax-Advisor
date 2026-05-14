import os
import shutil
from typing import Any, Dict, List, Optional

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase_service_account"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()


def create_chat_session(user_email: str, title: str = "New Chat") -> str:
    doc_ref = db.collection("chat_sessions").document()
    doc_ref.set({
        "user": user_email,
        "title": title,
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP,
        "vectorstore_path": None,
    })
    return doc_ref.id


def list_chat_sessions(user_email: str) -> List[Dict[str, Any]]:
    docs = (
        db.collection("chat_sessions")
        .where("user", "==", user_email)
        .stream()
    )

    sessions = [{"id": d.id, **d.to_dict()} for d in docs]

    # Sort in Python to avoid Firestore composite index requirement
    sessions.sort(
        key=lambda x: x.get("updated_at") or x.get("created_at"),
        reverse=True
    )

    return sessions


def load_chat_messages(session_id: str) -> List[Dict[str, Any]]:
    docs = (
        db.collection("chat_sessions")
        .document(session_id)
        .collection("messages")
        .order_by("created_at")
        .stream()
    )

    return [{"id": d.id, **d.to_dict()} for d in docs]


def ensure_session_doc(session_id: str) -> None:
    """
    Make sure the parent chat document exists.
    """
    session_ref = db.collection("chat_sessions").document(session_id)
    session_ref.set(
        {"updated_at": firestore.SERVER_TIMESTAMP},
        merge=True
    )


def save_chat_message(session_id: str, role: str, content: str) -> None:
    """
    Save a message under a chat session.

    Uses set(..., merge=True) so the parent doc is created if it doesn't exist,
    which prevents the Firestore 404 update error.
    """
    session_ref = db.collection("chat_sessions").document(session_id)

    # Ensure parent document exists
    session_ref.set(
        {"updated_at": firestore.SERVER_TIMESTAMP},
        merge=True
    )

    session_ref.collection("messages").add({
        "role": role,
        "content": content,
        "created_at": firestore.SERVER_TIMESTAMP,
    })


def save_resource(
    session_id: str,
    filename: str,
    file_path: str,
    index_path: Optional[str] = None
) -> None:
    session_ref = db.collection("chat_sessions").document(session_id)

    session_ref.set(
        {
            "vectorstore_path": index_path,
            "updated_at": firestore.SERVER_TIMESTAMP,
        },
        merge=True
    )

    session_ref.collection("resources").add({
        "filename": filename,
        "file_path": file_path,
        "index_path": index_path,
        "created_at": firestore.SERVER_TIMESTAMP,
    })


def delete_chat_session(session_id: str) -> None:
    session_ref = db.collection("chat_sessions").document(session_id)

    # Delete messages
    for msg in session_ref.collection("messages").stream():
        msg.reference.delete()

    # Delete resources and linked local files
    for res in session_ref.collection("resources").stream():
        data = res.to_dict()
        file_path = data.get("file_path")
        index_path = data.get("index_path")

        if file_path and os.path.exists(file_path):
            os.remove(file_path)

        if index_path and os.path.exists(index_path):
            shutil.rmtree(index_path, ignore_errors=True)

        res.reference.delete()

    # Delete the session document itself
    session_ref.delete()