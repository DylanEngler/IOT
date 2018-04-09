#! /usr/bin/python3.5
# -*- coding:utf-8 -*-

from flask import Flask, render_template, url_for, redirect, request, g, session
import mysql.connector
from passlib.hash import argon2
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit
import requests
import datetime

app = Flask(__name__)
app.config.from_object('config')
app.config.from_object('secret_config')


def connect_db():
    g.mysql_connection = mysql.connector.connect(
        host=app.config['DATABASE_HOST'],
        user=app.config['DATABASE_USER'],
        password=app.config['DATABASE_PASSWORD'],
        database=app.config['DATABASE_NAME']
    )

    g.mysql_cursor = g.mysql_connection.cursor()
    return g.mysql_cursor


def get_db():
    if not hasattr(g, 'db'):
        g.db = connect_db()
    return g.db


def commit():
    g.mysql_connection.commit()


def Recup_status(adresse):
    status_code = 999
    try:
        r = requests.get(adresse, timeout=2)
        r.raise_for_status()
        status_code = r.status_code
    except requests.exceptions.HTTPError as errh:
        status_code = r.status_code
    except requests.exceptions.ConnectionError as errc:
        pass
    except requests.exceptions.Timeout as errt:
        pass
    except requests.exceptions.RequestException as err:
        pass
    return str(status_code)


def status_all():
    with app.app_context():
        db = get_db()
        db.execute('SELECT id, adresse_web FROM adresse')
        adresse = db.fetchall()
        f = '%Y-%m-%d %H:%M:%S'
        for addr in adresse:
            id = addr[0]
            adresse_web = addr[1]
            status = Recup_status(adresse_web)
            test = datetime.datetime.now()
            date=test.strftime(f)
            db = get_db()
            db.execute('INSERT INTO historique (id_web, reponse_requete, date_derniere_requete) VALUES (%(id)s, %(status)s, %(date_requete)s)', {'id': id, 'status': status, 'date_requete': date})
        commit()


scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(
    func=status_all,
    trigger=IntervalTrigger(seconds=60),
    id='status_all',
    name='Ajout status',
    replace_existing=True)
atexit.register(lambda: scheduler.shutdown())


@app.route('/')
def index():
    db = get_db()
    db.execute('SELECT a.id, a.adresse_web, h.reponse_requete FROM adresse a, historique h WHERE a.id = h.id_web and h.date_derniere_requete=(SELECT MAX(date_derniere_requete) from historique hi where hi.id_web = a.id) GROUP BY a.id, a.adresse_web, h.reponse_requete')
    adresse = db.fetchall()
    return render_template("index.html", adresse = adresse)


@app.route('/historique/<int:id>')
def historique(id):
    db = get_db()
    db.execute('SELECT a.adresse_web, h.reponse_requete, h.date_derniere_requete from adresse a, historique h WHERE a.id = h.id_web AND a.id = %(id)s ORDER BY date_derniere_requete DESC', {'id': id})
    historique = db.fetchall()
    return render_template("historique.html", historique=historique)


@app.route('/login/', methods=['GET', 'POST'])
def login():
    email = str(request.form.get('email'))
    password = str(request.form.get('password'))

    db = get_db()
    db.execute('SELECT email, password, is_admin FROM user WHERE email = %(email)s', {'email': email})
    users = db.fetchall()

    valid_user = False
    for user in users:
        if argon2.verify(password, user[1]):
            valid_user = user

    if valid_user:
        session['user'] = valid_user
        return redirect(url_for('admin'))

    return render_template('login.html')


@app.route('/admin/')
def admin():

    db = get_db()
    db.execute('SELECT id, adresse_web FROM adresse')
    adresse = db.fetchall()
    if not session.get('user') or not session.get('user')[2]:
        return redirect(url_for('login'))
    return render_template('admin.html', user=session['user'], adresse=adresse)

@app.route('/admin/add/',methods=['GET', 'POST'])
def admin_add() :
    if not session.get('user') or not session.get('user')[2]:
        return redirect(url_for('login'))

    if request.method == 'POST':
        page = str(request.form.get('Page'))
        db = get_db()
        db.execute('INSERT INTO adresse (adresse_web) VALUES (%(page)s)', {'page': page})
        commit()
        return redirect(url_for('admin'))

    return render_template('admin_add.html')


@app.route('/admin/editer/<int:id>', methods=['GET', 'POST'])
def editer(id):

    if not session.get('user') or not session.get('user')[2]:
        return redirect(url_for('login'))
    db = get_db()

    if request.method == 'POST':
        page = str(request.form.get('Page'))
        db.execute('UPDATE adresse SET adresse_web = %(page)s WHERE id = %(id)s', {'page': page,'id': id})
        commit()
        return redirect(url_for('admin'))

    else:
        db.execute('SELECT id, adresse_web FROM adresse WHERE id = %(id)s', {'id': id})
        adresse = db.fetchone()
        return render_template('admin_edit.html', user=session['user'], adresse=adresse)


@app.route('/admin/supprimer/<int:id>', methods=['GET', 'POST'])
def supprimer(id):
    if not session.get('user') or not session.get('user')[2]:
        return redirect(url_for('login'))

    db = get_db()
    if request.method == 'POST':
        db.execute('DELETE FROM adresse WHERE id = %(id)s', {'id': id})
        commit()
        return redirect(url_for('admin'))

    else:
        db.execute('SELECT id, adresse_web FROM adresse WHERE id = %(id)s', {'id': id})
        adresse = db.fetchone()
        return render_template('admin_sup.html', user=session['user'], adresse=adresse)

@app.route('/admin/logout/')
def admin_logout():
    session.clear()
    return redirect(url_for('login'))

@app.teardown_appcontext
def close_db (error):
    if hasattr(g, 'db'):
        g.db.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')


