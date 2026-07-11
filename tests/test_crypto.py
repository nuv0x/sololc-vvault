from cryptography.fernet import Fernet


def test_crypto_encrypt_decrypt():
    # 1. 生成临时密钥
    key = Fernet.generate_key()
    f = Fernet(key)

    # 2. 原始敏感数据
    raw_data = b"my_super_secret_totp_keys"

    # 3. 加密后解密，验证数据一致性
    encrypted = f.encrypt(raw_data)
    decrypted = f.decrypt(encrypted)

    assert decrypted == raw_data
    assert encrypted != raw_data
