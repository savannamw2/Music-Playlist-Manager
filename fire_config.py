# firebase_config.py

import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase

# Initialize Firebase Admin SDK
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()

# Initialize Pyrebase for authentication
firebase = pyrebase.initialize_app({
    "apiKey": "YOUR_API_KEY",
    "authDomain": "YOUR_PROJECT_ID.firebaseapp.com",
    "databaseURL": "https://YOUR_PROJECT_ID.firebaseio.com",
    "projectId": "YOUR_PROJECT_ID",
    "storageBucket": "YOUR_PROJECT_ID.appspot.com",
    "messagingSenderId": "YOUR_SENDER_ID",
    "appId": "YOUR_APP_ID",
    "measurementId": "YOUR_MEASUREMENT_ID"
})

auth = firebase.auth()
