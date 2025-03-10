from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Used for flash messages

# ✅ MySQL Database Connection
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",  # Change if using another user
            password="root",  # Update with your MySQL password
            database="flaskdb"
        )
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# ✅ Find the nearest available parking slot
def get_nearest_slot():
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT slot FROM parking WHERE isVacated = 0")
    occupied_slots = {row["slot"] for row in cursor.fetchall()}
    conn.close()

    for slot in range(1, 101):  # Assuming 100 slots
        if slot not in occupied_slots:
            return slot
    return None  # No available slot

# ✅ Check-In Route
@app.route("/checkin", methods=["GET", "POST"])
def checkin():
    if request.method == "POST":
        car_number = request.form["car_number"]
        conn = get_db_connection()
        if not conn:
            flash("Database connection failed!", "danger")
            return redirect(url_for("checkin"))

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM parking WHERE car_number = %s AND isVacated = 0", (car_number,))
        existing_entry = cursor.fetchone()

        if existing_entry:
            flash("Car is already checked in!", "warning")
        else:
            slot = get_nearest_slot()
            if slot is None:
                flash("No available parking slots!", "danger")
            else:
                cursor.execute("INSERT INTO parking (car_number, slot, in_time, isVacated) VALUES (%s, %s, %s, %s)",
                               (car_number, slot, datetime.now(), 0))
                conn.commit()
                flash(f"Car {car_number} checked in at slot {slot}!", "success")

        conn.close()
        return redirect(url_for("checkin"))

    return render_template("checkin.html")

# ✅ Check-Out Route
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if request.method == "POST":
        car_number = request.form["car_number"]
        conn = get_db_connection()
        if not conn:
            flash("Database connection failed!", "danger")
            return redirect(url_for("checkout"))

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM parking WHERE car_number = %s AND isVacated = 0", (car_number,))
        car = cursor.fetchone()

        if not car:
            flash("Car not found or already checked out!", "warning")
        else:
            cursor.execute("UPDATE parking SET isVacated = 1 WHERE car_number = %s", (car_number,))
            conn.commit()
            flash(f"Car {car_number} checked out successfully!", "success")

        conn.close()
        return redirect(url_for("checkout"))

    return render_template("checkout.html")

# ✅ Run Flask App
if __name__ == "__main__":
    app.run(debug=True)
