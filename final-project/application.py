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
db = SQL("sqlite:///resources.db")


@app.route("/")
@login_required
def index():

    """Show resources"""
    #  Todo
    titles = db.execute("SELECT title FROM data where id=:id", id=session["user_id"])

    return render_template("index.html", titles=titles)


@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """Creates a new resource"""
    # Todo
    if request.method == "POST":
        # Ensure resource title was submitted
        if not request.form.get("title"):
            return apology("must provide title", 403)
        # Ensure resource link was submitted
        elif not request.form.get("link"):
            return apology("must provide resource link or type none", 403)
        # Ensure resource description is added
        elif not request.form.get("details"):
            return apology("must add resouce description or type none", 403)
        title = request.form.get("title")
        link = request.form.get("link")
        description = request.form.get("details")
        notes = request.form.get("notes")
        # check the database if we have the same resouce title
        rows = db.execute("SELECT * FROM data where id=:id AND title=:title", id=session["user_id"], title=title)

        # If we dont have the same resource title we insert a new resource in data table
        if len(rows) == 0:
            db.execute("INSERT INTO data (id, Title, Link, Description, notes) VALUES (:id, :Title, :Link, :Description, :notes)",
                       id=session["user_id"], Title=title, Link=link, Description=description, notes=notes)


            return  render_template("create.html")
        else:
            flash("You already have a resource with the same title.You can update the existing resouce or create a new one with a different title ")
            return  redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("create.html")


@app.route("/resource_details", methods=["GET", "POST"])
@login_required
def resource_details():
    """Show resource details"""
    # Todo
    resource_title = request.args.get('resource_title', None)
    # Query the database for the all the details of the the selected resource title
    details = db.execute("select * from data where id=:id and title=:title",id=session["user_id"], title=resource_title)
    print(details)
    # if the request method is get we display the resource details
    if request.method == 'GET':
        return render_template("resource_details.html", resource_title =resource_title, details=details)
    # if the request method was post
    else:
        # check which button was pressed
        if request.form['submit_button'] == 'update':
            # navigate to the update page to update
            return render_template("update.html", details=details)
        elif request.form['submit_button'] == 'delete':
            # Delete the selected resource and update the database
            db.execute("DELETE FROM data WHERE  id=:id AND title=:title",  id=session["user_id"], title=details[0]["Title"])
            return redirect("/")


@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    """Update a resource """
    resource_title = request.args.get('title', None)
    if request.method == 'POST':
        # Ensure resource title was submitted
        if not request.form.get("title"):
            return apology("must provide title", 403)
        # Ensure resource link was submitted
        elif not request.form.get("link"):
            return apology("must provide resource link or type none", 403)
        # Ensure resource description is added
        elif not request.form.get("details"):
            return apology("must add resouce description or type none", 403)
        title = request.form.get("title")
        link = request.form.get("link")
        description = request.form.get("details")
        notes = request.form.get("notes")
        # check the database if we have the same resouce title
        rows = db.execute("SELECT * FROM data where id=:id AND title=:title", id=session["user_id"], title=title)
        print(rows)
        # check If we have another resource with the same title, other than the one we curruntly want to update
        if len(rows) == 1:
            # check if it is the same resource we are updating
            if rows[0]['Title'] == title:
                # Update the database with the new changes
                db.execute("UPDATE data SET  Link=:Link, Description=:Description, notes=:notes where id=:id And title=:title" ,
                            Link=link, Description=description, notes=notes, id=session["user_id"], title =title)
                # Qurey the database for resource details after updating
                details = db.execute("SELECT * FROM data WHERE id=:id AND title=:title", id=session["user_id"], title=title)
                return render_template("resource_details.html", details=details)
            else:
                flash("You already have a resource with the same title.Please choose a different title")
                details = [{'Title': title, 'Link' : link, 'Description': description, 'Notes': notes}]
                return  render_template("update.html", details=details)
        # Title was changed and we dont have a resource with the same title
        else:

             db.execute("UPDATE data SET  title=:title, Link=:Link, Description=:Description, notes=:notes where id=:id",
                        Link=link, Description=description, notes=notes, id=session["user_id"], title =title)
             # Qurey the database for the updated resource details and passing the values to resource_details template
             details =  db.execute("select * from data where id=:id and title=:title",id=session["user_id"], title=title)
             return render_template("resource_details.html", details=details)
    else:
        # If the request method is GET

        details = db.execute("select * from data where id=:id and title=:title",id=session["user_id"], title=resource_title)
        return render_template("update.html", details=details)



@app.route("/delete")
@login_required
def delete():
    """Edit a resource """
    # Delete resource
    title = request.args.get('title', None)
    # update the database by removing the selected resource title
    db.execute("DELETE FROM data WHERE id=:id and title=:title",id=session["user_id"], title=title)
    return  redirect("/")


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Search for a resource accourding to its title"""
    # Todo
    if request.method == "POST":
        title = request.form.get("title")
        title_qurey = '%'+( request.form.get("title"))+"%"
        print (title)
        # Search the database for the resource with the supplied title
        search_results = db.execute("SELECT title FROM data WHERE id=:id AND title LIKE :title_qurey ", id=session["user_id"], title_qurey=title_qurey)
        count = db.execute("SELECT COUNT(title) FROM data  WHERE id=:id AND title LIKE :title_qurey ", id=session["user_id"], title_qurey=title_qurey)
        print(count)
        if len(search_results) == 0:
            flash("Resource dosen't exist")
            return redirect("/search")
        else:
            return render_template("search_results.html", search_results=search_results, title=title, count=count)
    else:
        return render_template("search.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

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

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)
        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        # Ensure password was confirmed
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 403)
        # Ensure password and confirmed password are the same
        elif request.form.get("confirmation") != request.form.get("password"):
            return apology("passwords does not match", 403)
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))
        # Checks if the username exists
        if len(rows) == 1:
            return apology("username already exists,try another username", 403)
        # Register a new user
        else:
            # Get the password from the form
            password = request.form.get("password")
            # Hash the password using the generate_password_hash function
            hash_password = generate_password_hash(password)
            # Get the new user name from the form
            username = request.form.get("username")
            # Insert the new user in the database
            db.execute("INSERT INTO users(username, hash) VALUES (?, ?)", username, hash_password)
            # Return to the log in page to log in
            flash("Please sign in with the new username and password")
            return render_template("login.html")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/edit")
@login_required
def edit():
    """Edit a resource"""
    flash("Please select a resource to edit")
    return redirect("/")



@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change user password"""
    if request.method == "POST":
        # Ensure old password was submitted
        if not request.form.get("old_password"):
            return apology("must provide old password", 403)
        # Ensure new password was submitted
        elif not request.form.get("new_password"):
            return apology("must provide new password", 403)
        # Ensure new password was confirmed
        elif not request.form.get("confirmation"):
            return apology("must confirm new password", 403)
        # Ensure password and confirmed password are the same
        elif request.form.get("confirmation") != request.form.get("new_password"):
            return apology("passwords does not match", 403)
        # Query database for old password
        rows = db.execute("SELECT hash FROM users WHERE id = :id", id=session["user_id"])
        # Ensure user old password is correct
        if not check_password_hash(rows[0]["hash"], request.form.get("old_password")):
            return apology("invalid old password", 403)

        # Change password
        else:
            # Get the new password from the form
            password = request.form.get("new_password")
            # Hash the new password using the generate_password_hash function
            hash_password = generate_password_hash(password)

            # Update the new password in the database
            db.execute("UPDATE users SET hash=:new_password WHERE id=:id", id=session["user_id"], new_password=hash_password)
            # Return to the index page
            return redirect("/")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("change_password.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)