from brownie import MutualBackupKey, accounts
from eth_account import Account
import time

def generate_activation_signature(contract_address, chain_id, main_key, approver_private_key, deadline=None):
    # 1. 初始化合约
    Contract = MutualBackupKey.at(contract_address)

    # 2. 获取当前nonce
    nonce = Contract.activationNonces(main_key)

    # 3. 设置过期时间，30分钟有效期
    if deadline is None:
        deadline = int(time.time()) + 30 * 60

    # 4. 使用合约的 getMessageHash 函数获取待签名哈希
    message_hash = Contract.getMessageHash(main_key, nonce, deadline)

    # 5. 授权方签名
    signed = Account.signHash(message_hash, private_key=approver_private_key)
    signature = signed.signature

    # 6. 恢复签名者地址用于验证
    signer_address = Account.recoverHash(message_hash, signature=signature)

    # 输出结果
    print("=" * 50)
    print("签名生成成功！")
    print(f"合约地址: {contract_address}")
    print(f"链ID: {chain_id}")
    print(f"目标主钥匙: {main_key}")
    print(f"授权方地址: {signer_address}")
    print(f"Nonce: {nonce}")
    print(f"过期时间: {deadline} (北京时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(deadline))})")
    print(f"签名: {signature.hex()}")
    print("=" * 50)

    return signature, deadline, nonce

def main():
    # 本地测试网络设置
    CONTRACT_ADDRESS = "0x2279B7A0a67DB372996a5FaB50D91eAA73d2eBe6"  # 合约部署地址
    CHAIN_ID = 31337
    MAIN_KEY = accounts[1].address  # Wanru 账户

    # Anvil测试网络账户2的私钥 (KJ = accounts[2])
    APPROVER_PRIVATE_KEY = "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a"

    generate_activation_signature(CONTRACT_ADDRESS, CHAIN_ID, MAIN_KEY, APPROVER_PRIVATE_KEY)