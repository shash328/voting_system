# blockchain_app/blockchain_app.py

from flask import Flask, jsonify, request
import requests
import json
import threading
from blockchain import Blockchain, Block
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Blockchain
blockchain = Blockchain()

# Load peers from nodes.json
def load_peers():
    with open('nodes.json', 'r') as f:
        return json.load(f)

peers = load_peers()

# Endpoint to get the blockchain
@app.route('/chain', methods=['GET'])
def get_chain():
    response = {
        'chain': blockchain.to_dict(),
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

# Endpoint to add a new vote
@app.route('/vote', methods=['POST'])
def add_vote():
    data = request.get_json()
    voter_id = data.get('voter_id')
    candidate = data.get('candidate')

    # Validate input
    if not voter_id or not candidate:
        logger.error('Invalid vote data received.')
        return jsonify({'message': 'Invalid vote data'}), 400

    vote = {
        'voter_id': voter_id,
        'candidate': candidate
    }

    # Add vote to blockchain
    success = blockchain.add_vote(vote)
    if not success:
        logger.info(f"Vote by voter_id {voter_id} rejected (duplicate).")
        return jsonify({'message': 'Duplicate vote detected. You have already voted.'}), 400

    logger.info(f"Vote added: {vote}")

    # Broadcast vote to peers
    broadcast_vote(vote)

    # Check if a new block was mined
    if len(blockchain.chain[-1].votes) == 0 and len(blockchain.unconfirmed_votes) == 0:
        # A new block was mined with this vote
        block = blockchain.last_block
        broadcast_block(block)
    
    mine_votes()
    return jsonify({'message': 'Vote added and block mined successfully'}), 201

# Endpoint to trigger mining manually
@app.route('/mine', methods=['GET'])
def mine_votes():
    block = blockchain.mine()
    if not block:
        return jsonify({'message': 'No votes to mine'}), 200

    # Broadcast the new block to peers
    broadcast_block(block)

    response = {
        'message': 'Block mined successfully',
        'block': {
            'index': block.index,
            'timestamp': block.timestamp,
            'votes': block.votes,
            'previous_hash': block.previous_hash,
            'nonce': block.nonce,
            'hash': block.hash
        }
    }
    return jsonify(response), 200

# Endpoint to register a new node
@app.route('/register_node', methods=['POST'])
def register_new_peers():
    nodes = request.get_json().get('nodes')
    if nodes is None:
        return "Invalid data", 400

    for node in nodes:
        if node not in peers and node != get_node_address():
            peers.append(node)

    return jsonify({'message': 'New nodes have been added.', 'total_nodes': peers}), 201

# Endpoint to resolve conflicts and ensure consensus
@app.route('/resolve_conflicts', methods=['GET'])
def consensus():
    replaced = resolve_conflicts()
    if replaced:
        return jsonify({'message': 'Our chain was replaced', 'new_chain': blockchain.to_dict()}), 200
    else:
        return jsonify({'message': 'Our chain is authoritative', 'chain': blockchain.to_dict()}), 200

def get_node_address():
    # Assuming the node is running on localhost with a unique port
    host = request.host.split(':')[0]
    port = request.host.split(':')[1] if ':' in request.host else '5000'
    return f"{host}:{port}"

def broadcast_vote(vote):
    for peer in peers:
        url = f'http://{peer}/vote'
        try:
            response = requests.post(url, json=vote)
            if response.status_code == 201:
                logger.info(f"Vote broadcasted to {peer}")
            elif response.status_code == 400:
                logger.warning(f"Vote rejected by {peer}: {response.json()['message']}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to broadcast vote to {peer}: {e}")

def broadcast_block(block: Block):
    for peer in peers:
        url = f'http://{peer}/mine'
        try:
            response = requests.get(url)
            if response.status_code == 200:
                logger.info(f"Block broadcasted to {peer}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to broadcast block to {peer}: {e}")

def resolve_conflicts():
    neighbours = peers
    new_chain = None
    max_length = len(blockchain.chain)

    for node in neighbours:
        url = f'http://{node}/chain'
        try:
            response = requests.get(url)
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and blockchain.is_valid_chain(chain):
                    max_length = length
                    new_chain = chain
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch chain from {node}: {e}")

    if new_chain:
        blockchain.replace_chain(new_chain)
        return True

    return False

if __name__ == '__main__':
    # Read port from environment variable
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
