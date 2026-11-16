# Henge v0.3 — iPhone SE 3（4GB）安装与使用说明

本包是 Henge 的 iOS 版本，针对 **iPhone SE 3（A15 / 4GB RAM）** 做了内存优化与
全量简体中文本地化，并内置了一个每 5 分钟运行一次的后台心跳任务。

---

## 一、这个包做了什么

| 项目 | 说明 |
|---|---|
| 内存优化 | 4GB 设备自动进入「低内存」档：JIT 代码缓存 512 MB、显示刷新率 30 Hz、安装器临时 Mac 上限 2 GB |
| 低内存档位 | 设置 → 内存配置，可手动选「自动 / 低内存 / 平衡 / 性能」 |
| 简体中文 | 界面全量汉化（429 条词条），含 Info.plist 权限描述 |
| 五分钟心跳 | 每 5 分钟检查一次 Henge 自身内存、运行中 Mac 的内存和日志；日志超过 8 MB 自动裁剪到 4 MB |
| 保活 | 每轮心跳用 `beginBackgroundTask` 申请后台执行窗口；回到前台自动重新计时 |
| 异常重试 | 心跳失败按 1s→2s→4s…（上限 60s）指数退避重试，失败计数写入日志 |

---

## 二、安装步骤

### 前提

- iPhone SE 3，iOS 17 或更高
- 一个 Apple ID（免费账号即可，签名有效期 7 天，到期需重签）
- 电脑或云端签名工具（Sideloadly / AltStore / SideStore / TrollStore 等）

### 用 Sideloadly（最简单，免费）

1. 电脑安装 [Sideloadly](https://sideloadly.io/)
2. 用数据线连接 iPhone，在手机上点「信任此电脑」
3. 把 `.ipa` 拖进 Sideloadly 窗口
4. 填入你的 Apple ID 和密码（Apple 会在手机上发验证码，按提示输入）
5. 点 **Start** 等待签名安装

### 用 AltStore / SideStore（可自动续签）

1. 电脑上安装 AltStore 或 SideStore
2. 添加你的 Apple ID
3. 把 `.ipa` 加入 AltStore 队列，在 iPhone 上打开 AltStore → My Apps → `+` 选择文件
4. 保持电脑上的 AltServer 运行，7 天后会自动续签

### 用 TrollStore（永久安装，仅限部分系统版本）

TrollStore 只支持 iOS 14–16.6.1 / 16.7 RC / 17.0，**iOS 17.0.1 以上不兼容**。
如果你的设备在支持范围内，可以直接安装，签名永久有效。

---

## 三、首次使用

### 1. 安装 macOS

打开 Henge → **安装** 标签页 → 选择要装的 macOS 版本 → 开始下载。

> ⚠️ **4GB 设备的建议**：装 **macOS 13.6**。系统越新、后台服务越多，对 4GB 内存的
> iPhone 压力越大。13.6 是当前可选版本里对低内存设备最友好的。

下载需要保持 App 在前台且设备联网，整个过程可能 1–3 小时。**中途不要切后台**。

### 2. 开启 JIT（必需）

macOS 运行需要 JIT 权限，Henge 通过 StikDebug 或内置 StikJIT 获取：

- 设置 → JIT → 选择方法：
  - **内置 StikJIT（推荐）**：导入配对文件后点「准备 JIT」
  - **StikDebug**：需先在手机上安装 StikDebug
  - **等待调试器**：最兼容但需要电脑端工具
- 需要开启手机的**开发者模式**（设置 → 隐私与安全性 → 开发者模式）
- 需要已连接 **LocalDevVPN**
- 配对文件放到 App 文档目录的 `StikJIT/pairingFile.plist`

### 3. 启动 Mac

回到 **Macs** 标签页 → 点 Mac 的「开始」→ 进入桌面。

4GB 设备建议在设置 → 内存配置里选「低内存」，并在安装时选 **2GB** 的 Mac 内存。

---

## 四、关于「每 5 分钟一次」的定时任务

### 它做什么

每 5 分钟，Henge 在后台执行一轮：

1. 记录 Henge 进程当前物理内存占用（`phys_footprint`）
2. 记录运行中 Mac 被分配的内存
3. 记录虚拟机状态
4. 检查日志文件大小，超过 8 MB 时裁剪，只保留最后 4 MB
5. 把这一轮的结果写入 `henge.log`

在「设置 → 心跳」里可以看到检查间隔、已检查次数和最近一轮的详细数据。

### 它的实际触发条件（重要）

iOS **不会**保证后台 App 在指定时间被唤醒。这是系统级限制，任何 App 都绕不过去。

| Henge 状态 | 触发精度 |
|---|---|
| 前台运行 | **精确 5 分钟**（`DispatchSourceTimer`，回到前台会自动重新计时） |
| 后台 / 锁屏 | **尽力而为**（`BGTaskScheduler`，系统决定何时给窗口，通常会推迟） |
| 被系统完全回收 | 不运行；下次打开 App 时补上 |

真正需要精确间隔的场景是「Mac 正在跑」的时候——那正是 Henge 在前台的场景，也是内存最紧张的场景。所以这个设计覆盖了实际需要。

日志里会如实记录每一轮的时间戳，间隔异常时一看就知道是被系统推迟了。

---

## 五、常见问题

**Q：App 被 iOS 关闭了（闪退）？**
A：4GB 设备上这通常是 jetsam 杀进程。请检查：设置 → 内存配置是否选「低内存」；Mac 内存是否 ≤ 2 GB；关闭其他占用内存的 App；日志文件（Documents/henge.log）里的 `heartbeat` 记录能看出内存涨到了哪里。

**Q：安装 macOS 过程中 App 被杀了？**
A：低内存档已经把安装器临时 Mac 压到 2 GB。如果仍然被杀，把「内存配置」改成「低内存」并重试，同时关掉后台 App。

**Q：JIT 开启失败？**
A：按顺序检查：开发者模式是否开启 → LocalDevVPN 是否连接 → 配对文件是否已导入 → iOS 版本是否 ≥ 17.4（内置 StikJIT 要求）。StikDebug 的报错更明确，优先用它排查。

**Q：界面有英文？**
A：设置 → 通用 → 语言与地区 → 设为「简体中文」，然后完全退出并重开 Henge。

**Q：签名能用多久？**
A：免费 Apple ID 签名 7 天。AltStore / SideStore 在电脑在线时可自动续签。付费开发者账号 1 年。

---

## 六、日志与问题反馈

App 内可查看实时日志。文件位置：

```
Henge/Documents/henge.log          ← 本次运行
Henge/Documents/henge-prev.log      ← 上一次运行（崩溃时看这个）
Henge/Documents/henge-native.log   ← 引擎的原始输出
```

分享日志时建议三个一起带上。
