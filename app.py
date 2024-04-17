from datetime import timedelta
import logging
from flask import Flask, redirect, render_template, request, session, url_for
import random
import string
import hashlib
import secrets
import sqlite3
from db import initialize_db

app = Flask(__name__)
app.secret_key = 'e83361cf58e2bbee28c6'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)

try:
    initialize_db()  
except Exception as e:
    app.logger.error('Error initializing database: %s', e)

def hash_value(value):
    return hashlib.sha256(value.encode()).hexdigest()

def generate_serial_key(length=4):
    serial_key = secrets.token_hex(length).upper()
    return serial_key

def generate_pin():
    pin = ''.join(random.choices(string.digits, k=4))
    return pin

def store_payment_data(number, serial_key_encrypted, pin_encrypted):
    conn = sqlite3.connect('payments.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO payments (number, serial_key, pin)
        VALUES (?, ?, ?)
    ''', (number, serial_key_encrypted, pin_encrypted))
    conn.commit()
    conn.close()

def verify_serial_and_pin(serial_key, pin):
    conn = sqlite3.connect('payments.db')
    cursor = conn.cursor()

    serial_key_hashed = hash_value(serial_key)
    pin_hashed = hash_value(pin)

    cursor.execute('''
        SELECT max_allowed_checks FROM payments
        WHERE serial_key = ? AND pin = ?
    ''', (serial_key_hashed, pin_hashed))

    result = cursor.fetchone()
    conn.close()

    if result and result[0] > 0:
        return True, result[0]

    return False, None

@app.route('/')
def index():
    result = session.pop('payment_result', None)
    return render_template('index.html', result=result)

@app.route('/process_payment', methods=['POST'])
def process_payment():
    status = request.form.get('status')
    number = request.form.get('number')

    if status == 'success':
        serial_key = generate_serial_key()
        pin = generate_pin()

        serial_key_encrypted = hash_value(serial_key)
        pin_encrypted = hash_value(pin)

        store_payment_data(number, serial_key_encrypted, pin_encrypted)

        payment_result = {
            'success': True,
            'message': 'Payment Successful!',
            'serial_key': serial_key,
            'pin': pin  
        }
        app.logger.info('Payment successful for number: %s', number)
    else:
        payment_result = {
            'success': False,
            'message': 'Payment Unsuccessful!'
        }
        app.logger.warning('Payment unsuccessful for number: %s', number)

    # temporal storage so we can display the vouchers until the user refreshes.
    session['payment_result'] = payment_result
    return redirect(url_for('index'))

@app.route('/check_result', methods=['GET', 'POST'])
def check_result():
    if request.method == 'POST':
        serial_key = request.form.get('serial_key')
        pin = request.form.get('pin')

        success, max_allowed_checks = verify_serial_and_pin(serial_key, pin)

        if success:
            if max_allowed_checks is not None:
                conn = sqlite3.connect('payments.db')
                cursor = conn.cursor()

                cursor.execute('''
                    UPDATE payments
                    SET max_allowed_checks = max_allowed_checks - 1
                    WHERE serial_key = ? AND pin = ?
                ''', (hash_value(serial_key), hash_value(pin)))

                conn.commit()
                conn.close()

                session['remaining_checks'] = max_allowed_checks - 1
                app.logger.info('Serial key and PIN verified successfully for update')

                return redirect(url_for('show_result'))

        app.logger.warning('Invalid serial key, PIN, or no remaining checks attempted')
        error_message = 'Invalid serial key, PIN, or no remaining checks. Please try again.'
        return render_template('check_result.html', error=error_message)

    return render_template('check_result.html')

@app.route('/show_result')
def show_result():
    remaining_checks = session.get('remaining_checks', 3)
    return render_template('show_result.html', remaining_checks=remaining_checks)

if __name__ == '__main__':
    app.run(debug=True)
