import logging
import sqlite3
import string

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
from string import Template
from datetime import date, datetime

# variable to count the total querys to database
total_querys = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    global total_querys
    total_querys += 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    if post != None:
        custom_logger(logging.DEBUG, 'Article "' + post['title'] + '" retrieved!')
    return post

# Function to get all records in the posts table
def count_posts():
    connection = get_db_connection()
    total_posts = connection.execute('SELECT COUNT(*) as total_posts FROM posts').fetchone()
    connection.close()
    total_posts = total_posts['total_posts']
    return total_posts

def custom_logger(log_level, message):
    dt = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    msg = dt + ', ' + message
    logging.log(log_level, msg)

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        custom_logger(logging.ERROR, 'Article not found.')
        return render_template('404.html'), 404
    else:
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    custom_logger(logging.INFO, 'Page "About Us" retrieved.')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            custom_logger(logging.INFO, 'The new article titled "' + title + '" was created!.')
            return redirect(url_for('index'))

    return render_template('create.html')

@app.route("/healthz")
def healthz():
    healthcheck = app.response_class(
        response = json.dumps({"result":"OK - healthy"}),
        status = 200,
        mimetype = 'application/json'
    )
    return healthcheck

@app.route("/metrics")
def metrics():
    posts = count_posts()
    template = Template('{"db_connection_count": "${db_conns}", "post_count": "${posts}"}').substitute(db_conns = total_querys, posts = posts)
    resp = app.response_class(
        response = json.dumps(template, indent=4),
        status = 200,
        mimetype = 'application/json'
    )
    return resp

# start the application on port 3111
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app.run(host='0.0.0.0', port='3111')
