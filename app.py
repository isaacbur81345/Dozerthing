from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

import json
import re
import secrets
import base64
import time
import os
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)
TOKEN = os.getenv("secretkey")

BASE_DIR = Path(__file__).resolve().parent
thejsonfilething = BASE_DIR / "users.json"

if not thejsonfilething.exists():
    with open(thejsonfilething, "w") as f:
        json.dump({"users": {}, "tokens": {}}, f)

with open(thejsonfilething) as f:
    users = json.load(f)

cooldownusers = {}
cooldownglobal = time.time() - 60
ratelimitsettings = 10 #per minute, low, but worth it
accountratelimit = {"exampleperson":time.time()-61} #the same with users

app = Flask(__name__)
o = '<a href="/login">Login </a>\n<a href="/signin"> Sign in </a>'
app.secret_key = TOKEN.encode()

#s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def valid_password(password):
    return 8 <= len(password) <= 128

def is_url_safe(username):
    return re.fullmatch(r"[A-Za-z0-9_-]{3,32}", username) is not None

def save_users(users):
    with open(thejsonfilething, "w") as f:
        json.dump(users, f, indent=4)

def tokenize(user):
    randomlet = secrets.token_urlsafe()
    baseuser = base64.b85encode(user.encode())

    return f"{baseuser}_{randomlet}"

@app.route("/")
def show():
    user = None

    if "token" in session:
        if session["token"] in users["tokens"]:
            usert = users["tokens"][session["token"]]
            user = users["users"][usert]["Display"]
    
    print(f"[INFO] {user} has logged into the main site.")

    return render_template("index.html", displayname = user)

@app.route("/dozerUI", methods=['GET', 'POST'])
def dozer():
    if request.method == 'GET':
        user = None

        if "token" in session:
            if session["token"] in users["tokens"]:
                usert = users["tokens"][session["token"]]
                user = users["users"][usert]["Display"]

        print(f"[INFO] {user} has logged into the dozer site.")

        return render_template("dozer.html", displayname = user)
    else:
        if "token" in session:
            if session["token"] in users["tokens"]:
                usert = users["tokens"][session["token"]]
                user = users["users"][usert]["Display"]

        print(f"[INFO] {user} has tried to spawn a dozer in the dozer site.")

        if not user:
            return {"text":"Ay, you ain't real!"}
        
        if time.time() - cooldownglobal < 10:
            return {"text":"On global cooldown!"}

        if user in cooldownusers:
            if time.time() - cooldownusers[user] < 60:
                return {"text":"On user cooldown!"}
            else:
                cooldownusers[user] = time.time()
                #s.sendto(user.encode(), ("localhost", 5067))
                return {"text":"Dozer spawned"}
        else:
            cooldownusers[user] = time.time()
            #s.sendto(user.encode(), ("localhost", 5067))
            return {"text":"Dozer spawned"}
        
@app.route("/dozerUI/leaderboard", methods=['GET', 'POST'])
def lead():
    if request.method == 'GET':
        user = None

        if "token" in session:
            if session["token"] in users["tokens"]:
                usert = users["tokens"][session["token"]]
                user = users["users"][usert]["Display"]

        print(f"[INFO] {user} has logged into the leaderboard site.")

        return render_template("leaderboard.html", displayname = user)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if "token" in session:
            if session["token"] in users["tokens"]:
                usert = users["tokens"][session["token"]]
                user = users["users"][usert]["Display"]
                return redirect(url_for('show'))

        return render_template("login.html")
    elif request.method == 'POST':
        if "token" in session:
            if session["token"] in users["tokens"]:
                usert = users["tokens"][session["token"]]
                user = users["users"][usert]["Display"]
                return redirect(url_for('show'))

        user = request.form['user']
        passw = request.form['password']
        user = users["users"].get(user.strip().lower())
        if user:
            if check_password_hash(user["passw"], passw):
                session["token"] = user["t"]
                print(f"[INFO] someone logged in as {user}")
                return jsonify({"success":True, "string":"/"})
            else:
                return jsonify({"success":False, "string":"Wrong user or password"})
        else:
            return jsonify({"success":False, "string":"Wrong user or password"})

@app.route("/logout", methods=['POST'])
def logout():
    if request.method == 'POST':
        del session["token"]
        return "yay"
        
@app.route("/signin", methods=['GET', 'POST'])
def signin():
    if request.method == 'GET':
        if "token" in session:
            if session["token"] in users["tokens"]:
                usert = users["tokens"][session["token"]]
                user = users["users"][usert]["Display"]
                return redirect(url_for('show'))

        return render_template("signin.html")
    elif request.method == 'POST':
        if "token" in session:
            if session["token"] in users["tokens"]:
                usert = users["tokens"][session["token"]]
                user = users["users"][usert]["Display"]
                return redirect(url_for('show'))

        if "accounts" in session:
            if session["accounts"] > 1:
                return jsonify({"success":False, "string":"Reached limit of accounts in device."})

        user = request.form['user']
        passw = request.form['password']

        if not is_url_safe(user):
            return jsonify({"success":False, "string":"User is not appropiate to the system, make sure your user only contains Letters, numbers, or _ and - and is between the range of 3 and 32."})
        
        if not valid_password(passw):
            return jsonify({"success":False, "string":"Allowed password range is 8-128"})
        
        usern = users["users"].get(user.strip().lower())
        if usern:
            return jsonify({"success":False, "string":"User already exists."})
        else:
            hashpass = generate_password_hash(passw)
            token = tokenize(user.strip().lower())

            try:
                if "accounts" in session:
                    session["accounts"] = session["accounts"] + 1
                else:
                    session["accounts"] = 1

                users["users"][user.strip().lower()] = {"Display":user,"passw":hashpass,"dozerperms":False, "t":token}
                users["tokens"][token] = user.strip().lower()
                save_users(users)
                session["token"] = token

                print(f"[INFO] new account: {user}")

                return jsonify({"success":True, "string":"/"})
            except KeyError as e:
                if user.strip().lower() in users["users"]:
                    del users["users"][user.strip().lower()]

                if token in users["tokens"]:
                    del users["tokens"][token]
                
                print(e)
                return jsonify({"success":False, "string":"unexpected error bro... WERE ALL GONNA DIE WERE ALL GONNA DIE"})

@app.route('/api/screenshare', methods=['GET'])
def share():
    if request.method == 'GET':
        key = request.args.get('key', '')
        username = request.cookies.get('username')
        print(username)
        if key == "IsaacBJ":
            return "yeah"
        else:
            return "hey. what are you doing. go away."
    else:
        return "no"

if __name__ == "__main__":
    app.run()