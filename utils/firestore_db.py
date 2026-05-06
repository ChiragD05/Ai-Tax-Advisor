import firebase_admin

from firebase_admin import credentials
from firebase_admin import firestore


# Initialize Firebase Admin
if not firebase_admin._apps:

    cred = credentials.Certificate(
        "utils/firebase_service_account.json"
    )

    firebase_admin.initialize_app(cred)


# Firestore client
db = firestore.client()


# Save chat
def save_chat(user_email, question, answer):

    db.collection("chat_history").add({

        "user": user_email,
        "question": question,
        "answer": answer,
        "timestamp": firestore.SERVER_TIMESTAMP

    })


# Get user chats
def get_user_chats(user_email):

    docs = db.collection("chat_history") \
        .where("user", "==", user_email) \
        .stream()

    chats = []

    for doc in docs:

        chats.append(doc.to_dict())

    return chats