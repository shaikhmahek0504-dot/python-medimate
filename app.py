from flask import Flask, render_template, request, redirect, url_for, flash, session
import json
import os
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'super_secret_health_key_for_flash'

DATA_FILE = 'reminders.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"medicines": [], "appointments": [], "completed": [], "tips": [], "users": []}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        data = load_data()
        users = data.get('users', [])
        
        # Check against hardcoded admin OR registered users
        user_exists = next((u for u in users if u['email'] == email and u['password'] == password), None)
        
        if (email == 'admin@example.com' and password == '1234') or user_exists:
            session['user'] = email
            flash("Logged in successfully!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid Email or Password", "error")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully!", "success")
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        data = load_data()
        if 'users' not in data:
            data['users'] = []
            
        # Check if email already exists
        if any(u['email'] == email for u in data['users']):
            flash("Email already registered. Please log in.", "error")
            return redirect(url_for('register'))
            
        data['users'].append({"email": email, "password": password})
        save_data(data)
        
        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    data = load_data()
    # Filter for active only
    active_medicines = [m for m in data.get('medicines', []) if not m.get('completed')]
    active_appointments = [a for a in data.get('appointments', []) if not a.get('completed')]
    completed_tasks = data.get('completed', [])
    
    tips = data.get('tips', ["Drink water!", "Take a walk."])
    daily_tip = random.choice(tips)

    return render_template('index.html', 
                           medicines=active_medicines, 
                           appointments=active_appointments,
                           completed=completed_tasks[-5:], # show last 5
                           daily_tip=daily_tip)

@app.route('/add_medicine', methods=['GET', 'POST'])
def add_medicine():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        time = request.form.get('time')
        frequency = request.form.get('frequency')
        
        data = load_data()
        new_id = len(data.get('medicines', [])) + 1
        data['medicines'].append({
            "id": f"med_{new_id}",
            "name": name,
            "time": time,
            "frequency": frequency,
            "completed": False
        })
        save_data(data)
        flash("Medicine reminder added successfully!")
        return redirect(url_for('dashboard'))
        
    return render_template('add_medicine.html')

@app.route('/add_appointment', methods=['GET', 'POST'])
def add_appointment():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        doctor = request.form.get('doctor')
        date = request.form.get('date')
        time = request.form.get('time')
        location = request.form.get('location')
        
        data = load_data()
        new_id = len(data.get('appointments', [])) + 1
        data['appointments'].append({
            "id": f"apt_{new_id}",
            "doctor": doctor,
            "date": date,
            "time": time,
            "location": location,
            "completed": False
        })
        save_data(data)
        flash("Appointment added successfully!")
        return redirect(url_for('dashboard'))
        
    return render_template('add_appointment.html')

@app.route('/complete/<type>/<id>')
def complete_task(type, id):
    if 'user' not in session:
        return redirect(url_for('login'))
        
    data = load_data()
    
    task_name = ""
    # Find and remove from active list, then add to completed
    if type == "medicine":
        for m in data['medicines']:
            if m['id'] == id:
                m['completed'] = True
                task_name = f"Medicine: {m['name']}"
                break
    elif type == "appointment":
        for a in data['appointments']:
            if a['id'] == id:
                a['completed'] = True
                task_name = f"Appointment: Dr. {a['doctor']}"
                break
                
    if task_name:
        data['completed'].append({
            "name": task_name,
            "time_completed": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_data(data)
        flash("Task marked as completed!")
    
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
