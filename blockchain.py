# blockchain_app/blockchain.py

import hashlib
import json
from time import time
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Block:
    def __init__(self, index, timestamp, votes, previous_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.votes = votes  # List of votes
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'votes': self.votes,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class Blockchain:
    difficulty = 2  # Proof of work difficulty
    votes_per_block = 5  # Number of votes to trigger mining

    def __init__(self):
        self.unconfirmed_votes = []  # Votes waiting to be mined
        self.chain: List[Block] = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, time(), [], "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)
        logger.info("Genesis block created.")

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def proof_of_work(self, block: Block) -> str:
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * self.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash

    def add_block(self, block: Block, proof: str) -> bool:
        previous_hash = self.last_block.hash
        if previous_hash != block.previous_hash:
            logger.error("Previous hash does not match.")
            return False
        if not proof.startswith('0' * self.difficulty):
            logger.error("Proof of work is invalid.")
            return False
        if proof != block.compute_hash():
            logger.error("Hash does not match proof.")
            return False
        block.hash = proof
        self.chain.append(block)
        logger.info(f"Block {block.index} added to the blockchain.")
        return True

    def has_voted(self, voter_id: str) -> bool:
        # Check in confirmed votes
        for block in self.chain:
            for vote in block.votes:
                if vote['voter_id'] == voter_id:
                    return True
        # Check in unconfirmed votes
        for vote in self.unconfirmed_votes:
            if vote['voter_id'] == voter_id:
                return True
        return False

    def add_vote(self, vote: Dict) -> bool:
        if self.has_voted(voter_id=vote['voter_id']):
            logger.warning(f"Duplicate vote attempt by voter_id: {vote['voter_id']}")
            return False
        self.unconfirmed_votes.append(vote)
        logger.info(f"Vote added to unconfirmed_votes: {vote}")
        if len(self.unconfirmed_votes) >= self.votes_per_block:
            logger.info("Votes threshold reached. Mining new block.")
            self.mine()
        return True

    def mine(self) -> Block:
        if not self.unconfirmed_votes:
            logger.info("No votes to mine.")
            return None
        new_block = Block(
            index=self.last_block.index + 1,
            timestamp=time(),
            votes=self.unconfirmed_votes.copy(),  # Copy to prevent modification during mining
            previous_hash=self.last_block.hash
        )
        proof = self.proof_of_work(new_block)
        added = self.add_block(new_block, proof)
        if added:
            self.unconfirmed_votes = []
            logger.info(f"Block {new_block.index} mined successfully with {len(new_block.votes)} votes.")
            return new_block
        else:
            logger.error("Failed to add mined block.")
            return None

    def to_dict(self):
        chain_data = []
        for block in self.chain:
            chain_data.append({
                'index': block.index,
                'timestamp': block.timestamp,
                'votes': block.votes,
                'previous_hash': block.previous_hash,
                'nonce': block.nonce,
                'hash': block.hash
            })
        return chain_data

    def is_valid_chain(self, chain: List[Dict]) -> bool:
        if not chain:
            return False
        if chain[0]['previous_hash'] != "0":
            return False
        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i - 1]
            if current['previous_hash'] != previous['hash']:
                return False
            block = Block(
                index=current['index'],
                timestamp=current['timestamp'],
                votes=current['votes'],
                previous_hash=current['previous_hash'],
                nonce=current['nonce']
            )
            if current['hash'] != block.compute_hash():
                return False
        return True

    def replace_chain(self, new_chain: List[Dict]) -> bool:
        if self.is_valid_chain(new_chain) and len(new_chain) > len(self.chain):
            self.chain = []
            for block_data in new_chain:
                block = Block(
                    index=block_data['index'],
                    timestamp=block_data['timestamp'],
                    votes=block_data['votes'],
                    previous_hash=block_data['previous_hash'],
                    nonce=block_data['nonce']
                )
                block.hash = block_data['hash']
                self.chain.append(block)
            logger.info("Blockchain replaced with the new chain.")
            return True
        logger.warning("Received chain is invalid or shorter than the current chain.")
        return False
