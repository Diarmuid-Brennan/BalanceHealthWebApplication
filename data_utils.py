"""
Name : Diarmuid Brennan
Project : Balance Health Web Application
Date : 05/04/2022
data_utils.py 
contains methods for connecting to and communicating with firestore database
"""
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
    """
    register a user using firbase authentication
    
    Parameters
    -------------
    user_details : Entered user details
    
    Displays a message if the user was registered successfully or not
    """
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
    """
    adss a newly register user details to the firestore database
    
    Parameters
    -------------
    user_id : created user firebase UID
    user_details : Entered user details
    
    Displays a message if the user details were added successfully or not
    """
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
    """
    logs in a user using firbase authentication
    
    Parameters
    -------------
    user_details : Entered user login details
    
    Displays an error message if the user details do not match the database entry
    """
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
    """
    adds a balance activity details to the database
    
    Parameters
    -------------
    activity_details : Entered balance activity details
    
    Displays a message if the activity details were added successfully or not
    """
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
    """
    adds a comment for a patinets balance activity performance to the database
    
    Parameters
    -------------
    comment : comment to be stored
    email : patients email address
    activity : name of activity to be commented on
    
    Displays a message if the activity comment added was unsuccessful
    """
    try:
        today = date.today().strftime("%Y-%m-%d")
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
    """
    retrieves comments made for a patinets balance activity performance from the database
    
    Parameters
    -------------
    email : patients email address
    activity : name of activity to retrieve comments from
    
    Displays a message if retrieving activity comments was unsuccessful
    """
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
    """
    retrieves activities from the database  
    
    Displays a message if retrieving activity comments was unsuccessful
    """
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
    """
    adds a new patient details to the database
    
    Parameters
    -------------
    user_details : Entered patient details
    
    Displays a message if the patient details were added successfully or not
    """
    try:
        userid = session["userId"]
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
        flash("SUCCESSFULLY Added/Updated patient.", "success")
    except Exception as e:
        flash(json.loads(e.args[1])["error"]["message"], "error")


def add_activities(email):
    """
    adds activities for a patient to the database
    
    Parameters
    -------------
    email : email address of patient
    
    Displays a message if the patient activity was added unsuccessfully
    """
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
    """
    retrieves patient lists related to the logged in medical personnel from the database
       
    Displays a message if retrieving patients was unsuccessful
    """
    try:
        userid = session["userId"]
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
    """
    retrieves a selected patients details from the database
    
    Parameters
    -------------
    email : email address of patient
       
    Displays a message if request was successful or not
    """
    try:
        userid = session["userId"]
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
    """
    retrieves activities set for a patient from the database
    
    Parameters
    -------------
    email : email address of patient
    
    Displays a message if the request was unsuccessful
    """
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
    """
    retrieves a selected patients activity scores from the database
    
    Parameters
    -------------
    email : email address of patient
       
    Displays a message if request was unsuccessful
    """
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
    """
    adds activities for a patient to the database
    
    Parameters
    -------------
    activity_details : entered details for activity
    email : email address of patient
    
    Displays a message if the request was unsuccessful
    """
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
    """
    retrieves a selected patients activity results from the database
    
    Parameters
    -------------
    actvity : the name of the actvity
    email : email address of patient
       
    Displays a message if request was unsuccessful
    """
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
