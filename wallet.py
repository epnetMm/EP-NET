import nacl.signing
import nacl.encoding
import json
import os
import logging
from typing import Dict, Tuple, Any, Optional
from transaction import Transaction

class Wallet:
    """
    Represents a wallet in the EPNET blockchain.
    Each wallet contains:
    - Private key
    - Public key (used as the wallet address)
    """
    
    def __init__(self, private_key: Optional[str] = None):
        """
        Initialize a wallet, either with a provided private key or by generating a new one
        
        Args:
            private_key: Optional hex-encoded private key string
        """
        if private_key:
            # Convert hex string to bytes
            key_bytes = bytes.fromhex(private_key)
            self.signing_key = nacl.signing.SigningKey(key_bytes)
        else:
            # Generate a new random key
            self.signing_key = nacl.signing.SigningKey.generate()
        
        # Get the verify key (public key)
        self.verify_key = self.signing_key.verify_key
    
    @property
    def private_key(self) -> str:
        """
        Get the private key as a hex string
        
        Returns:
            Hex-encoded private key
        """
        return self.signing_key.encode(encoder=nacl.encoding.HexEncoder).decode('utf-8')
    
    @property
    def public_key(self) -> str:
        """
        Get the public key as a hex string (this serves as the wallet address)
        
        Returns:
            Hex-encoded public key
        """
        return self.verify_key.encode(encoder=nacl.encoding.HexEncoder).decode('utf-8')
    
    def create_transaction(self, recipient: str, amount: float) -> Transaction:
        """
        Create and sign a new transaction
        
        Args:
            recipient: Recipient's public key (address)
            amount: Amount to transfer
            
        Returns:
            A signed Transaction
        """
        transaction = Transaction(self.public_key, recipient, amount)
        transaction.sign_transaction(self.signing_key)
        return transaction
    
    def save_to_file(self, filename: str):
        """
        Save the wallet to a file
        
        Args:
            filename: Path to save the wallet to
        """
        from config import ensure_data_directory
        
        # 데이터 디렉토리 확인
        ensure_data_directory()
        
        # 상대 경로를 절대 경로로 변환
        if not os.path.isabs(filename):
            from config import DATA_DIR
            filename = os.path.join(DATA_DIR, filename)
        
        data = {
            'private_key': self.private_key,
            'public_key': self.public_key
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            logging.info(f"월렛이 저장되었습니다: {filename}")
            logging.info(f"월렛 주소: {self.public_key}")
            return True
        except Exception as e:
            logging.error(f"월렛 저장 중 오류: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, filename: str) -> 'Wallet':
        """
        Load a wallet from a file
        
        Args:
            filename: Path to load the wallet from
            
        Returns:
            Wallet instance
        """
        from config import ensure_data_directory
        
        # 데이터 디렉토리 확인
        ensure_data_directory()
        
        # 상대 경로를 절대 경로로 변환
        if not os.path.isabs(filename):
            from config import DATA_DIR
            filename = os.path.join(DATA_DIR, filename)
        
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    data = json.load(f)
                wallet = cls(private_key=data['private_key'])
                logging.info(f"월렛이 로드되었습니다: {filename}")
                logging.info(f"월렛 주소: {wallet.public_key}")
                return wallet
            else:
                # 월렛 파일이 없는 경우 새 월렛 생성
                wallet = cls()
                wallet.save_to_file(filename)
                logging.info(f"새 월렛이 생성되었습니다: {filename}")
                return wallet
        except Exception as e:
            # 로드 중 오류 발생시 새 월렛 생성
            logging.error(f"월렛 로드 중 오류, 새 월렛을 생성합니다: {e}")
            wallet = cls()
            wallet.save_to_file(filename)
            return wallet
    
    def to_dict(self) -> Dict[str, str]:
        """
        Convert the wallet to a dictionary
        
        Returns:
            Dictionary representation of the wallet
        """
        return {
            'private_key': self.private_key,
            'public_key': self.public_key
        }
