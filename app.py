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


#############################
# User Login and Registration
############################


@auth.verify_password
def verify_password(username, password):
    user = db.query(Users).filter_by(username=username).first()
    if not user or not user.verify_password(password):
        return False
    g.user = user
    return True


def createUser(login_session):
    newUser = Users(username=login_session['username'])
    db.add(newUser)
    db.commit()
    user = db.query(Users).filter_by(username=login_session['username']).first()
    return user.id


def getUserInfo(user_id):
    user = db.query(Users).filter_by(id=user_id).first()
    return user


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html',
                                login_session=login_session)
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        verifyPass = request.form.get('verifyPassword')

        if username is None or password is None or password != verifyPass:
            flash('You must enter a valid username and password')
            return render_template('signup.html')

        # Check if user is already in database
        user = db.query(Users).filter_by(username=username).first()
        if user:
            flash('The user "%s" is already registered, please login to continue' % user.username)
            return render_template('signup.html')
        else:
            user = Users(username=username)
            user.hash_password(password)
            db.add(user)
            db.commit()
            flash('User %s has been created, please login to continue' % user.username)
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html',
                                login_session=login_session)
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if verify_password(username, password):
            user = db.query(Users).filter_by(username=username).first()
            login_session['username'] = user.username
            login_session['user_id'] = user.id
            flash("Welcome, %s" % user.username)
            g.user = user
            return redirect(url_for('index'))
        else:
            flash('Wrong Username or Password')
            return render_template('login.html')
    else:
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    del login_session['username']
    del login_session['user_id']
    flash('You have been logged out')
    return redirect(url_for('index'))


##################
# VIEWS
##################


@app.route('/')
def index():
    if ('username' in login_session):
        # Only show items added by this user
        items = db.query(Items).filter_by(author_id=login_session['user_id']).all()
        return render_template('home.html', items=items, login_session=login_session)
    else:
        # Don't show items when user is not logged in
        return render_template('home.html',
                                login_session=login_session)

# Method for Setting/Adding new Key Value Pairs
@app.route('/add', methods=['GET', 'POST'])
def addItem():
    if request.method == 'GET':
        # Make sure only logged in users can access this page
        if ('username' in login_session):
            return render_template('addItem.html',
                                    login_session=login_session)
        else:
            flash('Please login in order to add key/value pairs')
            return redirect(url_for('login'))
    elif request.method == 'POST':
        # Make sure only logged in users are adding key/value pairs
        if ('username' in login_session):
            key = request.form.get('key')
            value = request.form.get('value')

            item = db.query(Items).filter_by(key=key).first()

            # Make sure key is unique/not already added
            if item:
                flash('"%s" has already been added' % item.key)
                return redirect(url_for('addItem'))

            if key is not None and key != '':
                item = Items(key=key)
                if value is not None and value != '':
                    item.value = value
                item.author = getUserInfo(login_session['user_id'])
            else:
                flash('You need to provide a proper Key/Value pair')
                return redirect(url_for('addItem'))

            db.add(item)
            db.commit()
            flash('Item Added!')
            return redirect(url_for('index'))
        else:
            flash('Please login in order to add key/value pairs')
            return redirect(url_for('login'))
    else:
        return redirect(url_for('index'))


@app.route('/edit/<item_key>', methods=['GET', 'POST'])
def editItem(item_key):
    if request.method == 'GET':
        if ('username' in login_session):
            # find key/value pair that we want to edit
            item = db.query(Items).filter_by(key=item_key).first()

            # Make sure user is editing only their key/value pair
            if (item.author.username == login_session['username']):
                return render_template('editItem.html',
                                        item=item,
                                        login_session=login_session)
        else:
            flash('Please login to edit key/value pairs')
            return redirect(url_for('login'))
    elif request.method == 'POST':
        # Make sure only a logged in user is requesting edit
        if ('username' in login_session):
            key = request.form.get('key')
            value = request.form.get('value')

            item = db.query(Items).filter_by(key=item_key).first()

            # Make sure only user that added this item can edit this
            if (item.author_id != login_session['user_id']):
                flash('You are not allowed to edit this')
                return redirect(url_for('index'))

            # Update the Key/Value pair
            if key is not None and key != '':
                item.key = key
            if value is not None and value != '':
                item.value = value

            # Commit changes to the Database
            db.add(item)
            db.commit()
            flash('Key/value pair has been updated')
            return redirect(url_for('index'))
        else:
            flash('Please login to edit key/value pairs')
            return redirect(url_for('login'))
    else:
        return redirect(url_for('index'))


@app.route('/delete/<item_key>', methods=['GET', 'POST'])
def deleteItem(item_key):
    if request.method == 'GET':
        if ('username' in login_session):
            # find key/value pair that we want to edit
            item = db.query(Items).filter_by(key=item_key).first()

            # Make sure user is deleting only their key/value pair
            if (item.author.username == login_session['username']):
                return render_template('deleteItem.html',
                                        item=item,
                                        login_session=login_session)
        else:
            flash('Please login to delete key/value pairs')
            return redirect(url_for('login'))
    if request.method=='POST':
        item = db.query(Items).filter_by(key=item_key).first()

        # Make sure the right user is requesting the delete
        if login_session['username'] != item.author.username:
            flash('You do not have the permission to delete that')
            return redirect(url_for('index'))

        # Delete item and commit changes
        db.delete(item)
        db.commit()
        flash('Key/Value pair deleted')
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=3000)
