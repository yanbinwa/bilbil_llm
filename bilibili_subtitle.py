import base64
import json

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding as padding2
import base64


PUBLIC_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAkJZWIUIje8VjJ3okESY8stCs/a95hTUqK3fD/AST0F8mf7rTLoHCaW+AjmrqVR9NM/tvQNni67b5tGC5z3PD6oROJJ24QfcAW9urz8WjtrS/pTAfGeP/2AMCZfCu9eECidy16U2oQzBl9Q0SPoz0paJ9AfgcrHa0Zm3RVPL7JvOUzscL4AnirYImPsdaHZ52hAwz5y9bYoiWzUkuG7LvnAxO6JHQ71B3VTzM3ZmstS7wBsQ4lIbD318b49x+baaXVmC3yPW/E4Ol+OBZIBMWhzl7FgwIpgbGmsJSsqrOq3D8IgjS12K5CgkOT7EB/sil7lscgc22E5DckRpMYRG8dwIDAQAB"

class RSAEncryptor:
    def __init__(self):
        self.public_key = None

    def set_public_key(self, public_key_str: str):
        """设置公钥"""
        try:
            # 如果公钥不包含头部和尾部，添加它们
            if not public_key_str.startswith('-----BEGIN PUBLIC KEY-----'):
                public_key_str = f'-----BEGIN PUBLIC KEY-----\n{public_key_str}\n-----END PUBLIC KEY-----'

            # 将PEM格式的公钥字符串转换为公钥对象
            self.public_key = serialization.load_pem_public_key(
                public_key_str.encode('utf-8')
            )
        except Exception as e:
            print(f"设置公钥失败: {str(e)}")
            raise

    def encrypt_long(self, data: str) -> str:
        """
        加密长文本
        """
        try:
            # 将数据转换为字节
            data_bytes = data.encode('utf-8')

            # 获取单次可加密的最大长度
            # RSA加密时，消息长度必须小于密钥长度减去padding长度
            max_length = (self.public_key.key_size // 8) - 42  # PKCS1 v1.5 padding需要11字节

            # 分块加密
            encrypted_blocks = []
            for i in range(0, len(data_bytes), max_length):
                block = data_bytes[i:i + max_length]
                encrypted_block = self.public_key.encrypt(
                    block,
                    padding2.OAEP(
                        mgf=padding2.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                encrypted_blocks.append(base64.b64encode(encrypted_block).decode())

            # 将所有加密块拼接
            return '.'.join(encrypted_blocks)

        except Exception as e:
            print(f"加密失败: {str(e)}")
            raise


class AESCipher:
    def __init__(self, key: bytes, iv: bytes):
        """
        初始化AES加解密器

        Args:
            key: 密钥 (16, 24 或 32字节)
            iv: 初始化向量 (16字节)
        """
        self.key = key
        self.iv = iv

    def encrypt(self, plaintext: str) -> str:
        """
        加密函数
        """
        # 1. PKCS7填充
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext.encode()) + padder.finalize()

        # 2. 创建加密器
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(self.iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()

        # 3. 加密
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        # 4. Base64编码
        return base64.b64encode(ciphertext).decode('utf-8')


    def decrypt(self, encrypted_text: str) -> str:
        """
        解密函数
        """
        try:
            # 1. Base64解码
            encrypted_data = base64.b64decode(encrypted_text)

            # 2. 创建解密器
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.CBC(self.iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()

            # 3. 解密
            padded_data = decryptor.update(encrypted_data) + decryptor.finalize()

            # 4. 去除PKCS7填充
            unpadder = padding.PKCS7(128).unpadder()
            data = unpadder.update(padded_data) + unpadder.finalize()

            # 5. 转换为字符串
            return data.decode('utf-8')

        except Exception as e:
            print(f"解密错误: {str(e)}")
            return None


# 使用示例
if __name__ == '__main__':
    # 测试数据
    data = json.dumps(
        {
            "url": "https://www.bilibili.com/video/BV1aa4y1M7KZ/?spm_id_from=333.337.search-card.all.click"
        }
    )
    key = "kedou@8989!63239"  # 16, 24, 或 32字节的密钥

    iv = "a2Vkb3VAODk4OSE2MzIzMw=="  # Base64编码的IV
    my_cipher = AESCipher(key.encode('utf-8'), key.encode('utf-8'))

    encrypted = my_cipher.encrypt(data)
    # # rse
    my_encryptor = RSAEncryptor()
    my_encryptor.set_public_key(PUBLIC_KEY)
    print(my_encryptor.encrypt_long(encrypted))
    print(my_encryptor.encrypt_long(encrypted))

    target = "wH8KKAgaq0LVgw7WMcFrKpc5TNmBaS4R/bnk55C9H7vg5sMQecEb3PtwjsayadOYyqcnz82gMCJMv9hCI9Yyn+Ne5OwvSlyu6mX/jEglQuowZ3ad5gT33liEAv6xeBZuUnIFg4/09aejcbLJZl+8Kg=="
    print(my_encryptor.encrypt_long(target))


# import json
#
# from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
# from cryptography.hazmat.primitives import padding
# from cryptography.hazmat.backends import default_backend
# import base64
#
#
# def aes_encrypt(data: str, key: str, iv_base64: str) -> str:
#     """
#     AES加密函数
#
#     Args:
#         data: 要加密的数据
#         key: 加密密钥
#         iv_base64: Base64编码的初始化向量
#
#     Returns:
#         加密后的Base64字符串
#     """
#     try:
#         # 将密钥和数据转换为字节
#         key_bytes = key.encode('utf-8')
#         data_bytes = data.encode('utf-8')
#
#         # Base64解码IV
#         iv = base64.b64decode(iv_base64)
#
#         # 创建填充器
#         padder = padding.PKCS7(128).padder()
#
#         # 填充数据
#         padded_data = padder.update(data_bytes) + padder.finalize()
#
#         # 创建加密器
#         cipher = Cipher(
#             algorithms.AES(key_bytes),
#             modes.CBC(iv),
#             backend=default_backend()
#         )
#         encryptor = cipher.encryptor()
#
#         # 加密数据
#         encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
#
#         # 将加密后的数据转换为Base64
#         return base64.b64encode(encrypted_data).decode('utf-8')
#
#     except Exception as e:
#         print(f"加密错误: {str(e)}")
#         return None
#
#
# def decrypt(key: str, iv: str, encrypted_text: str) -> str:
#     """
#     解密函数
#     """
#     try:
#         # 1. Base64解码
#         encrypted_data = base64.b64decode(encrypted_text)
#
#         key_bytes = key.encode('utf-8')
#         iv_bytes = base64.b64decode(iv)
#
#         # 2. 创建解密器
#         cipher = Cipher(
#             algorithms.AES(key_bytes),
#             modes.CBC(iv_bytes),
#             backend=default_backend()
#         )
#         decryptor = cipher.decryptor()
#
#         # 3. 解密
#         padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
#
#         # 4. 去除PKCS7填充
#         unpadder = padding.PKCS7(128).unpadder()
#         data = unpadder.update(padded_data) + unpadder.finalize()
#
#         # 5. 转换为字符串
#         return data.decode('utf-8')
#
#     except Exception as e:
#         print(f"解密错误: {str(e)}")
#         return None
#

# 使用示例
# if __name__ == '__main__':
#     # 测试数据
#     data = json.dumps(
#         {
#             "url": "https://www.bilibili.com/video/BV1aa4y1M7KZ/?spm_id_from=333.337.search-card.all.click"
#         }
#     )
#     key = "kedou@8989!63239"  # 16, 24, 或 32字节的密钥
#     print(len(key))
#
#     iv = "a2Vkb3VAODk4OSE2MzIzMw=="  # Base64编码的IV
#     print(len(key))
#
#     encrypted = aes_encrypt(data, key, iv)
#     print(f"加密结果: {encrypted}")
#     print(len(encrypted))
#     print(decrypt(key, key, encrypted))
#
#
#     target = "wH8KKAgaq0LVgw7WMcFrKpc5TNmBaS4R/bnk55C9H7vg5sMQecEb3PtwjsayadOYyqcnz82gMCJMv9hCI9Yyn+Ne5OwvSlyu6mX/jEglQuowZ3ad5gT33liEAv6xeBZuUnIFg4/09aejcbLJZl+8Kg=="
#     print(target)
#     print(len(target))
