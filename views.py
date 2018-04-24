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
    return render_template('home.html')


@app.route('/add')
def addItem():
    return render_template('addItem.html')


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
