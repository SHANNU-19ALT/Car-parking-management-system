from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import heapq  # Min Heap

app = Flask(_name_)
app.config['SECRET_KEY'] = 'your_secret_key'  # Flash messages

# ✅ MySQL Database Configuration
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'root'
MYSQL_DB = 'flaskdb'

# ✅ Establish MySQL Connection
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB
        )
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# ✅ Initialize Min Heap for available slots
def initialize_min_heap():
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)
    
    # Fetch occupied slots
    cursor.execute("SELECT slot FROM parking WHERE isVacated = 1")
    occupied_slots = {row["slot"] for row in cursor.fetchall()}
    
    # Create a Min Heap with available slots (1 to 100)
    min_heap = [slot for slot in range(1, 101) if slot not in occupied_slots]
    heapq.heapify(min_heap)

    conn.close()
    return min_heap

# ✅ Global Min Heap
min_heap = initialize_min_heap()

# ✅ Check-In Route
@app.route("/checkin", methods=["GET", "POST"])
def checkin():
    global min_heap

    if request.method == "POST":
        car_number = request.form["car_number"]
        conn = get_db_connection()
        if not conn:
            flash("Database connection failed!", "danger")
            return redirect(url_for("checkin"))

        cursor = conn.cursor(dictionary=True)

        # Check if car is already checked in
        cursor.execute("SELECT * FROM parking WHERE car_number = %s AND isVacated = 1", (car_number,))
        existing_entry = cursor.fetchone()

        if existing_entry:
            flash("Car is already checked in!", "warning")
        else:
            # Get the nearest available slot from the Min Heap
            if min_heap:
                slot = heapq.heappop(min_heap)  # Extract the nearest slot
                cursor.execute("INSERT INTO parking (car_number, slot, in_time, isVacated) VALUES (%s, %s, %s, %s)",
                               (car_number, slot, datetime.now(), 0))
                conn.commit()
                flash(f"Car {car_number} checked in at slot {slot}!", "success")
            else:
                flash("No available parking slots!", "danger")

        conn.close()
        return redirect(url_for("checkin"))

    return render_template("checkin.html")

# ✅ Check-Out Route
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    global min_heap

    if request.method == "POST":
        car_number = request.form["car_number"]
        conn = get_db_connection()
        if not conn:
            flash("Database connection failed!", "danger")
            return redirect(url_for("checkout"))

        cursor = conn.cursor(dictionary=True)

        # Find the car record
        cursor.execute("SELECT slot FROM parking WHERE car_number = %s AND isVacated = 0", (car_number,))
        car = cursor.fetchone()

        if not car:
            flash("Car not found or already checked out!", "warning")
        else:
            slot = car["slot"]
            cursor.execute("UPDATE parking SET isVacated = 1 WHERE car_number = %s", (car_number,))
            conn.commit()

            # Push the slot back into the Min Heap
            heapq.heappush(min_heap, slot)

            flash(f"Car {car_number} checked out successfully!", "success")

        conn.close()
        return redirect(url_for("checkout"))

    return render_template("checkout.html")

# ✅ Run Flask App
if _name_ == "_main_":
    min_heap = initialize_min_heap()  # Initialize Heap on Startup
    app.run(debug=True)
