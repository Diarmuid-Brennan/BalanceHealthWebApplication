from flask import (
    Flask,
    render_template,
    url_for,
    redirect,
    request,
    session,
    flash,
    json,
)
import os

# from flask_bootstrap import Bootstrap
from data_utils import (
    register_user,
    login_user,
    add_patient,
    get_patients,
    add_activity,
    get_activities,
    get_patient,
    get_patient_activities,
    add_patient_activity,
    get_activity_results,
    add_activities,
    get_patient_scores,
    add_comment,
    retrieve_comments,
)
from models.patient import Patient
import pygal
from pygal.style import Style
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
import seaborn as sns
from io import BytesIO
import base64
import plotly
import plotly.express as px
from datetime import date, timedelta, datetime
import time
import numpy as np
from flask import Markup

user = {"is_logged_in": False}

app = Flask(__name__)

app.config["SECRET_KEY"] = os.urandom(24)


@app.route("/")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        userDetails = request.form
        userlogin = login_user(userDetails)
        if userlogin == None:
            return render_template("login.html")
        global user
        user["is_logged_in"] = True
        session["userId"] = userlogin["localId"]
        return render_template("welcome.html")
    return render_template("login.html")


@app.route("/logout")
def logout():
    global user
    user["is_logged_in"] = False
    session.clear()
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        userDetails = request.form
        if validate_register_details(userDetails):
            userregister = register_user(userDetails)
            if userregister == None:
                return render_template("register.html")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/welcome")
def welcome():
    if user["is_logged_in"] == True:
        return render_template("welcome.html")
    else:
        flash("You must be logged in to access webpage.", "error")
        return redirect(url_for("login"))


@app.route("/create_patient", methods=["GET", "POST"])
def create_patient():
	if user["is_logged_in"] == True:
		if request.method == "POST":
			userDetails = request.form
			add_patient(userDetails)
			return render_template("create_patient.html")
		return render_template("create_patient.html")


	else:
		flash("You must be logged in to access webpage.", "error")
		return redirect(url_for('login'))


@app.route("/edit_patient", methods=["GET", "POST"])
def edit_patient():
    if user["is_logged_in"] == True:
        data = get_patients()
        patient_details = None
        if request.method == "POST":
            userDetails = request.form
            email = userDetails["results"]
            if email == "":
                add_patient(userDetails)
            else:
                email = userDetails["results"]
                patient_details = get_patient(email)

            return render_template(
                "edit_patient.html", data=data, patient_details=patient_details
            )
        return render_template(
            "edit_patient.html", data=data, patient_details=patient_details
        )
    else:
        flash("You must be logged in to access webpage.", "error")
        return redirect(url_for("login"))


@app.route("/view_patients", methods=["GET", "POST"])
def view_patients():
    if user["is_logged_in"] == True:
        if request.method == "POST":
            session["user_email"] = request.form["user_email"]
            return redirect(url_for("patient_details"))
        data = get_patients()
        return render_template("view_patients.html", data=data)
    else:
        flash("You must be logged in to access webpage.", "error")
        return redirect(url_for("login"))


@app.route("/patient_details", methods=["GET", "POST"])
def patient_details():
    if user["is_logged_in"] == True:
        if "user_email" in session:
            user_email = session["user_email"]

        patient_detail = get_patient(user_email)
        if patient_detail == None:
            return redirect(url_for("view_patients"))
        session["patient_detail"] = patient_detail

        patient_activities = get_patient_activities(user_email)
        session["patient_activities"] = patient_activities

        if request.method == "POST":
            details = request.form
            if details["activity"] == "feetTogether":
                patient_comments = retrieve_comments(
                    "Stand with your feet side-by-side", user_email
                )
            elif details["activity"] == "instep":
                patient_comments = retrieve_comments("Instep Stance", user_email)
            elif details["activity"] == "tandem":
                patient_comments = retrieve_comments("Tandem Stance", user_email)
            elif details["activity"] == "general":
                patient_comments = retrieve_comments("General comments", user_email)
            else:
                patient_comments = retrieve_comments("Stand on one foot", user_email)
        else:
            patient_comments = retrieve_comments("General comments", user_email)
        print(patient_comments)
        return render_template(
            "patient_details.html",
            data=patient_detail,
            patient_comments=patient_comments,
            patient_activities=patient_activities,
        )
    else:
        flash("You must be logged in to access webpage.", "error")
        return redirect(url_for("login"))


@app.route("/create_activity", methods=["GET", "POST"])
def create_activity():
    if user["is_logged_in"] == True:
        if request.method == "POST":
            activityDetails = request.form
            add_activity(activityDetails)
            return render_template("create_activity.html")
        return render_template("create_activity.html")
    else:
        flash("You must be logged in to access webpage.", "error")
        return redirect(url_for("login"))


@app.route("/view_activities")
def view_activities():
    if user["is_logged_in"] == True:
        data = get_activities()
        return render_template("view_activities.html", data=data)
    else:
        flash("You must be logged in to access webpage.", "error")
        return redirect(url_for("login"))


@app.route("/view_activity_progress", methods=["GET", "POST"])
def view_activity_progress():
	if user["is_logged_in"] == True:

		user_email = session["user_email"]
		activities = get_activities()
		patient_scores = get_patient_scores(user_email)
		rows = create_activity_rows(patient_scores)
		df = pd.DataFrame(rows)
		df["date_set"] = pd.to_datetime(df["date_set"], format="%Y-%m-%d", utc=True).dt.date

		activitiesTaken_df = df[df["activityName"] == "Stand with your feet side-by-side"]
		firstDate = activitiesTaken_df["date_set"].min()
		today = date.today()

		idx = pd.date_range(firstDate, today)
		idx = idx[-7:]
		s = activitiesTaken_df.groupby(["date_set"]).size()
		s = s.reindex(idx, fill_value=0)
		fig, ax = plt.subplots()
		plt.xticks(rotation=90)
		plt.yticks([0, 1])

		ax.bar(idx.to_pydatetime(), s, color="red")
		ax.set_title("Dates activities taken last week", fontsize=18, color="#8C55AA")

		fig.savefig("static/images/fig.png")

		fig = px.bar(
        			df,
        			x="activityName",
        			color="completed",
        			barmode="group",
        			text="date_set",
        			title="Activities completed",
        			labels=dict(count="Activities carried out"),
    				)
		fig.write_image("static/images/fig1.png")

		percentages = calculate_percentages(df)

		sunburst = px.sunburst(df, path=["activityName", "date_set", "completed"])
		sunburst.write_image("static/images/fig4.png")

		df = df.sort_values(by="date_set", ascending=False)
		df = df[
        		["activityName", "date_set", "max_value", "min_value", "avg_value", "completed"]
    			]
		last_date = df["date_set"].max()
		lastActivity = df[df["date_set"] == last_date]
		last_week = df[df["date_set"] > (today - timedelta(7))]
		last_month = df[df["date_set"] > (today - timedelta(28))]

		if request.method == "POST":
			details = request.form
			comment = details["comment_made"]
			if comment == "":
				if details["results"] == "row_data_lastweek":
					row_data = list(last_week.values.tolist())
				elif details["results"] == "row_data":
					row_data = list(lastActivity.values.tolist())
				elif details["results"] == "row_data_lastmonth":
					row_data = list(last_month.values.tolist())
				else:
					row_data = list(df.values.tolist())
			else:
				if "user_email" in session:
					user_email = session["user_email"]
				add_comment(details, user_email, "General comments")
				row_data = list(lastActivity.values.tolist())
		else:
			row_data = list(lastActivity.values.tolist())

		return render_template(
        				"view_activity_progress.html",
        				activities=activities,
        				patient_scores=patient_scores,
        				column_names=df.columns.values,
        				row_data=row_data,
        				percentages=percentages,
        				lastActivity=last_date,
    					)


	else:
		flash("You must be logged in to access webpage.", "error")
		return redirect(url_for('login'))


def create_activity_rows(patient_scores):
    rows = []
    for data in patient_scores:
        if "Stand with your feet side-by-side" in data.keys():
            data_row = data["Stand with your feet side-by-side"]
            rows.append(data_row)
        if "Tandem Stance" in data.keys():
            data_row1 = data["Tandem Stance"]
            rows.append(data_row1)
        if "Instep Stance" in data.keys():
            data_row2 = data["Instep Stance"]
            rows.append(data_row2)
        if "Stand on one foot" in data.keys():
            data_row3 = data["Stand on one foot"]
            rows.append(data_row3)
    return rows


def calculate_percentages(df):
    numInstepSuccess = df[
        (df["completed"] == True) & (df["activityName"] == "Instep Stance")
    ].shape[0]
    numInstep = df[(df["activityName"] == "Instep Stance")].shape[0]

    numTademSuccess = df[
        (df["completed"] == True) & (df["activityName"] == "Tandem Stance")
    ].shape[0]
    numTandem = df[(df["activityName"] == "Tandem Stance")].shape[0]

    numFeetTogetherSuccess = df[
        (df["completed"] == True)
        & (df["activityName"] == "Stand with your feet side-by-side")
    ].shape[0]
    numFeetTogether = df[
        (df["activityName"] == "Stand with your feet side-by-side")
    ].shape[0]

    numOneFootSuccess = df[
        (df["completed"] == True) & (df["activityName"] == "Stand on one foot")
    ].shape[0]
    numOneFoot = df[(df["activityName"] == "Stand on one foot")].shape[0]

    percentages = [
        (round(((numFeetTogetherSuccess / numFeetTogether) * 100), 2)),
        (round(((numInstepSuccess / numInstep) * 100), 2)),
        (round(((numTademSuccess / numTandem) * 100), 2)),
        (round(((numOneFootSuccess / numOneFoot) * 100), 2)),
    ]
    return percentages


@app.route("/view_selected_activity/<activity>", methods=["GET", "POST"])
def view_selected_activity(activity):
	if user["is_logged_in"] == True:
		if request.method == "POST":
			if "user_email" in session:
				user_email = session["user_email"]
			comments = request.form
			add_comment(comments, user_email, activity)

		activities = get_activities()
		activities = [i for i in activities if not (i["name"] == activity)]
		dict1 = {"name": "Overall"}
		activities.append(dict1)
		patient_scores = get_patient_scores("malone@gmail.com")
		rows = create_activity_rows(patient_scores)
		df = pd.DataFrame(rows)
		df = df[df["activityName"] == activity]

		fig2 = px.sunburst(
        				df.head(7),
        				path=["date_set", "completed"],
        				hover_name="activityName",
        				color="completed",
    					)
		fig2.write_image("static/images/fig3.png")

		fig = px.line(
        			df, x="date_set", y=["avg_value", "max_value"], title="Overall Average Score"
    				)
		fig.write_image("static/images/fig2.png")

		i = 0
		fig = Figure()
		font1 = {"family": "serif", "color": "blue", "size": 10}
		fig = plt.figure(figsize=(18, 16))
		for index, row in df.head(7).iterrows():
			i = i + 1

			y = np.array(row["acc_data"])
			plt.subplot(3, 3, i)
			if row["completed"] is False:
				plt.plot(y, color="r")
			else:
				plt.plot(y)  # Plot the chart

			plt.title(activity + row["date_set"], fontdict=font1)
			plt.xlabel("Time")
			plt.ylabel("Movement")

		pngImage = io.BytesIO()
		FigureCanvas(fig).print_png(pngImage)
		pngImageB64String = "data:image/png;base64,"
		pngImageB64String += base64.b64encode(pngImage.getvalue()).decode("utf8")

		return render_template(
        			"view_selected_activity.html", activities=activities, image=pngImageB64String
   					 )


	else:
		flash("You must be logged in to access webpage.", "error")
		return redirect(url_for('login'))


def validate_register_details(data):
    if data["confirm_password"] != data["password"]:
        flash("Passwords do not match.", "error")
        return False
    return True


if __name__ == "__main__":
    app.run(debug=True)
