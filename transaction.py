# transaction.py

from flask import Blueprint, render_template


from dotenv import load_dotenv

load_dotenv()

transaction_bp = Blueprint('transaction', __name__, url_prefix='/transaction')

@transaction_bp.route('/', methods=['GET'])
def transaction_form():
    return render_template('transaction.html')
