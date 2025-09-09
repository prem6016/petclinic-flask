from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this in production

DB_NAME = 'pet_clinic.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        # Visits table
        c.execute('''
            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pet_name TEXT NOT NULL,
                species TEXT NOT NULL,
                visit_date TEXT NOT NULL,
                reason TEXT NOT NULL,
                owner_name TEXT NOT NULL,
                owner_contact TEXT NOT NULL
            )
        ''')
        # Users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        # Create default user if not exists
        c.execute('SELECT * FROM users WHERE username = ?', ('admin',))
        if not c.fetchone():
            hashed = generate_password_hash('password123', method='pbkdf2:sha256')
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('admin', hashed))
        conn.commit()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def is_logged_in():
    return 'user_id' in session

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = c.fetchone()
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if not is_logged_in():
        return redirect(url_for('login'))

    query = "SELECT * FROM visits"
    params = []
    if request.method == 'POST':
        pet_name = request.form.get('pet_name')
        visit_date = request.form.get('visit_date')
        conditions = []
        if pet_name:
            conditions.append("pet_name LIKE ?")
            params.append(f"%{pet_name}%")
        if visit_date:
            conditions.append("visit_date = ?")
            params.append(visit_date)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(query, params)
        visits = c.fetchall()
    return render_template('index.html', visits=visits)

@app.route('/add', methods=['GET', 'POST'])
def add_visit():
    if not is_logged_in():
        return redirect(url_for('login'))
    if request.method == 'POST':
        pet_name = request.form['pet_name']
        species = request.form['species']
        visit_date = request.form['visit_date']
        reason = request.form['reason']
        owner_name = request.form['owner_name']
        owner_contact = request.form['owner_contact']
        
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO visits (pet_name, species, visit_date, reason, owner_name, owner_contact)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (pet_name, species, visit_date, reason, owner_name, owner_contact))
            conn.commit()
        return redirect(url_for('index'))
    return render_template('add_visit.html')

@app.route('/edit/<int:visit_id>', methods=['GET', 'POST'])
def edit_visit(visit_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    with get_db_connection() as conn:
        c = conn.cursor()
        if request.method == 'POST':
            pet_name = request.form['pet_name']
            species = request.form['species']
            visit_date = request.form['visit_date']
            reason = request.form['reason']
            owner_name = request.form['owner_name']
            owner_contact = request.form['owner_contact']
            c.execute('''
                UPDATE visits
                SET pet_name = ?, species = ?, visit_date = ?, reason = ?, owner_name = ?, owner_contact = ?
                WHERE id = ?
            ''', (pet_name, species, visit_date, reason, owner_name, owner_contact, visit_id))
            conn.commit()
            return redirect(url_for('index'))
        else:
            c.execute('SELECT * FROM visits WHERE id = ?', (visit_id,))
            visit = c.fetchone()
            if not visit:
                return "Visit not found", 404
    return render_template('edit_visit.html', visit=visit)

@app.route('/delete/<int:visit_id>')
def delete_visit(visit_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('DELETE FROM visits WHERE id = ?', (visit_id,))
        conn.commit()
    return redirect(url_for('index'))

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0")
