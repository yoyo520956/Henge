# Henge iOS — 免费 GitHub Actions 编译 IPA

## 前置条件（只需做一次）

1. **Fork/克隆本仓库到你自己的 GitHub 账号**（公开仓库 = 无限免费 macOS 分钟数；私有仓库 = 每月 2000 分钟免费额度）。
2. 在你的仓库 **Settings → Secrets and variables → Actions → New repository secret** 添加：
   - `APPLE_TEAM_ID` = 你的 Apple Developer Team ID（10 位字母数字，如 `ABCD1234EF`）
     - 在 Xcode → Preferences → Accounts 里查看，或终端运行：
       ```bash
       security find-identity -v -p codesigning | head -1
       ```
3. （可选）如果想自动发布到 Releases，确保仓库有 **Settings → Actions → General → Workflow permissions = Read and write permissions**。

---

## 触发编译

| 方式 | 说明 |
|------|------|
| **手动** | 在仓库 **Actions → Build Henge IPA → Run workflow** 点击运行 |
| **Push main** | 推送到 `main` 分支自动编译 |
| **打 Tag** | `git tag v0.3.1 && git push origin v0.3.1` → 自动编译 + 创建 Release 并上传 IPA |

---

## 产物获取

| 方式 | 位置 |
|------|------|
| **Artifact** | Actions 运行完成后 → **Artifacts → Henge-ipa** 下载 `Henge.ipa`（保留 30 天） |
| **Release** | 打 Tag 触发时 → **Releases** 页面直接下载 IPA |

---

## 本地验证（有 Mac 时）

```bash
# 1. 安装 xcodegen
brew install xcodegen

# 2. 生成工程
cd ios && xcodegen generate

# 3. 编译并打包（需先在 GitHub 设置好 APPLE_TEAM_ID secret，或本地 export）
xcodebuild -scheme Henge -configuration Release -sdk iphoneos \
  -derivedDataPath build \
  CODE_SIGN_STYLE=Automatic \
  DEVELOPMENT_TEAM="<你的 Team ID>" \
  PRODUCT_BUNDLE_IDENTIFIER=com.henge.app
./scripts/package_ipa.sh
# 产物：ios/Henge.ipa
```

---

## 常见问题

| 报错 | 解决 |
|------|------|
| `No signing certificate "iOS Development" found` | 确保 `APPLE_TEAM_ID` secret 正确；免费账号只能用 "iOS Development" 证书，真机安装有效期 7 天。 |
| `xcodegen: command not found` | workflow 已自动 `brew install xcodegen`。 |
| `IPA 太大 / 找不到 Henge.ipa` | 检查 `scripts/package_ipa.sh` 是否把 IPA 输出到 `ios/Henge.ipa`。 |
| 免费私有仓库分钟数用完 | 改公开仓库，或等次月重置（2000 分钟/月）。 |

---

## 关键文件

| 文件 | 作用 |
|------|------|
| `.github/workflows/build-ipa.yml` | 免费 macOS runner 编译流程 |
| `ios/project.yml` | XcodeGen 配置（已含 `developmentLanguage: en`） |
| `ios/scripts/package_ipa.sh` | 打包 IPA 脚本 |
| `ios/Henge/Resources/*.lproj/` | 简体中文 / 英文本地化资源 |
| `ios/Henge/L.swift` | `L.s` / `L.f` 本地化助手 |

---

**一句话**：把仓库推到 GitHub，加上 `APPLE_TEAM_ID` secret，Actions 就能免费帮你产出可在 iPhone SE 3（4 GB）上跑的中文版 Henge IPA。