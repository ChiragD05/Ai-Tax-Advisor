import os
import shutil
from typing import Any, Dict, List, Optional
from datetime import datetime
from utils.supabase_client import supabase


def create_chat_session(
    user_email: str,
    title: str = "New Chat"
) -> str:

    result = (
        supabase.table("chat_sessions")
        .insert({
            "user_email": user_email,
            "title": title,
            "vectorstore_path": None
        })
        .execute()
    )

    return result.data[0]["id"]


def list_chat_sessions(
    user_email: str
) -> List[Dict[str, Any]]:

    result = (
        supabase.table("chat_sessions")
        .select("*")
        .eq("user_email", user_email)
        .order("updated_at", desc=True)
        .execute()
    )

    return result.data


def load_chat_messages(
    session_id: str
) -> List[Dict[str, Any]]:

    result = (
        supabase.table("chat_messages")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
    )

    return result.data


def ensure_session_doc(
    session_id: str
):
    pass


from datetime import datetime

def save_chat_message(
    session_id: str,
    role: str,
    content: str
):

    # Save message
    result = (
        supabase.table("chat_messages")
        .insert({
            "session_id": session_id,
            "role": role,
            "content": content
        })
        .execute()
    )

    print("MESSAGE SAVED:", result)

    # Update chat timestamp
    (
        supabase.table("chat_sessions")
        .update({
            "updated_at": datetime.utcnow().isoformat()
        })
        .eq("id", session_id)
        .execute()
    )

def save_resource(
    session_id: str,
    filename: str,
    file_path: str,
    index_path: Optional[str] = None
):

    (
        supabase.table("resources")
        .insert({
            "session_id": session_id,
            "filename": filename,
            "file_path": file_path,
            "index_path": index_path
        })
        .execute()
    )

    (
        supabase.table("chat_sessions")
        .update({
            "vectorstore_path": index_path
        })
        .eq("id", session_id)
        .execute()
    )


def delete_chat_session(
    session_id: str
):

    resources = (
        supabase.table("resources")
        .select("*")
        .eq("session_id", session_id)
        .execute()
    )

    for res in resources.data:

        file_path = res.get("file_path")
        index_path = res.get("index_path")

        if file_path and os.path.exists(file_path):
            os.remove(file_path)

        if index_path and os.path.exists(index_path):
            shutil.rmtree(index_path, ignore_errors=True)

    (
        supabase.table("chat_messages")
        .delete()
        .eq("session_id", session_id)
        .execute()
    )

    (
        supabase.table("resources")
        .delete()
        .eq("session_id", session_id)
        .execute()
    )

    (
        supabase.table("chat_sessions")
        .delete()
        .eq("id", session_id)
        .execute()
    )