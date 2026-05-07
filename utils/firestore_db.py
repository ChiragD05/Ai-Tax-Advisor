import os
import shutil
import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate("utils/firebase_service_account.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()


def create_chat_session(user_email, title="New Chat"):
    doc_ref = db.collection("chat_sessions").document()
    doc_ref.set({
        "user": user_email,
        "title": title,
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP,
        "vectorstore_path": None,
    })
    return doc_ref.id


def list_chat_sessions(user_email):
    docs = (
        db.collection("chat_sessions")
        .where("user", "==", user_email)
        .stream()
    )

    sessions = [{"id": d.id, **d.to_dict()} for d in docs]

    sessions.sort(
        key=lambda x: x.get("updated_at") or x.get("created_at"),
        reverse=True
    )

    return sessions


def save_chat_message(session_id, role, content):
    db.collection("chat_sessions").document(session_id).collection("messages").add({
        "role": role,
        "content": content,
        "created_at": firestore.SERVER_TIMESTAMP,
    })
    db.collection("chat_sessions").document(session_id).update({
        "updated_at": firestore.SERVER_TIMESTAMP
    })


def load_chat_messages(session_id):
    docs = (
        db.collection("chat_sessions")
        .document(session_id)
        .collection("messages")
        .order_by("created_at")
        .stream()
    )
    return [{"id": d.id, **d.to_dict()} for d in docs]


def save_resource(session_id, filename, file_path, index_path=None):
    db.collection("chat_sessions").document(session_id).collection("resources").add({
        "filename": filename,
        "file_path": file_path,
        "index_path": index_path,
        "created_at": firestore.SERVER_TIMESTAMP,
    })
    db.collection("chat_sessions").document(session_id).update({
        "vectorstore_path": index_path,
        "updated_at": firestore.SERVER_TIMESTAMP,
    })


def delete_chat_session(session_id):
    session_ref = db.collection("chat_sessions").document(session_id)

    # delete messages
    for msg in session_ref.collection("messages").stream():
        msg.reference.delete()

    # delete resources + local files
    for res in session_ref.collection("resources").stream():
        data = res.to_dict()
        file_path = data.get("file_path")
        index_path = data.get("index_path")

        if file_path and os.path.exists(file_path):
            os.remove(file_path)

        if index_path and os.path.exists(index_path):
            shutil.rmtree(index_path, ignore_errors=True)

        res.reference.delete()

    session_ref.delete()