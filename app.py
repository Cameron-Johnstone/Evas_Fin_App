from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
db = SQLAlchemy(app)

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    venue = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))  # e.g., "performance", "private event"
    notes = db.Column(db.Text)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))  # e.g., "costumes", "travel", "marketing"
    description = db.Column(db.Text)

# Create the database and tables
with app.app_context():
    db.create_all()

# Routes for the web interface
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/income', methods=['POST'])
def add_income():
    data = request.json
    new_income = Income(
        amount=data['amount'],
        venue=data['venue'],
        category=data['category'],
        notes=data.get('notes', '')
    )
    db.session.add(new_income)
    db.session.commit()
    return jsonify({'message': 'Income added successfully'})

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    data = request.json
    new_expense = Expense(
        amount=data['amount'],
        category=data['category'],
        description=data.get('description', '')
    )
    db.session.add(new_expense)
    db.session.commit()
    return jsonify({'message': 'Expense added successfully'})

@app.route('/api/summary', methods=['GET'])
def get_summary():
    # Get date range from query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Query income and expenses
    income_query = Income.query
    expense_query = Expense.query
    
    if start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        income_query = income_query.filter(Income.date.between(start, end))
        expense_query = expense_query.filter(Expense.date.between(start, end))
    
    total_income = sum(income.amount for income in income_query.all())
    total_expenses = sum(expense.amount for expense in expense_query.all())
    
    return jsonify({
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_profit': total_income - total_expenses
    })

# Service worker for PWA functionality
@app.route('/sw.js')
def service_worker():
    return app.send_static_file('sw.js')

@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

if __name__ == '__main__':
    app.run(debug=True)