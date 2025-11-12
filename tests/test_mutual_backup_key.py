import pytest
from brownie import MutualBackupKey, accounts
from eth_account import Account
import time

@pytest.fixture
def deploy_contract():
    """部署测试合约"""
    return MutualBackupKey.deploy({"from": accounts[0]})

@pytest.fixture
def setup_users(deploy_contract):
    """设置测试用户并配置"""
    userWanru = accounts[1]   # 婉如主钥匙
    userKJ = accounts[2]      # KJ主钥匙
    backupWanru = accounts[3] # 婉如备用钥匙
    backupKJ = accounts[4]    # KJ备用钥匙

    # Wanru 设置配置：备用钥匙=backupWanru，授权方=userKJ
    deploy_contract.userConfig(backupWanru, userKJ, {"from": userWanru})
    # KJ 设置配置：备用钥匙=backupKJ，授权方=userWanru
    deploy_contract.userConfig(backupKJ, userWanru, {"from": userKJ})

    return {
        "contract": deploy_contract,
        "userWanru": userWanru,
        "userKJ": userKJ,
        "backupWanru": backupWanru,
        "backupKJ": backupKJ
    }

def generate_test_signature(contract, main_key, approver_private_key, deadline=None):
    """
    生成激活签名
    :param contract: 合约实例
    :param main_key: 主钥匙地址
    :param approver_private_key: 授权方私钥 (16进制字符串)
    :param deadline: 过期时间戳
    :return: (signature, deadline) 元组
    """
    nonce = contract.activationNonces(main_key)
    if deadline is None:
        deadline = int(time.time()) + 30 * 60

    # 使用合约的 getMessageHash 函数获取待签名的哈希
    message_hash = contract.getMessageHash(main_key, nonce, deadline)

    # 使用 eth_account 签名
    signed = Account.signHash(message_hash, private_key=approver_private_key)

    return signed.signature, deadline

def test_activate_wanru_backup_with_signature(setup_users):
    """测试通过授权方的签名激活备用钥匙"""
    contract = setup_users["contract"]
    userWanru = setup_users["userWanru"]
    userKJ = setup_users["userKJ"]
    backupWanru = setup_users["backupWanru"]

    # Anvil测试网络账户2的私钥 (userKJ = accounts[2])
    kj_private_key = accounts[2]

    # 1. 授权方生成签名
    signature, deadline = generate_test_signature(
        contract,
        userWanru.address,
        kj_private_key
    )

    # 2. 备用钥匙提交签名
    tx = contract.activateBackupKey(
        userWanru.address,
        signature,
        deadline,
        {"from": backupWanru}
    )

    # 3. 验证结果
    assert "BackupActivated" in tx.events
    assert tx.events["BackupActivated"]["isSignedActivation"] == True
    user_info = contract.getUser(userWanru.address)
    assert user_info["isBackupActive"] == True
    assert contract.activationNonces(userWanru.address) == 1  # nonce递增

def test_activate_KJ_backup_with_signature(setup_users):
    """测试通过授权方的签名激活备用钥匙"""
    contract = setup_users["contract"]
    userKJ = setup_users["userKJ"]
    userWanru = setup_users["userWanru"]
    backupKJ = setup_users["backupKJ"]

    # Anvil测试网络账户1的私钥 (userWanru = accounts[1])
    wanru_private_key = accounts[1]

    # 1. 授权方生成签名
    signature, deadline = generate_test_signature(
        contract,
        userKJ.address,
        wanru_private_key
    )

    # 2. 备用钥匙提交签名
    tx = contract.activateBackupKey(
        userKJ.address,
        signature,
        deadline,
        {"from": backupKJ}
    )

    # 3. 验证结果
    assert "BackupActivated" in tx.events
    assert tx.events["BackupActivated"]["isSignedActivation"] == True
    user_info = contract.getUser(userKJ.address)
    assert user_info["isBackupActive"] == True
    assert contract.activationNonces(userKJ.address) == 1  # nonce递增