"""
Existence Proof — MrLiouWord Identity Anchoring
origin_signature: MrLiouWord

Provides cryptographic proof of existence for the MrLiouWord identity
across the particle system. Uses a Merkle chain to anchor identity
claims with timestamps, creating an immutable proof trail.

The existence proof serves as the "carrier" (載體) — the persistent
identity that ties all system components together.
"""

import time
import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class IdentityAnchor:
    """A single identity anchor in the proof chain."""
    index: int
    identity: str
    claim: str
    timestamp: float
    prev_hash: str
    data_hash: str
    anchor_hash: str = ""

    def __post_init__(self):
        if not self.anchor_hash:
            self.anchor_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = f"{self.index}:{self.identity}:{self.claim}:{self.timestamp}:{self.prev_hash}:{self.data_hash}"
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "identity": self.identity,
            "claim": self.claim,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
            "data_hash": self.data_hash,
            "anchor_hash": self.anchor_hash,
        }


class ExistenceProof:
    """
    Merkle-chained existence proof for MrLiouWord.

    Each anchor in the chain contains:
      - Identity name
      - A claim (what is being proven)
      - Timestamp
      - Hash of associated data
      - Hash of previous anchor (chain integrity)

    The chain is append-only and verifiable.
    """

    GENESIS_HASH = "0" * 64

    def __init__(self, identity: str = "MrLiouWord"):
        self.identity = identity
        self.chain: List[IdentityAnchor] = []
        self.origin_signature = identity
        self._create_genesis()

    def _create_genesis(self):
        """Create the genesis anchor."""
        genesis = IdentityAnchor(
            index=0,
            identity=self.identity,
            claim="genesis: existence proof chain initialized",
            timestamp=time.time(),
            prev_hash=self.GENESIS_HASH,
            data_hash=hashlib.sha256(self.identity.encode()).hexdigest(),
        )
        self.chain.append(genesis)

    def anchor(self, claim: str, data: Optional[str] = None) -> IdentityAnchor:
        """Add a new anchor to the proof chain."""
        prev = self.chain[-1]
        data_hash = hashlib.sha256((data or claim).encode()).hexdigest()

        anchor = IdentityAnchor(
            index=len(self.chain),
            identity=self.identity,
            claim=claim,
            timestamp=time.time(),
            prev_hash=prev.anchor_hash,
            data_hash=data_hash,
        )
        self.chain.append(anchor)
        return anchor

    def verify_chain(self) -> bool:
        """Verify the entire chain's integrity."""
        if not self.chain:
            return False

        # Genesis check
        if self.chain[0].prev_hash != self.GENESIS_HASH:
            return False

        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Check prev_hash linkage
            if current.prev_hash != previous.anchor_hash:
                return False

            # Verify hash computation
            expected = current._compute_hash()
            if current.anchor_hash != expected:
                return False

        return True

    def verify_identity(self, identity: str) -> bool:
        """Check if all anchors belong to the claimed identity."""
        return all(a.identity == identity for a in self.chain)

    def get_proof(self, index: int) -> Optional[Dict]:
        """Get a specific anchor's proof with chain context."""
        if index < 0 or index >= len(self.chain):
            return None

        anchor = self.chain[index]
        return {
            "anchor": anchor.to_dict(),
            "chain_length": len(self.chain),
            "chain_valid": self.verify_chain(),
            "identity_verified": self.verify_identity(self.identity),
            "merkle_root": self.merkle_root(),
        }

    def merkle_root(self) -> str:
        """Compute Merkle root of all anchor hashes."""
        if not self.chain:
            return self.GENESIS_HASH

        hashes = [a.anchor_hash for a in self.chain]

        while len(hashes) > 1:
            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])  # duplicate last for odd count
            next_level = []
            for i in range(0, len(hashes), 2):
                combined = hashlib.sha256((hashes[i] + hashes[i + 1]).encode()).hexdigest()
                next_level.append(combined)
            hashes = next_level

        return hashes[0]

    def export_chain(self) -> Dict:
        """Export the full proof chain."""
        return {
            "identity": self.identity,
            "chain_length": len(self.chain),
            "merkle_root": self.merkle_root(),
            "chain_valid": self.verify_chain(),
            "anchors": [a.to_dict() for a in self.chain],
            "origin_signature": self.origin_signature,
        }

    def stats(self) -> Dict:
        return {
            "identity": self.identity,
            "chain_length": len(self.chain),
            "merkle_root": self.merkle_root()[:16] + "...",
            "chain_valid": self.verify_chain(),
            "first_anchor": self.chain[0].timestamp if self.chain else None,
            "last_anchor": self.chain[-1].timestamp if self.chain else None,
            "origin_signature": self.origin_signature,
        }
