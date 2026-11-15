【Henge v0.3 交付流水线 · 每轮执行一次】

你是本任务的执行者。本轮目标：推进「Henge v0.3 iOS IPA 交付」流水线，直到 IPA 交付给用户。

## 硬性目标（交付物）
1. 一个可在 iPhone SE 3（4GB RAM / A15）安装运行的 `.ipa`
2. 全量简体中文汉化，无乱码/缺字/排版异常
3. App 内每 5 分钟一轮的后台定时任务（保活 + 异常重试 + 防休眠中断）
4. 4GB 设备的内存优化（512MB JIT 缓存 / 低内存档位 / 启动峰值控制）
5. 部署说明文档

## 当前已知状态（每轮先核实，以实际为准）
- 工作副本：`/var/minis/workspace/henge`（git remote: yoyo520956/Henge，公开仓库）
- 目标仓库分支：`main`
- 重要分支 `se3-low-memory-zh` 含有【内存优化 + 汉化 + 5分钟定时任务的实现】，但 **main 目前落后**，必须把它合并进 main（合并时不要用 `--ours` 丢改动；解决冲突要保留双方语义）
- CI 工作流：`.github/workflows/build-henge.yml`
- runner：`macos-15`（Xcode 16.4）。`macos-14` 已下线，`macos-latest`=macos-26/Xcode 27 会因 SDK 移除 `NSURLHandle.h` 而失败
- StikJIT 必须**在 CI 里用 Xcode 16.4 重建**（`ci/build-stikjit.sh`），上游预编译版是 Xcode 27 产物，Xcode 16 的 Swift 解析不了
- 关键坑（已定位，勿再走弯路）：`BUILD_LIBRARY_FOR_DISTRIBUTION=YES` 会让 Xcode 16.4 生成 `.swiftinterface`，其中 `DDIPaths` 被写成 `StikJIT.DDIPaths`（模块名与枚举名同名），Swift 6.0 解析自己的 interface 就报 `'DDIPaths' is not a member type of enum 'StikJIT.StikJIT'`。已在 `ci/build-stikjit.sh` 改为 `BUILD_LIBRARY_FOR_DISTRIBUTION=NO`
- github.com 常常 SSL 失败，但 api.github.com 正常 → 推送用 `python3 tools/push_file_api.py <远端路径> <本地路径>`（设 `MSG=` 环境变量指定 commit message）；`gh` CLI 的 api 子命令可用

## 本轮工作流
1. **查状态**：`export GH_TOKEN="$GITHUB_TOKEN" && gh run list --repo yoyo520956/Henge --limit 3`
2. **若最近一次 build 成功**：下载 artifact（`gh run download <runId> --repo yoyo520956/Henge -n Henge-ipa-<sha> -D /var/minis/workspace/henge/out`），把 `.ipa` 复制到 `/var/minis/attachments/`，用 Markdown 链接 `[Henge.ipa](minis://attachments/Henge.ipa)` 交付给用户，并附部署说明。若用户已收到可用的 IPA，则转为只做补充验证。
3. **若 build 失败**：`gh run view <runId> --repo yoyo520956/Henge --log-failed` 取错误 → 定位根因 → 修复 → 用 push_file_api.py 推送 → 等待下一轮 CI
4. **若 main 尚未包含汉化/内存优化/定时任务**：把 `se3-low-memory-zh` 合并进 `main` 并推送。注意：合并冲突必须逐个核对语义保留双方；合并后确认 `ios/Henge/LowMemoryProfile.swift`、汉化资源 `ios/Henge/Resources/zh-Hans.lproj/*.strings`、`ios/Henge/L.swift`、5 分钟定时任务实现文件都在 main 上，且 `ios/Henge` 下没有残留英文硬编码（用 `rg` 扫 `Text("` / `Label("` / `Button("` 等模式核对）
5. **每轮结束后**用一句话汇报：这一轮做了什么、当前阻塞点、下一步是什么。不要长篇复盘。

## 5 分钟定时任务的实现要求（若尚未落地）
- 落点：`ios/Henge/` 下新建独立文件，例如 `Heartbeat.swift` / `PeriodicTask.swift`
- 前台/活跃期精确 5 分钟触发一次（`DispatchSourceTimer` 或 `Timer`），后台用 `BGTaskScheduler` 注册兜底
- 每轮执行用 `UIApplication.shared.beginBackgroundTask` 延长存活时间，`endBackgroundTask` 收尾
- 异常重试：指数退避（1s→2s→4s…上限 60s），失败计数，连续失败 N 次后降级并写日志
- 任务内容要服务于 4GB 设备存活：周期性内存体检/清理、日志裁剪、VM 会话健康检查（不要做破坏性操作）
- 用 `HengeLog.log("heartbeat", ...)` 记录每轮，日志可在 App 内查看
- 必须在 `HengeApp.init()` 里启动
- 注意：iOS 不保证后台精确 5 分钟唤醒，代码里要显式处理「被系统推迟」的情况，并如实说明这一点

## 约束
- 不要谎报成功：没验证过的东西不要写成「已完成」
- 不要编造 IPA 已生成，除非 artifact 确实下载成功并校验过（sha256 + zip 结构）
- 24 小时内持续推进；交付完成后做一轮回归验证并把结论写进当日 memory
