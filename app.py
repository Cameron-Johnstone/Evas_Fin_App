from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import func, extract, text
import os
import csv
from io import StringIO
import json
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
database_url = os.getenv('DATABASE_URL', 'sqlite:///finance.db')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Enhanced models with more metadata
class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text)
    venue = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db():
    """Initialize database and handle migrations"""
    try:
        with app.app_context():
            # Create tables if they don't exist
            db.create_all()
            
            # Check and add timestamp columns
            from sqlalchemy import text
            
            # Add created_at and modified_at to income table
            try:
                db.session.execute(text(
                    'ALTER TABLE income ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                ))
                db.session.execute(text(
                    'ALTER TABLE income ADD COLUMN modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                ))
            except Exception as e:
                print(f"Income table migration: {str(e)}")
                db.session.rollback()

            # Add created_at and modified_at to expense table
            try:
                db.session.execute(text(
                    'ALTER TABLE expense ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                ))
                db.session.execute(text(
                    'ALTER TABLE expense ADD COLUMN modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                ))
            except Exception as e:
                print(f"Expense table migration: {str(e)}")
                db.session.rollback()

            db.session.commit()

    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        db.session.rollback()

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    try:
        with db.engine.connect() as conn:
            # This query works for both PostgreSQL and SQLite
            if database_url.startswith('postgresql://'):
                query = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = :table 
                    AND column_name = :column
                """)
            else:  # SQLite
                query = text(f"SELECT * FROM pragma_table_info('{table_name}') WHERE name = :column")
            
            result = conn.execute(query, {'table': table_name, 'column': column_name})
            return bool(result.first())
    except Exception as e:
        logger.error(f"Error checking column {column_name} in {table_name}: {str(e)}")
        return False

def init_db():
    """Initialize database and handle migrations"""
    try:
        with app.app_context():
            # Create tables if they don't exist
            db.create_all()
            logger.info("Database tables created successfully")

            # Check and add created_at column to income table if it doesn't exist
            if not check_column_exists('income', 'created_at'):
                logger.info("Adding created_at column to income table")
                if database_url.startswith('postgresql://'):
                    db.session.execute(text(
                        'ALTER TABLE income ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                    ))
                else:  # SQLite
                    db.session.execute(text(
                        'ALTER TABLE income ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP'
                    ))

            # Check and add modified_at column to income table if it doesn't exist
            if not check_column_exists('income', 'modified_at'):
                logger.info("Adding modified_at column to income table")
                if database_url.startswith('postgresql://'):
                    db.session.execute(text(
                        'ALTER TABLE income ADD COLUMN modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                    ))
                else:  # SQLite
                    db.session.execute(text(
                        'ALTER TABLE income ADD COLUMN modified_at DATETIME DEFAULT CURRENT_TIMESTAMP'
                    ))

            # Check and add timestamp columns to expense table if they don't exist
            if not check_column_exists('expense', 'created_at'):
                logger.info("Adding created_at column to expense table")
                if database_url.startswith('postgresql://'):
                    db.session.execute(text(
                        'ALTER TABLE expense ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                    ))
                else:  # SQLite
                    db.session.execute(text(
                        'ALTER TABLE expense ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP'
                    ))

            if not check_column_exists('expense', 'modified_at'):
                logger.info("Adding modified_at column to expense table")
                if database_url.startswith('postgresql://'):
                    db.session.execute(text(
                        'ALTER TABLE expense ADD COLUMN modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                    ))
                else:  # SQLite
                    db.session.execute(text(
                        'ALTER TABLE expense ADD COLUMN modified_at DATETIME DEFAULT CURRENT_TIMESTAMP'
                    ))

            db.session.commit()
            logger.info("Database migration completed successfully")

    except Exception as e:
        db.session.rollback()
        logger.error(f"Database initialization error: {str(e)}")
        raise

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/income', methods=['GET'])
def get_income():
    # Get optional date range filters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Income.query.order_by(Income.date.desc())
    
    if start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(Income.date.between(start, end))
    
    incomes = query.all()
    return jsonify([{
        'id': i.id,
        'date': i.date.strftime('%Y-%m-%d'),
        'amount': i.amount,
        'category': i.category,
        'notes': i.notes,
        'venue': i.venue
    } for i in incomes])

@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Expense.query.order_by(Expense.date.desc())
    
    if start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(Expense.date.between(start, end))
    
    expenses = query.all()
    return jsonify([{
        'id': e.id,
        'date': e.date.strftime('%Y-%m-%d'),
        'amount': e.amount,
        'category': e.category,
        'description': e.description
    } for e in expenses])

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    now = datetime.utcnow()
    
    # Total calculations (all time)
    total_income = db.session.query(func.sum(Income.amount)).scalar() or 0
    total_expenses = db.session.query(func.sum(Expense.amount)).scalar() or 0
    
    # Current week calculations
    week_start = now - timedelta(days=now.weekday())
    current_week_income = db.session.query(func.sum(Income.amount)).filter(
        Income.date >= week_start
    ).scalar() or 0
    current_week_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.date >= week_start
    ).scalar() or 0

    # Current month calculations
    month_start = now.replace(day=1)
    current_month_income = db.session.query(func.sum(Income.amount)).filter(
        Income.date >= month_start
    ).scalar() or 0
    current_month_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.date >= month_start
    ).scalar() or 0

    # Weekly average (last 4 weeks)
    four_weeks_ago = now - timedelta(weeks=4)
    weekly_avg_income = db.session.query(func.sum(Income.amount)).filter(
        Income.date >= four_weeks_ago
    ).scalar() or 0
    weekly_avg_income = weekly_avg_income / 4

    weekly_avg_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.date >= four_weeks_ago
    ).scalar() or 0
    weekly_avg_expenses = weekly_avg_expenses / 4

    # Monthly average (last 3 months)
    three_months_ago = now - timedelta(days=90)
    monthly_avg_income = db.session.query(func.sum(Income.amount)).filter(
        Income.date >= three_months_ago
    ).scalar() or 0
    monthly_avg_income = monthly_avg_income / 3

    monthly_avg_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.date >= three_months_ago
    ).scalar() or 0
    monthly_avg_expenses = monthly_avg_expenses / 3

    return jsonify({
        'totals': {
            'income': total_income,
            'expenses': total_expenses,
            'net': total_income - total_expenses
        },
        'current': {
            'week': {
                'income': current_week_income,
                'expenses': current_week_expenses,
                'net': current_week_income - current_week_expenses
            },
            'month': {
                'income': current_month_income,
                'expenses': current_month_expenses,
                'net': current_month_income - current_month_expenses
            }
        },
        'averages': {
            'weekly': {
                'income': weekly_avg_income,
                'expenses': weekly_avg_expenses,
                'net': weekly_avg_income - weekly_avg_expenses
            },
            'monthly': {
                'income': monthly_avg_income,
                'expenses': monthly_avg_expenses,
                'net': monthly_avg_income - monthly_avg_expenses
            }
        }
    })

@app.route('/api/trends', methods=['GET'])
def get_trends():
    # Get daily totals for the last 30 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    income_daily = db.session.query(
        func.date(Income.date).label('date'),
        func.sum(Income.amount).label('total')
    ).filter(Income.date.between(start_date, end_date)
    ).group_by(func.date(Income.date)).all()
    
    expense_daily = db.session.query(
        func.date(Expense.date).label('date'),
        func.sum(Expense.amount).label('total')
    ).filter(Expense.date.between(start_date, end_date)
    ).group_by(func.date(Expense.date)).all()
    
    return jsonify({
        'income': [{
            'date': date.strftime('%Y-%m-%d'),
            'total': float(total)
        } for date, total in income_daily],
        'expenses': [{
            'date': date.strftime('%Y-%m-%d'),
            'total': float(total)
        } for date, total in expense_daily]
    })

@app.route('/api/income', methods=['POST'])
def add_income():
    data = request.json
    try:
        date = datetime.strptime(data['date'], '%Y-%m-%d') if 'date' in data else datetime.utcnow()
        new_income = Income(
            date=date,
            amount=float(data['amount']),
            category=data['category'],
            notes=data.get('notes', ''),
            venue=data.get('venue', '')
        )
        db.session.add(new_income)
        db.session.commit()
        return jsonify({'message': 'Income added successfully', 'id': new_income.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    data = request.json
    try:
        date = datetime.strptime(data['date'], '%Y-%m-%d') if 'date' in data else datetime.utcnow()
        new_expense = Expense(
            date=date,
            amount=float(data['amount']),
            category=data['category'],
            description=data.get('description', '')
        )
        db.session.add(new_expense)
        db.session.commit()
        return jsonify({'message': 'Expense added successfully', 'id': new_expense.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    data_type = request.args.get('type', 'all')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    si = StringIO()
    writer = csv.writer(si)
    
    if data_type in ['all', 'income']:
        writer.writerow(['Type', 'Date', 'Amount', 'Category', 'Venue', 'Notes'])
        query = Income.query.order_by(Income.date)
        if start_date and end_date:
            query = query.filter(Income.date.between(
                datetime.strptime(start_date, '%Y-%m-%d'),
                datetime.strptime(end_date, '%Y-%m-%d')
            ))
        for income in query.all():
            writer.writerow([
                'Income',
                income.date.strftime('%Y-%m-%d'),
                f'£{income.amount:.2f}',
                income.category,
                income.venue,
                income.notes
            ])

    if data_type in ['all', 'expenses']:
        if data_type == 'all':
            writer.writerow([])  # Add blank row between sections
        writer.writerow(['Type', 'Date', 'Amount', 'Category', 'Description'])
        query = Expense.query.order_by(Expense.date)
        if start_date and end_date:
            query = query.filter(Expense.date.between(
                datetime.strptime(start_date, '%Y-%m-%d'),
                datetime.strptime(end_date, '%Y-%m-%d')
            ))
        for expense in query.all():
            writer.writerow([
                'Expense',
                expense.date.strftime('%Y-%m-%d'),
                f'£{expense.amount:.2f}',
                expense.category,
                expense.description
            ])

    output = si.getvalue()
    si.close()
    
    filename = f'finance_export_{datetime.now().strftime("%Y%m%d")}.csv'
    return output, 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename={filename}'
    }

@app.route('/api/delete/income/<int:id>', methods=['DELETE'])
def delete_income(id):
    try:
        income = Income.query.get_or_404(id)
        db.session.delete(income)
        db.session.commit()
        return jsonify({'message': 'Income deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/delete/expense/<int:id>', methods=['DELETE'])
def delete_expense(id):
    try:
        expense = Expense.query.get_or_404(id)
        db.session.delete(expense)
        db.session.commit()
        return jsonify({'message': 'Expense deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/sw.js')
def service_worker():
    return app.send_static_file('sw.js')

@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

# Call init_db when app starts
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)