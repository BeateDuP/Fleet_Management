from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models import db, User, Vehicle, Booking  # import models and db

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fleet.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your_secret_key_here'  # Required for session & flash

    db.init_app(app)  # initialize SQLAlchemy with app

    # -------------------- LOGIN --------------------
    @app.route('/', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = User.query.filter_by(username=username, password=password).first()
            if user:
                session['username'] = username
                session['is_admin'] = user.is_admin
                return redirect(url_for('admin_dashboard') if user.is_admin else url_for('dashboard'))
            else:
                flash("Invalid username or password.")
                return redirect(url_for('login'))
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    # -------------------- REGISTER --------------------
    @app.route('/register', methods=['GET', 'POST'])
    def register_user():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            if User.query.filter_by(username=username).first():
                flash("Username already exists.")
                return redirect(url_for('register_user'))
            new_user = User(username=username, password=password, is_admin=False)
            db.session.add(new_user)
            db.session.commit()
            flash("Account created successfully! Please log in.")
            return redirect(url_for('login'))
        return render_template('register.html')

    # -------------------- USER DASHBOARD --------------------
    @app.route('/dashboard')
    def dashboard():
        if 'username' not in session or session.get('is_admin'):
            return redirect(url_for('login'))
        user_bookings = Booking.query.filter_by(username=session['username']).all()
        return render_template('dashboard.html', username=session['username'], bookings=user_bookings)

    # -------------------- SCHEDULE --------------------
    @app.route('/schedule', methods=['GET', 'POST'])
    def schedule():
        if 'username' not in session or session.get('is_admin'):
            return redirect(url_for('login'))
        if request.method == 'POST':
            session['start_time'] = request.form.get('start_time')
            session['end_time'] = request.form.get('end_time')
            return redirect(url_for('available_vehicles'))
        return render_template('schedule.html')

    # -------------------- AVAILABLE VEHICLES --------------------
    @app.route('/available', methods=['GET', 'POST'])
    def available_vehicles():
        if 'username' not in session or session.get('is_admin'):
            return redirect(url_for('login'))

        start_time = datetime.fromisoformat(session['start_time'])
        end_time = datetime.fromisoformat(session['end_time'])

        all_vehicles = Vehicle.query.filter_by(active=True).all()
        available = []
        for v in all_vehicles:
            conflict = Booking.query.filter(
                Booking.vehicle_id == v.id,
                Booking.status == 'Approved',
                Booking.start_time < end_time,
                Booking.end_time > start_time,
                Booking.returned == False
            ).first()
            if not conflict:
                available.append(v)

        if request.method == 'POST':
            vehicle_id = int(request.form.get('vehicle'))
            booking = Booking(
                vehicle_id=vehicle_id,
                start_time=start_time,
                end_time=end_time,
                username=session['username'],
                status='Pending'
            )
            db.session.add(booking)
            db.session.commit()
            flash("Booking request submitted!")
            return redirect(url_for('dashboard'))

        return render_template('available.html', vehicles=available)

    # -------------------- ADMIN DASHBOARD --------------------
    @app.route('/admin', methods=['GET', 'POST'])
    def admin_dashboard():
        if 'username' not in session or not session.get('is_admin'):
            return redirect(url_for('login'))

        pending_bookings = Booking.query.filter_by(status='Pending').all()

        if request.method == 'POST':
            booking_id = int(request.form.get('booking_id'))
            action = request.form.get('action')
            booking = Booking.query.get(booking_id)
            booking.status = action
            db.session.commit()
            flash(f"Booking {action.lower()}!")
            return redirect(url_for('admin_dashboard'))

        return render_template('admin.html', bookings=pending_bookings)

    # -------------------- APPROVED BOOKINGS (ADMIN) --------------------
    @app.route('/approved', methods=['GET', 'POST'])
    def approved_bookings():
        if 'username' not in session or not session.get('is_admin'):
            return redirect(url_for('login'))

        bookings = Booking.query.filter_by(status='Approved', returned=False).all()

        if request.method == 'POST':
            booking_id = int(request.form.get('booking_id'))
            action = request.form.get('action')
            booking = Booking.query.get(booking_id)

            if action == 'collected':
                booking.collected = True
            elif action == 'returned':
                booking.returned = True
            db.session.commit()
            return redirect(url_for('approved_bookings'))

        return render_template('approved.html', bookings=bookings)

    # -------------------- BOOKING HISTORY (ADMIN) --------------------
    @app.route('/booking_history', methods=['GET'])
    def booking_history():
        if 'username' not in session or not session.get('is_admin'):
            return redirect(url_for('login'))

        bookings = Booking.query.filter_by(returned=True).all()
        return render_template('booking_history.html', bookings=bookings)

    # -------------------- VEHICLE MANAGEMENT --------------------
    @app.route('/vehicles', methods=['GET', 'POST'])
    def manage_vehicles():
        if 'username' not in session or not session.get('is_admin'):
            return redirect(url_for('login'))

        if request.method == 'POST':
            if request.form.get('name'):
                name = request.form.get('name')
                db.session.add(Vehicle(name=name, active=True))
                db.session.commit()
                flash(f"Vehicle '{name}' added successfully!")
                return redirect(url_for('manage_vehicles'))

            action = request.form.get('action')
            vehicle_id = int(request.form.get('vehicle_id'))
            vehicle = Vehicle.query.get(vehicle_id)

            if action == 'delete':
                db.session.delete(vehicle)
                db.session.commit()
                flash(f"Vehicle '{vehicle.name}' permanently deleted!")
            elif action == 'disable':
                vehicle.active = False
                db.session.commit()
                flash(f"Vehicle '{vehicle.name}' temporarily disabled!")
            elif action == 'enable':
                vehicle.active = True
                db.session.commit()
                flash(f"Vehicle '{vehicle.name}' re-enabled!")

            return redirect(url_for('manage_vehicles'))

        vehicles = Vehicle.query.all()
        return render_template('vehicles.html', vehicles=vehicles)
    
    return app


# ======================== RUN APP ========================
if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)
