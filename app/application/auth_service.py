from ecdsa import VerifyingKey, NIST256p, BadSignatureError
import base64

class AuthService:
    @staticmethod
    def verify_signature(public_key_pem: str, signature_b64: str, message: str) -> bool:
        """
        Verify an ECDSA secp256r1 signature.
        """
        try:
            vk = VerifyingKey.from_pem(public_key_pem)
            signature = base64.b64decode(signature_b64)
            return vk.verify(signature, message.encode('utf-8'))
        except (BadSignatureError, ValueError, TypeError) as e:
            return False
