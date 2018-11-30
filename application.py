import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///leadership.db")


@app.route("/register", methods=["GET", "POST"])
def register():

    # If the request method is POST, do the below
    if request.method == "POST":

        # Apologises with the message "Missing username" if the new user (manager) did not provide a username
        if not request.form.get("username"):
            return apology("Missing username")

        # Apologises with the message "Missing password" if the new user (manager) did not provide a password in the first password field
        if not request.form.get("password"):
            return apology("Missing password")

        # Apologises with the message "Passwords don't match" if the new user (manager) did not provide a password in the confirmation field or the passwords in
        # The password field and in the confirmation field do not match
        if not request.form.get("confirmation") or request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords don't match")

        # Hashes the password provided by the user (manager)
        hashed_password = generate_password_hash(request.form.get("password"))

        # Inserts the new user (manager) (i.e. username, hashed password and type of user) to the table "user" of the database (the below function will
        # Return "none" if the provided username does already exist in the table "users", since the field "username" is a unique field in the table)
        result = db.execute("INSERT INTO users (username, hash, manager_or_employee) VALUES (:username, :hashed_password, 'manager')",
                            username=request.form.get("username"), hashed_password=hashed_password)

        # Apologises with the message "Username is not available" if the provided username does already exist in the table "users"
        if not result:
            return apology("Username is not available")

        # Logs the new user (manager) in by storing his/her id number in sessions
        id_ = db.execute("SELECT id FROM users WHERE username = :username", username=request.form.get("username"))
        session["user_id"] = id_[0]["id"]

        # Redirects the new user (manager) to the homepage for managers
        return redirect("/manager_index")

    # If the request method is GET, this renders the template "register.html" via which a person can register for the site
    else:
        return render_template("register.html")


@app.route("/check", methods=["GET"])
def check():

    # Stores the username that the user provided via /register in the variable "username"
    username = request.args.get("username")

    # If the user did not provide a username or if there already is a user in the table "users" who has the same username as the one provided by the
    # New user, this returns, in JSON format, false
    registered_users = db.execute("SELECT * FROM users WHERE username = :username", username=username)
    if not username or registered_users:
        return jsonify(False)

    # Otherwise, this returns, in JSON format, true
    return jsonify(True)


@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # If user is manager, redirect user to the homepage for managers
        if rows[0]["manager_or_employee"] == "manager":
            return redirect("/manager_index")

        # If user is employee, redirect user to the homepage for employees
        if rows[0]["manager_or_employee"] == "employee":
            return redirect("/employee_index")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/manager_index")
@login_required
def manager_index():

    return render_template("manager_index.html")


@app.route("/manager_request_feedback", methods=["GET", "POST"])
@login_required
def manager_request_feedback():

    # If the request method is POST, do the below
    if request.method == "POST":
        print("hello")
        # TODO MORRIS

    # If the request method is GET, this renders the template "manager_request_feedback.html" via which the logged-in manager can ...
    else:
        # TODO MORRIS
        return render_template("manager_request_feedback.html")


@app.route("/manager_self_assessment", methods=["GET", "POST"])
@login_required
def manager_self_assessment():

    if request.method == "POST":
        manager_id = request.form.get("manager_id")
        Q1 = request.form.get("Q1")
        Q2 = request.form.get("Q2")
        Q3 = request.form.get("Q3")
        Q4 = request.form.get("Q4")
        Q5 = request.form.get("Q5")
        Q6 = request.form.get("Q6")
        Q7 = request.form.get("Q7")
        Q8 = request.form.get("Q8")
        Q9 = request.form.get("Q9")
        Q10 = request.form.get("Q10")
        Q11 = request.form.get("Q11")
        Q12 = request.form.get("Q12")
        Q13 = request.form.get("Q13")
        Q14 = request.form.get("Q14")
        Q15 = request.form.get("Q15")
        Q16 = request.form.get("Q16")
        Q17 = request.form.get("Q17")
        Q18 = request.form.get("Q18")
        Q19 = request.form.get("Q19")
        Q20 = request.form.get("Q20")
        Q21 = request.form.get("Q21")
        Q22 = request.form.get("Q22")
        Q23 = request.form.get("Q23")
        Q24 = request.form.get("Q24")
        Q25 = request.form.get("Q25")
        Q26 = request.form.get("Q26")
        Q27 = request.form.get("Q27")
        Q28 = request.form.get("Q28")
        Q29 = request.form.get("Q29")
        Q30 = request.form.get("Q30")
        Q31 = request.form.get("Q31")
        Q32 = request.form.get("Q32")
        Q33 = request.form.get("Q33")
        Q34 = request.form.get("Q34")
        Q35 = request.form.get("Q35")
        Q36 = request.form.get("Q36")
        Q37 = request.form.get("Q37")
        Q38 = request.form.get("Q38")
        Q39 = request.form.get("Q39")
        Q40 = request.form.get("Q40")
        Description = request.form.get("Description")

        # insert the survey values into the table
        selfassessment = db.execute("INSERT INTO surveyanswers(manager_id, Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q10, Q11, Q12, Q13, Q14, Q15, Q16, Q17, Q18, Q19, Q20, Q21, Q22, Q23, Q24, Q25, Q26, Q27, Q28, Q29, Q30, Q31, Q32, Q33, Q34, Q35, Q36, Q37, Q38, Q39, Q40, Description) VALUES (:manager_id, :Q1, :Q2, :Q3, :Q4, :Q5, :Q6, :Q7, :Q8, :Q9, :Q10, :Q11, :Q12, :Q13, :Q14, :Q15, :Q16, :Q17, :Q18, :Q19, :Q20, :Q21, :Q22, :Q23, :Q24, :Q25, :Q26, :Q27, :Q28, :Q29, :Q30, :Q31, :Q32, :Q33, :Q34, :Q35, :Q36, :Q37, :Q38, :Q39, :Q40, :Description)",
                                    manager_id = manager_id, Q1=Q1, Q2=Q2, Q3=Q3, Q4=Q4, Q5=Q5, Q6=Q6, Q7=Q7, Q8=Q8, Q9=Q9, Q10=Q10, Q11=Q11, Q12=Q12, Q13=Q13, Q14=Q14, Q15=Q15, Q16=Q16, Q17=Q17, Q18=Q18, Q19=Q19, Q20=Q20, Q21=Q21, Q22=Q22, Q23=Q23, Q24=Q24, Q25=Q25, Q26=Q26, Q27=Q27, Q28=Q28, Q29=Q29, Q30=Q30, Q31=Q31, Q32=Q32, Q33=Q33, Q34=Q34, Q35=Q35, Q36=Q36, Q37=Q37, Q38=Q38, Q39=Q39, Q40=Q40, Description=Description)

        if not selfassessment:
            print("hello")
        return apology("Thank you for submitting")

        # Dont submit twice -> maybe add SQL column with default value of 0 and adding 1 if filled out and checking that?

    else:
        return render_template("manager_self-assessment.html")


@app.route("/manager_view_report")
@login_required
def manager_view_report():

    # TODO
    return render_template("manager_view_report.html")


@app.route("/employee_index")
@login_required
def employee_index():

    if request.method == "POST":

        manager_id = request.form.get("manager_id")
        Q1 = request.form.get("Q1")
        Q2 = request.form.get("Q2")
        Q3 = request.form.get("Q3")
        Q4 = request.form.get("Q4")
        Q5 = request.form.get("Q5")
        Q6 = request.form.get("Q6")
        Q7 = request.form.get("Q7")
        Q8 = request.form.get("Q8")
        Q9 = request.form.get("Q9")
        Q10 = request.form.get("Q10")
        Q11 = request.form.get("Q11")
        Q12 = request.form.get("Q12")
        Q13 = request.form.get("Q13")
        Q14 = request.form.get("Q14")
        Q15 = request.form.get("Q15")
        Q16 = request.form.get("Q16")
        Q17 = request.form.get("Q17")
        Q18 = request.form.get("Q18")
        Q19 = request.form.get("Q19")
        Q20 = request.form.get("Q20")
        Q21 = request.form.get("Q21")
        Q22 = request.form.get("Q22")
        Q23 = request.form.get("Q23")
        Q24 = request.form.get("Q24")
        Q25 = request.form.get("Q25")
        Q26 = request.form.get("Q26")
        Q27 = request.form.get("Q27")
        Q28 = request.form.get("Q28")
        Q29 = request.form.get("Q29")
        Q30 = request.form.get("Q30")
        Q31 = request.form.get("Q31")
        Q32 = request.form.get("Q32")
        Q33 = request.form.get("Q33")
        Q34 = request.form.get("Q34")
        Q35 = request.form.get("Q35")
        Q36 = request.form.get("Q36")
        Q37 = request.form.get("Q37")
        Q38 = request.form.get("Q38")
        Q39 = request.form.get("Q39")
        Q40 = request.form.get("Q40")
        Description = request.form.get("Description")

        # insert the survey values into the table
        selfassessment = db.execute("INSERT INTO surveyanswers (user_id, manager_id, Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q10, Q11, \
        Q12, Q13, Q14, Q15, Q16, Q17, Q18, Q19, Q20, Q21, Q22, Q23, Q24, Q25, Q26, Q27, Q28, Q29, Q30, Q31, Q32, Q33, Q34, Q35, Q36, \
        Q37, Q38, Q39, Q40, Description) \
        VALUES(:user_id, :manager_id, :Q1, :Q2, :Q3, :Q4, :Q5, :Q6, :Q7, :Q8, :Q9, :Q10, :Q11, :Q12, :Q13, :Q14, :Q15, :Q16, :Q17, \
        :Q18, :Q19, :Q20, :Q21, :Q22, :Q23, :Q24, :Q25, :Q26, :Q27, :Q28, :Q29, :Q30, :Q31, :Q32,:Q33, :Q34, :Q35, :Q36, :Q37, :Q38,\
        :Q39, :Q40, :Description)",
        user_id=session["user_id"], manager_id = manager_id, Q1=Q1, Q2=Q2, Q3=Q3, Q4=Q4, Q5=Q5, Q6=Q6, Q7=Q7, Q8=Q8, Q9=Q9, Q10=Q10,
        Q11=Q11, Q12=Q12, Q13=Q13, Q14=Q14, Q15=Q15, Q16=Q16, Q17=Q17, Q18=Q18, Q19=Q19, Q20=Q20, Q21=Q21, Q22=Q22, Q23=Q23, Q24=Q24,
        Q25=Q25, Q26=Q26, Q27=Q27, Q28=Q28, Q29=Q29, Q30=Q30, Q31=Q31, Q32=Q32, Q33=Q33, Q34=Q34, Q35=Q35, Q36=Q36, Q37=Q37, Q38=Q38,
        Q39=Q39, Q40=Q40, Description=Description)

        return render_template("employee_index.html")

    else:
        # Name Manager
        # Questionnaire
        # Dont submit twice
        return render_template("employee_index.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
