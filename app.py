from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Function to create database and tables
def create_tables():
    conn = sqlite3.connect('bakery.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        username TEXT NOT NULL,
                        password TEXT NOT NULL
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        item TEXT NOT NULL,
                        quantity INTEGER NOT NULL
                    )''')
    conn.commit()
    conn.close()

# Function to check if user is logged in
def logged_in():
    return 'username' in session

# Home page
@app.route('/')
def home():
    return render_template('home.html')

# Registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        try:
            # Use context manager to handle connection
            with sqlite3.connect('bakery.db') as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
                conn.commit()
                
                # Fetch user_id for session
                cursor.execute('SELECT id FROM users WHERE username=?', (username,))
                user = cursor.fetchone()
                session['username'] = username
                session['user_id'] = user[0]
                
                return redirect(url_for('home'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error='Username already exists')
        except sqlite3.ProgrammingError as e:
            # Handle database programming error
            return render_template('register.html', error=f"Database error: {str(e)}")
    return render_template('register.html')

def logged_in():
    return 'username' in session

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('bakery.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['username'] = username
            session['user_id'] = user[0]
            return redirect(url_for('create_order'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

# Logout page
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('home'))

# Order creation page
@app.route('/create_order', methods=['GET', 'POST'])
def create_order():
    if not logged_in():
        return redirect(url_for('login'))
    if request.method == 'POST':
        item = request.form['item']
        quantity = int(request.form['quantity'])
        conn = sqlite3.connect('bakery.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO orders (user_id, item, quantity) VALUES (?, ?, ?)", 
                       (session['user_id'], item, quantity))
        conn.commit()
        conn.close()
        return redirect(url_for('order_history'))
    return render_template('create_order.html')

# Order history page
@app.route('/order_history')
def order_history():
    if not logged_in():
        return redirect(url_for('login'))
    conn = sqlite3.connect('bakery.db')
    cursor = conn.cursor()
    cursor.execute("SELECT item, quantity FROM orders WHERE user_id=?", (session['user_id'],))
    orders = cursor.fetchall()
    conn.close()
    return render_template('order_history.html', orders=orders)


if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
