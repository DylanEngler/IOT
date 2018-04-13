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
import os
from slackclient import SlackClient

app = Flask(__name__)
app.config.from_object('config')
app.config.from_object('secret_config')

slack_token = "xoxp-342639127040-342639127264-344459677879-5c0a5fa41c499b94893f932011acfcf7"
sc = SlackClient(slack_token)



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
            if (int(status) != 200):
                sc.api_call(
                    "chat.postMessage",
                    channel="bot",
                    text=str(adresse_web)+"  "+str(status)
                )
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
    md5_d77d5e503ad1439f585ac494268b351b = get_db()
    md5_d77d5e503ad1439f585ac494268b351b.execute('SELECT a.id, a.adresse_web, h.reponse_requete FROM adresse a, historique h WHERE a.id = h.id_web and h.date_derniere_requete=(SELECT MAX(date_derniere_requete) from historique hi where hi.id_web = a.id) GROUP BY a.id, a.adresse_web, h.reponse_requete')
    md5_4bef6bece607e237b5027b6d01a242aa = md5_d77d5e503ad1439f585ac494268b351b.fetchall()
    return render_template("index.html", adresse = md5_4bef6bece607e237b5027b6d01a242aa)


@app.route('/historique/<int:id>')
def historique(id):
    md5_d77d5e503ad1439f585ac494268b351b = get_db()
    md5_d77d5e503ad1439f585ac494268b351b.execute('SELECT a.adresse_web, h.reponse_requete, h.date_derniere_requete from adresse a, historique h WHERE a.id = h.id_web AND a.id = %(id)s ORDER BY date_derniere_requete DESC', {'id': id})
    md5_a2dfcab51cb1743fe7d4c93735d1c604 = md5_d77d5e503ad1439f585ac494268b351b.fetchall()
    return render_template("historique.html", md5_a2dfcab51cb1743fe7d4c93735d1c604=md5_a2dfcab51cb1743fe7d4c93735d1c604)


@app.route('/login/', methods=['GET', 'POST'])
def login():
    email = str(request.form.get('email'))
    password = str(request.form.get('password'))

    md5_d77d5e503ad1439f585ac494268b351b = get_db()
    md5_d77d5e503ad1439f585ac494268b351b.execute('SELECT email, password, is_admin FROM user WHERE email = %(email)s', {'email': email})
    users = md5_d77d5e503ad1439f585ac494268b351b.fetchall()

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
    md5_d77d5e503ad1439f585ac494268b351b = get_db()
    md5_d77d5e503ad1439f585ac494268b351b.execute('SELECT id, adresse_web FROM adresse')
    md5_4bef6bece607e237b5027b6d01a242aa = md5_d77d5e503ad1439f585ac494268b351b.fetchall()
    if not session.get('user') or not session.get('user')[2]:
        return redirect(url_for('login'))
    return render_template('admin.html', user=session['user'], md5_4bef6bece607e237b5027b6d01a242aa=md5_4bef6bece607e237b5027b6d01a242aa)

@app.route('/admin/add/',methods=['GET', 'POST'])
def admin_add() :
    if not session.get('user') or not session.get('user')[2]:
        return redirect(url_for('login'))

    if request.method == 'POST':
        page = str(request.form.get('Page'))
        md5_d77d5e503ad1439f585ac494268b351b = get_db()
        md5_d77d5e503ad1439f585ac494268b351b.execute('INSERT INTO adresse (adresse_web) VALUES (%(page)s)', {'page': page})
        commit()
        return redirect(url_for('admin'))

    return render_template('admin_add.html')


@app.route('/admin/editer/<int:id>', methods=['GET', 'POST'])
def editer(id):

    if not session.get('user') or not session.get('user')[2]:
        return redirect(url_for('login'))
    md5_d77d5e503ad1439f585ac494268b351b = get_db()

    if request.method == 'POST':
        page = str(request.form.get('Page'))
        md5_d77d5e503ad1439f585ac494268b351b.execute('UPDATE adresse SET adresse_web = %(page)s WHERE id = %(id)s', {'page': page,'id': id})
        commit()
        return redirect(url_for('admin'))

    else:
        md5_d77d5e503ad1439f585ac494268b351b.execute('SELECT id, adresse_web FROM adresse WHERE id = %(id)s', {'id': id})
        md5_4bef6bece607e237b5027b6d01a242aa = md5_d77d5e503ad1439f585ac494268b351b.fetchone()
        return render_template('admin_edit.html', user=session['user'], md5_4bef6bece607e237b5027b6d01a242aa=md5_4bef6bece607e237b5027b6d01a242aa)


@app.route('/admin/supprimer/<int:id>', methods=['GET', 'POST'])
def supprimer(id):
    if not session.get('user') or not session.get('user')[2]:
        return redirect(url_for('login'))

    md5_d77d5e503ad1439f585ac494268b351b = get_db()
    if request.method == 'POST':
        md5_d77d5e503ad1439f585ac494268b351b.execute('DELETE FROM adresse WHERE id = %(id)s', {'id': id})
        commit()
        return redirect(url_for('admin'))

    else:
        md5_d77d5e503ad1439f585ac494268b351b.execute('SELECT id, adresse_web FROM adresse WHERE id = %(id)s', {'id': id})
        md5_4bef6bece607e237b5027b6d01a242aa = md5_d77d5e503ad1439f585ac494268b351b.fetchone()
        return render_template('admin_sup.html', user=session['user'], md5_4bef6bece607e237b5027b6d01a242aa=md5_4bef6bece607e237b5027b6d01a242aa)

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



