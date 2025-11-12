pragma solidity ^0.8.13;

/**
 * 用eth-brownie 做两个人的签名，互相激活备用钥匙的合约
 * @title 双签名备用钥匙激活合约
 * @dev 两个用户互相授权对方激活自己的备用钥匙，仅支持授权方直接激活 + 离线签名激活
 */
contract MutualBackupKey {
    // 用户信息
    struct User{
        address mainKey;
        address backupKey;
        address approver;
        bool isBackupActive;
    }

    // 主钥匙 => 用户配置
    mapping(address => User) public users;
    // 主钥匙 => 签名nonce(防重播)
    mapping(address => uint256) public activationNonces;
    // 链ID（防跨链重播）
    uint256 public immutable CHAIN_ID;
    // 合约地址（防跨合约重播）
    address public immutable CONTRACT_ADDRESS;

    // 事件定义
    event UserConfig(address indexed mainKey, address indexed backupKey, address approver);
    event BackupActivated(address indexed mainKey, address indexed backupKey, address activatedBy, bool isSignedActivation);

    constructor() {
        CHAIN_ID = block.chainid;
        CONTRACT_ADDRESS = address(this);
    }

    // 修饰器
    modifier onlyMainKey(address mainKey) {
        require(msg.sender == mainKey, "DSB: only main key");
        _;
    }

    modifier onlyApprover(address mainKey) {
        require(msg.sender == users[mainKey].approver, "DSB: only approver");
        _;
    }

    modifier onlyBackupKey(address mainKey) {
        require(msg.sender == users[mainKey].backupKey, "DSB: only backup key");
        _;
    }

    modifier backupNotActive(address mainKey) {
        require(!users[mainKey].isBackupActive, "DSB: backup already active");
        _;
    }

    modifier validConfig(address mainKey) {
        require(users[mainKey].backupKey != address(0), "DSB: backup key not set");
        require(users[mainKey].approver != address(0), "DSB: approver not set");
        _;
    }

    // 业务功能区

    /**
     * @dev 生成签名：计算待签名哈希
     * 结构化数据签名哈希计算逻辑
     */
    function getMessageHash(address mainKey, uint256 nonce, uint256 deadline) external view returns (bytes32) {
        return keccak256(
            abi.encodePacked(
                "\x19Ethereum Signed Message:\n32",
                keccak256(
                    abi.encode("activateBackup", CHAIN_ID, CONTRACT_ADDRESS, mainKey, nonce, deadline)
                )
            )
        );
    }

    /**
     * @dev 用户注册（主钥匙、备用钥匙、授权方）
     * @param backupKey 备用钥匙地址
     * @param approver 授权方地址（对方主钥匙）
     */
    function userConfig(address backupKey, address approver) external {
        require(backupKey != address(0) && backupKey != msg.sender, "DSB: invalid backup key");
        require(approver != address(0) && approver != msg.sender, "DSB: invalid approver");

        users[msg.sender] = User({
            mainKey: msg.sender,
            backupKey: backupKey,
            approver: approver,
            isBackupActive: false
        });

        emit UserConfig(msg.sender, backupKey, approver);
    }

    /**
     * @dev 查询用户信息 
     * @param mainKey 主钥匙地址
     */
    function getUser(address mainKey) external view returns (User memory) {
        return users[mainKey];
    }

    function activateBackupKey(address mainKey, bytes memory approverSignature, uint deadline
        ) external backupNotActive(mainKey) validConfig(mainKey) {
            User storage user = users[mainKey];
            uint256 currentNonce = activationNonces[mainKey];

            // 1. 验证签名是否过期
            require(block.timestamp <= deadline, "Signature expired");

            // 2. 构建签名消息()
            bytes32 messageHash = keccak256(
                abi.encodePacked(
                    "\x19Ethereum Signed Message:\n32",
                    keccak256(
                        abi.encode("activateBackup", CHAIN_ID, CONTRACT_ADDRESS, mainKey, currentNonce, deadline)
                        )
                    )
                );

            // 3. 验证签名是否来自授权方
            address signer = recoverSigner(messageHash, approverSignature);
            require(signer == user.approver, "DSB: invalid approver signature");

            // 4. 激活备用钥匙
            user.isBackupActive = true;
            activationNonces[mainKey]++;

            emit BackupActivated(mainKey, user.backupKey, msg.sender, true);
        }
    
    /**
     * @dev 从签名恢复签名者地址
     */
    function recoverSigner(bytes32 messageHash, bytes memory signature) internal pure returns (address signer){
        require(signature.length == 65, "DSB: invalid signature length");

        bytes32 r;
        bytes32 s;
        uint8 v;

        assembly {
            r := mload(add(signature, 32))
            s := mload(add(signature, 64))
            v := byte(0, mload(add(signature, 96)))
        }

        require(v == 27 || v == 28, "DSB: invalid v value");
        signer = ecrecover(messageHash, v, r, s);
        require(signer != address(0), "DSB: invalid signature");
    }
}