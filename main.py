import datetime
import os
from flask import Flask, render_template, request, session, redirect, g, url_for
from os import urandom
from pymongo import MongoClient
from datetime import date
from bson.json_util import dumps, loads


app = Flask(__name__)
app.secret_key = urandom(30)
SECRET_KEY = os.getenv('SECRET_KEY')
DB_NAME = os.getenv('DB_NAME')

client = MongoClient(
    "mongodb+srv://DB_NAME:SECRET_KEY@cluster0.2oz9x.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")

profiles = client["Profiles"]
user_collection = profiles["test"]

vaccines = client["vaccines"]
vaccine_info = vaccines["test"]

hsp_prof = client["Hspprof"]
hsp_info = hsp_prof["test"]

today = date.today()


@app.route("/")
def home():
    return "Hello"


@app.route("/login")
def login():
    return render_template("loginpage.html")


@app.route("/signup")
def signup():
    return render_template("signup.html")


@app.route("/hspsignup")
def hspsignup():
    return render_template("hospital_signup.html")


@app.route("/signform", methods=["POST"])
def sign():
    user = {
        'first_name': request.form.get('first-name'),
        'last_name': request.form.get('last-name'),
        'dob': request.form.get('dob'),
        'gender': request.form.get('gen'),
        'emai_id': request.form.get('exampleInputEmail1'),
        'phone_no': request.form.get('pno'),
        'password': request.form.get('exampleInputPassword1')
    }

    profiles.user_collection.insert_one(user)

    return redirect(url_for('login'))


@app.route("/hspsignform", methods=["POST"])
def hspsign():

    h_user = {
        'email': request.form.get('email'),
        'h_name': request.form.get('h-name'),
        'address': request.form.get('address'),
        'location': request.form.get('location'),
        'state': request.form.get('state'),
        'phno': request.form.get('phno'),
        'password': request.form.get('password')
    }

    hsp_prof.hsp_info.insert_one(h_user)

    return redirect(url_for('login'))


@app.route("/log", methods=["POST"])
def log():
    if request.method == 'POST':
        session.pop('user', None)

        if request.form.get('usr_val'):
            p_users = profiles.user_collection.find_one(
                {'emai_id': request.form['email']})
            if p_users:
                if request.form.get("pwd") == p_users["password"]:
                    session['user'] = request.form['email']
                    return redirect(url_for('panel'))
                    # return "welcome"
        if request.form.get('hsp_val'):
            h_users = hsp_prof.hsp_info.find_one(
                {'email': request.form['email']})

            if h_users:

                if request.form.get("pwd") == h_users["password"]:
                    session['user'] = h_users['email']
                    return redirect(url_for('hsppanel'))
                    # return "Welcome Hsp"

    return "Invalid email or password"


@app.route('/hsppanel')
def hsppanel():
    if g.user:
        hsp_name = hsp_prof.hsp_info.find_one(
            {'email': session['user']}, {"_id": 0, "password": 0})
        # hsp_name['list_vaccines'] = hsp_name.get('list_vaccines', [])
        # print(hsp_name, type(hsp_name['list_vaccines']))
        # l = ["Hepatits B", "OPV", "BCG"]
        # for i in l:
        # hsp_name['list_vaccines'].append(i)

        # hsp_prof.hsp_info.replace_one({'email': session['user']}, hsp_name)

        return render_template("hospital_land.html",)
    return redirect(url_for('login'))


@app.route('/panel')
def panel():
    if g.user:
        values = profiles.user_collection.find_one(
            {'emai_id': session['user']})
        dob = str(values['dob'])
        # print(dob)
        t_d = today.strftime("%Y-%m-%d")
        dob = list(dob.split("-"))
        t_d = list(t_d.split("-"))
        time_diff = datetime.date(
            int(dob[0]), int(dob[1]), int(dob[2]))-datetime.date(int(t_d[0]), int(t_d[1]), int(t_d[2]))  # converts to days
        # print(time_diff)
        days = abs(time_diff.days)
        age = []
        age.append(days//365)
        age.append((days % 365)//7)
        age.append(days - ((age[0]*365)+(age[1]*7)))

        find = 0
        cat = "m"
        if age[0]:
            find = round(age[0]*12, 2)
        else:
            find = round(age[1]/4, 2)

        vac_values = loads(dumps(vaccines.vaccine_info.find(
            {'age': {'$lt': find+1}, 'y/m': cat}, {'Vaccine_name': 1, 'age': 1, "_id": 0})))

        p_name, email = values['first_name']+" " + \
            values["last_name"], values["emai_id"]
        for data in vac_values:
            val = data["Vaccine_name"]
            val = val[1:-1]
            val = list(val.split(','))
            data["Vaccine_name"] = val

        vac_hsp = dict()
        for data in vac_values:
            for i in data['Vaccine_name']:
                hs = loads(dumps(hsp_prof.hsp_info.find({'list_vaccines': i})))
                # print(hs[0], type(hs))

                if len(hs) > 1:
                    for j in hs:
                        vac_hsp[i] = vac_hsp.get(
                            i, [])+[[j['email'], j['h_name']]]
                elif len(hs) == 1:
                    vac_hsp[i] = vac_hsp.get(
                        i, [])+[[hs[0]['email'], hs[0]['h_name']]]
        return render_template("landing_page.html", name=p_name, email=email, vaccine_val=vac_values, vac_hsp=vac_hsp)

    return redirect(url_for('login'))


@ app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


@ app.before_request
def before_request():
    g.user = None

    if 'user' in session:
        g.user = session['user']
