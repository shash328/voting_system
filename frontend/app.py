# frontend_app/frontend_app.py

from flask import Flask, render_template, request, jsonify
import requests
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URL of the Blockchain Flask App
BLOCKCHAIN_URL = os.environ.get('BLOCKCHAIN_URL', 'http://127.0.0.1:5000')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_vote', methods=['POST'])
def submit_vote():
    data = request.get_json()
    voter_id = data.get('voter_id')
    candidate = data.get('candidate')

    if not voter_id or not candidate:
        return jsonify({'message': 'Invalid vote data'}), 400

    vote = {
        'voter_id': voter_id,
        'candidate': candidate
    }

    try:
        response = requests.post(f"{BLOCKCHAIN_URL}/vote", json=vote)
        if response.status_code == 201:
            logger.info("Vote submitted successfully.")
            return jsonify({'message': response.json()['message']}), 201
        else:
            logger.warning(f"Failed to submit vote: {response.json()['message']}")
            return jsonify({'message': response.json()['message']}), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error communicating with Blockchain App: {e}")
        return jsonify({'message': 'Blockchain service unavailable.'}), 503

@app.route('/get_chain', methods=['GET'])
def get_chain():
    try:
        response = requests.get(f"{BLOCKCHAIN_URL}/chain")
        if response.status_code == 200:
            chain = response.json()['chain']
            return jsonify({'chain': chain}), 200
        else:
            logger.warning("Failed to retrieve blockchain.")
            return jsonify({'message': 'Failed to retrieve blockchain.'}), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error communicating with Blockchain App: {e}")
        return jsonify({'message': 'Blockchain service unavailable.'}), 503

if __name__ == '__main__':
    # Read port from environment variable
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
