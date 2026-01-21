from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Secret key for sessions

# DB connection helper
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # Return rows as dicts
    return conn

# Auth check helpers
def is_authenticated():
    return 'user_id' in session

def is_admin():
    return is_authenticated() and session.get('role') == 'admin'

def is_user():
    return is_authenticated() and session.get('role') == 'user'

@app.route('/')
def hello_world():
    return render_template('hello.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            return render_template('formulaire_authentification.html', error=True)
    return render_template('formulaire_authentification.html', error=False)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('hello_world'))

@app.route('/dashboard')
def dashboard():
    if not is_authenticated():
        return redirect(url_for('login'))
    return f"<h2>Welcome, {session['role'].capitalize()}! <a href='/logout'>Logout</a></h2>"

# User Management (Admin only)
@app.route('/users', methods=['GET'])
def list_users():
    if not is_admin():
        return "Access denied", 403
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return render_template('read_data.html', data=users, title='Users')

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if not is_admin():
        return "Access denied", 403
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        conn = get_db_connection()
        conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, password, role))
        conn.commit()
        conn.close()
        return redirect(url_for('list_users'))
    return render_template('add_user.html')  # Create this template (see below)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not is_admin():
        return "Access denied", 403
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('list_users'))

# Book Management (Admin only)
@app.route('/books', methods=['GET'])
def list_books():
    if not is_authenticated():
        return redirect(url_for('login'))
    conn = get_db_connection()
    books = conn.execute('SELECT * FROM books').fetchall()
    conn.close()
    return render_template('read_data.html', data=books, title='Books')

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if not is_admin():
        return "Access denied", 403
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        conn = get_db_connection()
        conn.execute('INSERT INTO books (title, author) VALUES (?, ?)', (title, author))
        conn.commit()
        conn.close()
        return redirect(url_for('list_books'))
    return render_template('add_book.html')  # Create this template (see below)

@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if not is_admin():
        return "Access denied", 403
    conn = get_db_connection()
    conn.execute('DELETE FROM books WHERE id = ?', (book_id,))
    conn.execute('DELETE FROM borrowings WHERE book_id = ?', (book_id,))  # Clean up borrowings
    conn.commit()
    conn.close()
    return redirect(url_for('list_books'))

# Search Available Books (User or Admin)
@app.route('/search_books', methods=['GET', 'POST'])
def search_books():
    if not is_authenticated():
        return redirect(url_for('login'))
    search_term = request.form.get('search_term', '') if request.method == 'POST' else ''
    conn = get_db_connection()
    books = conn.execute('SELECT * FROM books WHERE available = 1 AND (title LIKE ? OR author LIKE ?)', (f'%{search_term}%', f'%{search_term}%')).fetchall()
    conn.close()
    return render_template('search_books.html', books=books, search_term=search_term)  # Create this template (see below)

# Borrow Book (User only)
@app.route('/borrow_book/<int:book_id>', methods=['POST'])
def borrow_book(book_id):
    if not is_user():
        return "Access denied", 403
    conn = get_db_connection()
    book = conn.execute('SELECT * FROM books WHERE id = ? AND available = 1', (book_id,)).fetchone()
    if book:
        conn.execute('INSERT INTO borrowings (user_id, book_id) VALUES (?, ?)', (session['user_id'], book_id))
        conn.execute('UPDATE books SET available = 0 WHERE id = ?', (book_id,))
        conn.commit()
    conn.close()
    return redirect(url_for('search_books'))

# Optional: Return Book (Admin only, for simplicity)
@app.route('/return_book/<int:borrowing_id>', methods=['POST'])
def return_book(borrowing_id):
    if not is_admin():
        return "Access denied", 403
    conn = get_db_connection()
    borrowing = conn.execute('SELECT * FROM borrowings WHERE id = ? AND return_date IS NULL', (borrowing_id,)).fetchone()
    if borrowing:
        conn.execute('UPDATE borrowings SET return_date = CURRENT_TIMESTAMP WHERE id = ?', (borrowing_id,))
        conn.execute('UPDATE books SET available = 1 WHERE id = ?', (borrowing['book_id'],))
        conn.commit()
    conn.close()
    return redirect(url_for('list_books'))  # Or a borrowings list page

if __name__ == "__main__":
    app.run(debug=True)
