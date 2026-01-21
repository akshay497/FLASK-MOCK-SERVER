"""
Flask Mock Server - Customer Data API
Serves customer data from JSON file with pagination support
"""

from flask import Flask, jsonify, request
import json
import os

app = Flask(__name__)

# Load customer data from JSON file
def load_customers():
    """Load customers from JSON file"""
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'customers.json')
    with open(data_path, 'r') as f:
        return json.load(f)

# Load data at startup
CUSTOMERS = load_customers()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "mock-server",
        "total_customers": len(CUSTOMERS)
    })


@app.route('/api/customers', methods=['GET'])
def get_customers():
    """
    Get paginated list of customers
    Query params:
        - page: Page number (default: 1)
        - limit: Items per page (default: 10)
    """
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    # Validate parameters
    if page < 1:
        page = 1
    if limit < 1:
        limit = 1
    if limit > 100:
        limit = 100
    
    # Calculate pagination
    total = len(CUSTOMERS)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    # Get paginated data
    paginated_customers = CUSTOMERS[start_idx:end_idx]
    
    return jsonify({
        "data": paginated_customers,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    })


@app.route('/api/customers/<customer_id>', methods=['GET'])
def get_customer(customer_id):
    """
    Get a single customer by ID
    Returns 404 if customer not found
    """
    for customer in CUSTOMERS:
        if customer['customer_id'] == customer_id:
            return jsonify({
                "data": customer
            })
    
    return jsonify({
        "error": "Customer not found",
        "customer_id": customer_id
    }), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
