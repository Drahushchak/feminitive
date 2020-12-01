from app import app, db
from flask import render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import *
from app.controller import *
from app.forms import *
from flask_login import login_user, login_required, current_user, logout_user
from werkzeug.datastructures import FileStorage

@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('home.html')  
    else: 
        return render_template('index.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        name_email = form.name_email.data
        password = form.password.data
        remember = form.remember.data
        user = User.query.filter((User.name==name_email) | (User.email==name_email)).first()
        # check if the user actually exists
        # take the user-supplied password, hash it, and compare it to the hashed password in the database
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('login')) # if the user doesn't exist or password is wrong, reload the page

        # if the above check passes, then we know the user has the right credentials
        login_user(user, remember=remember)
        flash('Logged in successful!', 'success')
        return redirect(url_for('profile'))
    return render_template('login.html', form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        user_name = User.query.filter(User.name==form.name.data).first()
        user_email = User.query.filter(User.name==form.name.data).first()
        if user_name or user_email:
            if user_name:
                flash(f'User with the username {user_name.name} already exists!', 'danger')
            elif user_email:
                flash(f'User with the email address {user_name.name} already exists!', 'danger')
            return render_template('signup.html', form=form)
        user = User(name=form.name.data, email=form.email.data,
                    password=generate_password_hash(form.password.data))
        db.session.add(user)
        db.session.commit()
        flash('Thanks for registering!', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET','POST'])
@login_required
def upload():
    file = FileStorage
    if 'file' not in request.files:
        flash('No file added', 'danger')
        return redirect(url_for('index'))
    file = request.files['file']
    if not file:
        flash('No file found', 'danger')
        return redirect(url_for('index'))
    if not file.filename:
        flash('No file name', 'danger')
        return redirect(url_for('index'))
    valid_file_format = get_valid_file_format(file.filename)
    if not bool(valid_file_format):
        flash('Invalid file format', 'danger')
        return redirect(url_for('index'))
    
    source_name = '.'.join(file.filename.split('.')[:-1])
    data = loads_file(file.stream, valid_file_format)
    if not is_valid_data(data):
        flash('Invalid data', 'danger')
        return redirect(url_for('index'))
    if not upsert_data(current_user, source_name, data):
        flash('Upload data error', 'danger')
        return redirect(url_for('index'))
    return redirect(url_for('index'))

@app.route('/source/delete', methods=['GET'])
@login_required
def source_delete():
    source_id = int(request.args.get('source_id', '0'))
    if not source_id:
        flash('No source_id is specified', 'danger')
        return redirect(url_for('index'))
    source = current_user.get_source(source_id)
    if not source:
        flash('The source was not found in your sources list', 'danger')
        return redirect(url_for('index'))
    db.session.delete(source)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    sources_ids = request.args.getlist('sources')
    if not sources_ids:
        flash('No sources were specified', 'danger')
        return redirect(url_for('index'))
    sources = list(filter(None, map(lambda source_id: current_user.get_source(int(source_id)), sources_ids)))
    if len(sources_ids)!=len(sources):
        flash('One or more sources are not in your sources list', 'danger')
        return redirect(url_for('index'))

    dashboard = generate_dashboard_data(sources)

    return render_template('dashboard.html', dashboard=dashboard)

@app.route('/service-worker.js')
def sw():
    print('hello')
    return app.send_static_file('service-worker.js')