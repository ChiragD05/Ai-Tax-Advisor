import os
import shutil
from typing import Any, Dict, List, Optional
from datetime import datetime
from utils.supabase_client import supabase


def create_chat_session(
    user_email: str,
    title: str = "New Chat"
) -> str:
    try:
        result = (
            supabase.table("chat_sessions")
            .insert({
                "user_email": user_email,
                "title": title,
                "vectorstore_path": None
            })
            .execute()
        )
        if result.data and len(result.data) > 0:
            return result.data[0]["id"]
        raise ValueError("No data returned from database insert")
    except Exception as e:
        print(f"Error creating chat session: {e}")
        raise RuntimeError(f"Database error while creating session: {e}")


def list_chat_sessions(
    user_email: str
) -> List[Dict[str, Any]]:
    try:
        result = (
            supabase.table("chat_sessions")
            .select("*")
            .eq("user_email", user_email)
            .order("updated_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception as e:
        print(f"Error listing chat sessions: {e}")
        return []


def load_chat_messages(
    session_id: str
) -> List[Dict[str, Any]]:
    try:
        result = (
            supabase.table("chat_messages")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at")
            .execute()
        )
        return result.data or []
    except Exception as e:
        print(f"Error loading chat messages: {e}")
        return []


def ensure_session_doc(
    session_id: str
):
    pass


def save_chat_message(
    session_id: str,
    role: str,
    content: str
):
    try:
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
    except Exception as e:
        print(f"Error saving chat message: {e}")

    try:
        # Update chat timestamp
        (
            supabase.table("chat_sessions")
            .update({
                "updated_at": datetime.utcnow().isoformat()
            })
            .eq("id", session_id)
            .execute()
        )
    except Exception as e:
        print(f"Error updating chat session timestamp: {e}")


def save_resource(
    session_id: str,
    filename: str,
    file_path: str,
    index_path: Optional[str] = None
):
    try:
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
    except Exception as e:
        print(f"Error saving resource: {e}")

    try:
        (
            supabase.table("chat_sessions")
            .update({
                "vectorstore_path": index_path
            })
            .eq("id", session_id)
            .execute()
        )
    except Exception as e:
        print(f"Error updating chat session vectorstore: {e}")


def delete_chat_session(
    session_id: str
):
    try:
        resources = (
            supabase.table("resources")
            .select("*")
            .eq("session_id", session_id)
            .execute()
        )
        res_data = resources.data or []
    except Exception as e:
        print(f"Error listing resources for deletion: {e}")
        res_data = []

    for res in res_data:
        file_path = res.get("file_path")
        index_path = res.get("index_path")

        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error removing file {file_path}: {e}")

        if index_path and os.path.exists(index_path):
            try:
                shutil.rmtree(index_path, ignore_errors=True)
            except Exception as e:
                print(f"Error deleting index directory {index_path}: {e}")

    try:
        (
            supabase.table("chat_messages")
            .delete()
            .eq("session_id", session_id)
            .execute()
        )
    except Exception as e:
        print(f"Error deleting chat messages: {e}")

    try:
        (
            supabase.table("resources")
            .delete()
            .eq("session_id", session_id)
            .execute()
        )
    except Exception as e:
        print(f"Error deleting resources: {e}")

    try:
        (
            supabase.table("chat_sessions")
            .delete()
            .eq("id", session_id)
            .execute()
        )
    except Exception as e:
        print(f"Error deleting chat session: {e}")