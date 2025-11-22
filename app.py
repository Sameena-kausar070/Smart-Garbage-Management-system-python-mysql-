from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="test",
    database="smart_garbage"
)
cursor = db.cursor(dictionary=True)

# ---------------------- HOME PAGE ----------------------
@app.route('/')
def home():
    return render_template('index.html')

# ---------------------- USER ROUTES ----------------------
@app.route('/user-register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
                       (username, email, password))
        db.commit()
        return redirect('/user-login')
    return render_template('user_register.html')

@app.route('/user-login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", 
                       (username, password))
        user = cursor.fetchone()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('user_dashboard', user_id=user['id']))
        else:
            return "Invalid credentials, please try again."
    return render_template('user_login.html')

@app.route('/user-dashboard/<int:user_id>')
def user_dashboard(user_id):
    if 'user_id' not in session or session['user_id'] != user_id:
        return redirect('/user-login')
    cursor.execute("SELECT * FROM bins")
    bins = cursor.fetchall()
    return render_template('user_dashboard.html', bins=bins, username=session['username'])

@app.route('/request-pickup', methods=['POST'])
def request_pickup():
    if 'user_id' not in session:
        return redirect('/user-login')
    bin_location = request.form['bin_location']
    cursor.execute("INSERT INTO pickup_requests (location) VALUES (%s)", (bin_location,))
    db.commit()
    return redirect(url_for('user_dashboard', user_id=session['user_id']))

# ---------------------- ADMIN ROUTES ----------------------
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute("SELECT * FROM admins WHERE username = %s AND password = %s", 
                       (username, password))
        admin = cursor.fetchone()
        if admin:
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
            return redirect('/admin-dashboard')
        else:
            return "Invalid admin credentials."
    return render_template('admin_login.html')

@app.route('/admin-dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect('/admin-login')
    cursor.execute("SELECT * FROM bins")
    bins = cursor.fetchall()
    cursor.execute("SELECT * FROM pickup_requests")
    requests = cursor.fetchall()
    return render_template('admin_dashboard.html', bins=bins, requests=requests, admin=session['admin_username'])

@app.route('/admin-logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    return redirect('/')

@app.route('/user-logout')
def user_logout():
    session.pop('user_id', None)
    session.pop('user_username', None)
    return redirect('/')

@app.route('/driver-logout')
def driver_logout():
    session.pop('driver_id', None)
    session.pop('driver_username', None)
    return redirect('/')


# ---------------------- DRIVER ROUTES ----------------------
@app.route('/driver-login', methods=['GET', 'POST'])
def driver_login():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        cursor.execute("SELECT * FROM drivers WHERE username = %s AND password = %s", 
                       (username, password))
        driver = cursor.fetchone()
        if driver:
            session['driver_id'] = driver['id']
            session['driver_username'] = driver['username']
            return redirect('/driver-dashboard')
        else:
            return "Invalid driver credentials."
    return render_template('driver_login.html')

@app.route('/driver-dashboard')
def driver_dashboard():
    if 'driver_id' not in session:
        return redirect('/driver-login')
    cursor.execute("SELECT * FROM bins WHERE status = 'Full'")
    assigned_bins = cursor.fetchall()
    return render_template('driver_dashboard.html', assigned_bins=assigned_bins, driver=session['driver_username'])

@app.route('/mark-bin-empty', methods=['POST'])
def mark_bin_empty():
    if 'driver_id' not in session:
        return redirect('/driver-login')
    bin_id = request.form['bin_id']
    cursor.execute("UPDATE bins SET status = 'Empty' WHERE id = %s", (bin_id,))
    db.commit()
    return redirect('/driver-dashboard')
@app.route('/add-bin', methods=['GET', 'POST'])
def add_bin():
    if 'admin_id' not in session:
        return redirect('/admin-login')
    if request.method == 'POST':
        location = request.form['location']
        status = request.form['status']
        cursor.execute("INSERT INTO bins (location, status) VALUES (%s, %s)", (location, status))
        db.commit()
        return redirect('/admin-dashboard')
    return render_template('add_bin.html')

@app.route('/assign-bin', methods=['GET', 'POST'])
def assign_bin():
    if 'admin_id' not in session:
        return redirect('/admin-login')
    if request.method == 'POST':
        driver_id = request.form['driver_id']
        bin_id = request.form['bin_id']
        cursor.execute("INSERT INTO driver_assignments (driver_id, bin_id) VALUES (%s, %s)", (driver_id, bin_id))
        db.commit()
        return redirect('/admin-dashboard')
    cursor.execute("SELECT * FROM bins WHERE status = 'Full'")
    bins = cursor.fetchall()
    cursor.execute("SELECT * FROM drivers")
    drivers = cursor.fetchall()
    return render_template('assign_bin.html', bins=bins, drivers=drivers)

@app.route('/update-bin', methods=['GET', 'POST'])
def update_bin():
    if 'admin_id' not in session:
        return redirect('/admin-login')
    if request.method == 'POST':
        bin_id = request.form['bin_id']
        new_status = request.form['status']
        cursor.execute("UPDATE bins SET status = %s WHERE id = %s", (new_status, bin_id))
        db.commit()
        return redirect('/admin-dashboard')
    cursor.execute("SELECT * FROM bins")
    bins = cursor.fetchall()
    return render_template('update_bin.html', bins=bins)

@app.route('/add-driver', methods=['GET', 'POST'])
def add_driver():
    if 'admin_id' not in session:
        return redirect('/admin-login')
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        cursor.execute("INSERT INTO drivers (name, username, password) VALUES (%s, %s, %s)", (name, username, password))
        db.commit()
        return redirect('/admin-dashboard')
    return render_template('add_driver.html')

@app.route('/update-driver', methods=['GET', 'POST'])
def update_driver():
    if 'admin_id' not in session:
        return redirect('/admin-login')
    if request.method == 'POST':
        driver_id = request.form['driver_id']
        new_name = request.form['name']
        cursor.execute("UPDATE drivers SET name = %s WHERE id = %s", (new_name, driver_id))
        db.commit()
        return redirect('/admin-dashboard')
    cursor.execute("SELECT * FROM drivers")
    drivers = cursor.fetchall()
    return render_template('update_driver.html', drivers=drivers)

@app.route('/delete-driver', methods=['GET', 'POST'])
def delete_driver():
    if 'admin_id' not in session:
        return redirect('/admin-login')
    if request.method == 'POST':
        driver_id = request.form['driver_id']
        cursor.execute("DELETE FROM drivers WHERE id = %s", (driver_id,))
        db.commit()
        return redirect('/admin-dashboard')
    cursor.execute("SELECT * FROM drivers")
    drivers = cursor.fetchall()
    return render_template('delete_driver.html', drivers=drivers)

@app.route('/manage-requests', methods=['GET', 'POST'])
def manage_requests():
    """Admin route to view and manage user requests."""
    if 'admin_id' not in session:
        return redirect('/admin-login')
    
    # Fetch pending requests
    cursor.execute("SELECT * FROM pickup_requests WHERE status = 'Pending'")
    pending_requests = cursor.fetchall()
    
    # Fetch approved/rejected requests for admin reference
    cursor.execute("SELECT * FROM pickup_requests WHERE status IN ('Approved', 'Rejected')")
    processed_requests = cursor.fetchall()
    
    return render_template('manage_requests.html', pending_requests=pending_requests, processed_requests=processed_requests)


@app.route('/approve-request/<int:request_id>')
def approve_request(request_id):
    """Admin approves a pickup request."""
    if 'admin_id' not in session:
        return redirect('/admin-login')
    
    cursor.execute("UPDATE pickup_requests SET status = 'Approved' WHERE id = %s", (request_id,))
    db.commit()
    return redirect('/manage-requests')


@app.route('/reject-request/<int:request_id>')
def reject_request(request_id):
    """Admin rejects a pickup request."""
    if 'admin_id' not in session:
        return redirect('/admin-login')
    
    cursor.execute("UPDATE pickup_requests SET status = 'Rejected' WHERE id = %s", (request_id,))
    db.commit()
    return redirect('/manage-requests')

# ---------------------- RUN APP ----------------------
if __name__ == '__main__':
    app.run(debug=True)
