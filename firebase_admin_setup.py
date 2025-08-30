import os
from firebase_admin import credentials, firestore, initialize_app

# Relative path to the service account key file
SERVICE_ACCOUNT_KEY_PATH = os.path.join(os.path.dirname(__file__), '.\\credentials\\firebase-adminsdk.json')

cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
initialize_app(cred)

db = firestore.client()


#TEST
# import firebase_admin
# from firebase_admin import credentials, firestore

# def test_firebase_admin():
# try:
#     cred = credentials.Certificate("serviceAccountKey.json")
#     firebase_admin.initialize_app(cred)
#     db = firestore.client()

#     # Try to get some info — list collections or a test doc read
#     collections = db.collections()
#     print("Firebase Admin initialized successfully. Collections:")
#     for coll in collections:
#         print("-", coll.id)
#     return True
# except Exception as e:
#     print(f"Firebase Admin initialization failed: {e}")
#     return False

# if __name__ == "__main__":
# test_firebase_admin()
