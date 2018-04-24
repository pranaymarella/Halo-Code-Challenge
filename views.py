import json
import string
import random
import os
import httplib2
import requests

# Flask Imports
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask import abort, g, flash, Response, make_response
from flask import session as login_session
from flask_httpauth import HTTPBasicAuth

# SQLAlchemy imports
from models import Items, Users, Base
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import desc

auth = HTTPBasicAuth()

engine = create_engine('sqlite:///items.db')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
db = DBSession()
app = Flask(__name__)


def redirect_url(default='/'):
    return request.args.get('next') or request.referrer or url_for(default)


##################
# VIEWS
##################
@app.route('/')
def index():
    items = db.query(Items).all()
    return render_template('home.html',
                            items=items)


@app.route('/add', methods=['GET', 'POST'])
def addItem():
    if request.method == 'GET':
        return render_template('addItem.html')
    elif request.method == 'POST':
        key = request.form.get('key')
        value = request.form.get('value')

        if key is not None and key != '':
            item = Items(key=key)
            if value is not None and value != '':
                item.value = value
        else:
            flash('You need to provide a proper Key/Value pair')
            return redirect(url_for('add'))

        db.add(item)
        db.commit()
        flash('Item Added!')
        return redirect(url_for('index'))


@app.route('/edit')
def editItem():
    return render_template('editItem.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/signup')
def signup():
    return render_template('signup.html')


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=3000)
