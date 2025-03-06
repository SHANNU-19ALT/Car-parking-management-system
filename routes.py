def find_nearest_slot():
    available_slots = ParkingSlot.query.filter_by(status='available').all()
    slots = [slot.id for slot in available_slots]

    if not slots:
        return None  # No slots available

    slots.sort()
    return slots[len(slots) // 2]  # Allocate the middle slot for balance

from flask import request, jsonify, render_template
import qrcode
import io
import base64
from app import app, db
from models import User, ParkingSlot, Booking

@app.route('/book_slot', methods=['POST'])
def book_slot():
    data = request.json
    user = User.query.filter_by(vehicle_number=data['vehicle_number']).first()

    if not user:
        user = User(name=data['name'], vehicle_number=data['vehicle_number'])
        db.session.add(user)
        db.session.commit()

    slot_id = find_nearest_slot()
    if not slot_id:
        return jsonify({'message': 'No available slots'}), 400

    qr = qrcode.make(f"User: {user.id}, Slot: {slot_id}")
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_code_data = base64.b64encode(buffer.getvalue()).decode()

    booking = Booking(user_id=user.id, slot_id=slot_id, qr_code=qr_code_data)
    db.session.add(booking)

    slot = ParkingSlot.query.get(slot_id)
    slot.status = 'occupied'
    slot.allocated_to = user.id
    db.session.commit()

    return render_template('confirm.html', qr_code=qr_code_data)

@app.route('/exit_parking', methods=['POST'])
def exit_parking():
    data = request.json
    user = User.query.filter_by(vehicle_number=data['vehicle_number']).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    booking = Booking.query.filter_by(user_id=user.id).first()
    if not booking:
        return jsonify({'message': 'No active booking'}), 400

    slot = ParkingSlot.query.get(booking.slot_id)
    slot.status = 'available'
    slot.allocated_to = None
    db.session.commit()

    return jsonify({'message': 'Slot released successfully'})
