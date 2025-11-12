from brownie import MutualBackupKey, accounts, network

def main():
    """
    部署 MutualBackupKey 合约
    """
    # 获取部署账户
    deployer = accounts[0]

    print("=" * 60)
    print(f"部署网络: {network.show_active()}")
    print(f"部署账户: {deployer.address}")
    print(f"账户余额: {deployer.balance() / 1e18} ETH")
    print("=" * 60)

    # 部署合约
    print("\n正在部署 MutualBackupKey 合约...")
    contract = MutualBackupKey.deploy(
        {'from': deployer, 'gas_price': '20 gwei'}
    )

    print("=" * 60)
    print("✅ 部署成功！")
    print(f"合约地址: {contract.address}")
    print(f"部署交易: {contract.tx.txid}")
    print(f"链ID: {contract.CHAIN_ID()}")
    print(f"合约地址(存储): {contract.CONTRACT_ADDRESS()}")
    print("=" * 60)

    # 保存部署信息供后续脚本使用
    print("\n📝 部署信息已保存到 build/deployments/")

    return contract
