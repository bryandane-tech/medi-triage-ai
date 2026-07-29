import base64
import os
from typing import Dict, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class MultiKeyEnvelopeEncryption:
    """AES-256-GCM Envelope Encryption with Multi-Version Key Lifecycle Management."""

    def __init__(self, key_ring: Dict[str, str], active_version: str):
        """
        key_ring: Dictionary mapping version strings to Base64-encoded 32-byte keys.
                  e.g., {"v1": "key1_b64...", "v2": "key2_b64..."}
        active_version: Default key version used for new encryptions.
        """
        self.active_version = active_version
        self.keys: Dict[str, bytes] = {}

        for ver, key_b64 in key_ring.items():
            raw_key = base64.b64decode(key_b64)
            if len(raw_key) != 32:
                raise ValueError(f"Key for version {ver} must be 32 bytes (256-bit).")
            self.keys[ver] = raw_key

        if self.active_version not in self.keys:
            raise ValueError(f"Active key version '{active_version}' is missing from key ring.")

    def encrypt(self, plaintext: str) -> Tuple[str, str]:
        """
        Encrypts text with the current active_version key.
        Returns: Tuple of (formatted_ciphertext, key_version)
        Format: "v2:BASE64(IV + Ciphertext)"
        """
        if not plaintext:
            return "", self.active_version

        iv = os.urandom(12)
        aesgcm = AESGCM(self.keys[self.active_version])
        ciphertext = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)

        b64_payload = base64.b64encode(iv + ciphertext).decode("utf-8")
        formatted = f"{self.active_version}:{b64_payload}"
        return formatted, self.active_version

    def decrypt(self, formatted_payload: str) -> Tuple[str, str]:
        """
        Parses version prefix and decrypts payload with matching key.
        Returns: Tuple of (plaintext, key_version_used)
        """
        if not formatted_payload:
            return "", self.active_version

        if ":" not in formatted_payload:
            ver = "v1"
            b64_payload = formatted_payload
        else:
            ver, b64_payload = formatted_payload.split(":", 1)

        if ver not in self.keys:
            raise KeyError(f"Key version '{ver}' is not available in current key ring.")

        raw_data = base64.b64decode(b64_payload.encode("utf-8"))
        iv = raw_data[:12]
        ciphertext = raw_data[12:]

        aesgcm = AESGCM(self.keys[ver])
        decrypted_bytes = aesgcm.decrypt(iv, ciphertext, None)
        return decrypted_bytes.decode("utf-8"), verpy
