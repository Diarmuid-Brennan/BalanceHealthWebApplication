import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import pyrebase
from flask import flash
import json
from flask import session
from models.patient import Patient
import config as cfg
from datetime import date, timedelta, datetime

cred = credentials.Certificate("firebase_sdk.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

firebaseConfig = cfg.firebaseConfig
firebase = pyrebase.initialize_app(firebaseConfig)
storage = firebase.storage()
# storage = getStorage(firebase_admin);
auth = firebase.auth()


def register_user(user_details):
    try:
        user = auth.create_user_with_email_and_password(
            user_details["email"], user_details["password"]
        )
        register_medical_staff(user["localId"], user_details)
        flash("SUCCESSFULLY REGISTERED USER.", "success")
        return user
    except Exception as e:
        flash(json.loads(e.args[1])["error"]["message"], "error")
        return None


def register_medical_staff(userId, user_details):
    try:
        doc_ref = db.collection(u"medical_staff").document(userId)
        doc_ref.set(
            {
                u"firstname": user_details["first_name"],
                u"lastname": user_details["last_name"],
                u"email": user_details["email"],
                u"userUid": userId,
            }
        )
    except Exception as e:
        flash(json.loads(e.args[1])["error"]["message"], "error")


def login_user(user_details):
    try:
        login = auth.sign_in_with_email_and_password(
            user_details["email"], user_details["password"]
        )
        doc_ref = db.collection(u"medical_staff").document(login["localId"])
        doc = doc_ref.get()
        if doc.exists:
            return login
        else:
            flash("Could not authenticate user", "error")
            return None

    except Exception as e:
        flash(json.loads(e.args[1])["error"]["message"], "error")
        return None


def add_activity(activity_details):
    try:
        doc_ref = db.collection(u"activities").add(
            {
                u"name": activity_details["activity_name"],
                u"description": activity_details["description"],
                u"time_limit": int(activity_details["time_limit"]),
            }
        )
        flash("SUCCESSFULLY Added activity.", "success")
    except Exception as e:
        flash(json.loads(e.args[1])["error"]["message"], "error")


def add_comment(comment, email, activity):
    try:
        today = date.today().strftime("%Y-%m-%d")
        print(today)
        doc_ref = (
            db.collection(u"comments")
            .document(email)
            .collection(activity)
            .add(
                {u"comment": comment["comment"], u"date": today, u"activity": activity,}
            )
        )
    except Exception as e:
        flash(json.loads(e.args[1])["error"]["message"], "error")


def retrieve_comments(activity, email):
    try:
        comments = []
        docs = (
            db.collection(u"comments")
            .document(email)
            .collection(activity)
            .order_by(u"date", direction=firestore.Query.DESCENDING)
            .stream()
        )
        for doc in docs:
            comment = doc.to_dict()
            comments.append(comment)
        return comments
    except Exception as e:
        flash(json.loads(e.args[1])["error"]["message"], "error")


def get_activities():
    try:
        docs = db.collection(u"activities").stream()
        activities = []
        for doc in docs:
            activity = doc.to_dict()
            activities.append(activity)
        return activities
    except Exception as e:
        flash(json.loads(e.args[1])["error"]["message"], "error")


def add_patient(user_details):
    try:
        userid = (session['userId'])
        doc_ref = (
            db.collection(u"patients")
            .document(userid)
            .collection(u"patient_details")
            .document(user_details["email"])
            .set(
                {
                    u"firstname": user_details["first_name"],
                    u"lastname": user_details["last_name"],
                    u"email": user_details["email"],
                    u"D.O.B": user_details["age"],
                    u"condition": user_details["condition"],
                }
            )
        )
        # storage.child(image).put(image)
        # bucket = storage.bucket()

        # img = cv2.imread(image)
        # imageBlob = bucket.blob(os.path.basename(image)
        # cv2.imshow('image',img)

        # storage.put(imageBlob)
        # download
        # storage.child(image).download(filename='myimage.png', path=os.path.basename(image)
        flash("SUCCESSFULLY Added/Updated patient.", "success")
    except Exception as e:
        flash(json.loads(e.args[1])["error"]["message"], "error")


def add_activities(email):
    activities = get_activities()
    for a in activities:
        try:
            doc_ref = (
                db.collection(u"patient_activities")
                .document(email)
                .collection(u"activities")
                .document(a["name"])
                .set(
                    {
                        u"name": a["name"],
                        u"description": a["description"],
                        u"time_limit": int(a["time_limit"]),
                    }
                )
            )
        except Exception as e:
            flash(json.loads(e.args[1])["error"]["message"], "error")


def get_patients():
    try:
        userid = (session['userId'])
        docs = (
            db.collection(u"patients")
            .document(userid)
            .collection(u"patient_details")
            .stream()
        )
        patients = []
        for doc in docs:
            patient = doc.to_dict()
            patients.append(patient)
        return patients
    except Exception as e:
        flash(json.loads(e.args[1])["error"]["message"], "error")


def get_patient(email):
    try:
        userid = (session['userId'])
        doc_ref = (
            db.collection(u"patients")
            .document(userid)
            .collection(u"patient_details")
            .document(email)
        )

        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            flash("No record found for patient.", "error")
            return None
    except Exception as e:
        flash(json.loads(e.args[1])["error"]["message"], "error")
        return None


def get_patient_activities(email):
    try:
        docs = (
            db.collection(u"patient_activities")
            .document(email)
            .collection(u"activities")
            .stream()
        )
        patient_activities = []
        for d in docs:
            activity = d.to_dict()
            patient_activities.append(activity)
        return patient_activities
    except Exception as e:
        flash(json.loads(e.args[1])["error"]["message"], "error")


def get_patient_scores(email):
    try:
        docs = (
            db.collection(u"patient_scores")
            .document(email)
            .collection(u"scores")
            .stream()
        )
        patient_scores = []
        for d in docs:
            score = d.to_dict()
            patient_scores.append(score)
        return patient_scores
    except Exception as e:
        flash(json.loads(e.args[1])["error"]["message"], "error")


def add_patient_activity(activity_details, email):
    try:
        doc_ref = (
            db.collection(u"patient_activities")
            .document(email)
            .collection(u"activities")
            .document(activity_details["name"])
            .set(
                {
                    u"name": activity_details["name"],
                    u"description": activity_details["description"],
                    u"time_limit": int(activity_details["time_limit"]),
                }
            )
        )
    except Exception as e:
        flash(json.loads(e.args[1])["error"]["message"], "error")


def get_activity_results(activity, email):
    try:
        docs = (
            db.collection(u"patient_activities")
            .document(email)
            .collection(u"activities")
            .document(activity)
            .collection(u"scores")
            .stream()
        )
        scores = []
        for doc in docs:
            activity = doc.to_dict()
            scores.append(activity)
        return scores
    except Exception as e:
        flash(json.loads(e.args[1])["error"]["message"], "error")
