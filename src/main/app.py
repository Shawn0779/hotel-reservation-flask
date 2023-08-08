from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import and_, or_

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reservations.db'
db = SQLAlchemy(app)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(10), unique=True, nullable=False)
    # Add more fields as needed

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    guest_name = db.Column(db.String(100), nullable=False)
    room = db.relationship('Room', backref=db.backref('reservations', lazy=True))

@app.route('/api/reservations', methods=['POST'])
def create_reservation():
    try:
        data = request.json

        # Validate incoming data
        required_fields = ['room_id', 'check_in_date', 'check_out_date', 'guest_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing {field} field'}), 400

        room = Room.query.get(data['room_id'])
        if not room:
            return jsonify({'error': 'Room not found'}), 404

        check_in_date = datetime.strptime(data['check_in_date'], '%Y-%m-%d').date()
        check_out_date = datetime.strptime(data['check_out_date'], '%Y-%m-%d').date()

        # Check room availability
        conflicting_reservation = Reservation.query.filter(
            and_(Reservation.room_id == data['room_id'],
                 or_(
                     and_(Reservation.check_in_date <= check_out_date, Reservation.check_out_date >= check_in_date),
                     and_(Reservation.check_in_date >= check_in_date, Reservation.check_in_date <= check_out_date)
                 )
            )
        ).first()

        if conflicting_reservation:
            return jsonify({'error': 'Room is already booked for the requested dates'}), 409

        # Create and store reservation
        new_reservation = Reservation(
            room_id=data['room_id'],
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            guest_name=data['guest_name']
        )

        db.session.add(new_reservation)
        db.session.commit()

        return jsonify({'message': 'Reservation created successfully'}), 201
    except Exception as e:
        print('Error creating reservation:', e)
        db.session.rollback()
        return jsonify({'error': 'An error occurred'}), 500

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)