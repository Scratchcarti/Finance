import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd
from datetime import datetime


# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd
# custom lookup
app.jinja_env.filters["lookup"] = lookup

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# INDEX


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    data = db.execute("SELECT * FROM clientdata WHERE userid = ?",
                      session["user_id"])
    cah = db.execute("SELECT cash FROM users WHERE id = ?",
                     session["user_id"])[0]["cash"]

    ttl = 0
    for x in range(len(data)):

        a = (lookup(data[x]["symbol"])["price"]) * (data[x]["shares"])
        ttl = ttl + a

    return render_template("index.html", data=data, money=float(cah), fake=float(ttl))


# BUY


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")

    elif request.method == "POST":

        sym = (request.form.get("symbol")).upper()
        if not request.form.get("shares").isdigit():
            return apology("its not a digit")
        shr = int(request.form.get("shares"))

        if (not sym) or (not lookup(sym)):
            return apology("Symbol doesnt exist")

        if shr <= 0 :
            return apology("Weird shares")

        cash = (db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"]))[0]["cash"]

        if (cash >= (shr * lookup(sym)["price"])):

            try:
                db.execute("INSERT INTO clientdata (userid,symbol,shares,time) VALUES(?,?,?,?)",
                           session["user_id"], sym, shr, datetime.now())
            except ValueError:
                db.execute(" UPDATE clientdata SET shares = shares + (?) WHERE userid = (?) AND symbol = (?)",
                           shr, session["user_id"], sym)

            db.execute("INSERT INTO buydata(id,symbol,shares,time,cost) VALUES(?,?,?,?,?)",
                       session["user_id"], sym, shr, datetime.now(), lookup(sym)["price"])
            db.execute("UPDATE users SET cash = (?) WHERE id = (?)",
                       (cash - (shr * lookup(sym)["price"])), session["user_id"])

            return redirect("/")

        else:
            return apology("get your bread up broke boy")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    if request.method == "GET":
        bhai = db.execute("SELECT * FROM buydata WHERE id = (?)", session["user_id"])
        salmon = db.execute("SELECT * FROM selldata WHERE id = (?)", session["user_id"])
        return render_template("history.html", bhai=bhai, salmon=salmon)

    return apology("TODO")

# LOGIN


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

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
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
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

# QUOTE


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")

    elif request.method == "POST":

        symb = request.form.get("symbol")

        dicc = lookup(symb)

        if not dicc:
            return apology("Enter a valid symbol")

        else:
            val = dicc["price"]

            return render_template("quoted.html", symb=symb, val=usd(val))

    return apology("quote not working prop")


# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        uss = request.form.get("username")
        pss = request.form.get("password")
        cpss = request.form.get("confirmation")

    # username shi and pass shi

        if not uss:
            return apology("must provide username", 400)

        if not pss:
            return apology("Must provide password", 400)

        if pss != cpss:
            return apology("Passwords must match", 400)

        try:
            db.execute("INSERT INTO users (username,hash) VALUES(?,?)", uss, generate_password_hash(pss))

        except:
            return apology("Username already exist")

        return redirect("/")

    elif request.method == "GET":

        return render_template("register.html")

    return apology("Some retded error??")

# SELL THAT SHI


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "GET":
        symbols = db.execute("SELECT symbol FROM clientdata WHERE userid = ?",
                             session["user_id"])

        return render_template("sell.html", symbols=symbols)

    elif request.method == "POST":

        symb = request.form.get("symbol")
        shr = int(request.form.get("shares"))

        wha = db.execute("SELECT * FROM clientdata WHERE userid = ?",
                         session["user_id"])
    # FIRST DUMB CONDITION

        count = 0
        for x in range(len(wha)):
            if (symb == wha[x]["symbol"]):
                count += 1
        if (count == 0):
            return apology("what the fuu")

        # SECOND CONDI

        else:
            usr = db.execute("SELECT shares FROM clientdata WHERE userid = ? AND symbol = ?", session["user_id"], symb)[0]["shares"]

            if usr < shr or shr <= 0:
                return apology("know your worth")

            else:
                db.execute("UPDATE clientdata SET shares = shares - (?) WHERE symbol = ? AND userid = ? ",
                           shr, symb, session["user_id"])
                db.execute("UPDATE users SET cash = cash + (?)",
                           (shr)*(lookup(symb)["price"]))
                db.execute("INSERT INTO selldata(id,symbol,shares,time,cost) VALUES(?,?,?,?,?)",
                           session["user_id"], symb, shr, datetime.now(), lookup(symb)["price"])

                return redirect("/")

    return apology("kys")


@app.route("/cpass", methods=["GET", "POST"])
@login_required
def cpass():

    if request.method == "GET":
        return render_template("cpass.html")

    elif request.method == "POST":

        oldp = (request.form.get("oldpass"))
        newp = (request.form.get("newpass"))
        cp = (request.form.get("confirm"))

        if (check_password_hash((db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"]))[0]["hash"], oldp)):

            if (newp == cp):

                db.execute("UPDATE users SET hash = (?) WHERE id = ? ",
                           generate_password_hash(cp), session["user_id"])

                return redirect("/")

            else:
                return apology("NEW Passwords donot match")

        else:
            return apology("Old password is incorrect")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)