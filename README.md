<p align="center">
  <img src="docs/icon.png" width="120" height="120" alt="Henge">
</p>

<h1 align="center">Henge</h1>

<p align="center">macOS on your iPhone and iPad.</p>

<p align="center">
  <a href="#install">Install</a>
  ·
  <a href="docs/architecture.md">How it works</a>
  ·
  <a href="https://github.com/yoyo520956/Henge/releases">Releases</a>
  ·
  <a href="#this-fork">这个版本做了什么</a>
</p>

<p align="center">
  <a href="https://github.com/yoyo520956/Henge/releases"><img src="https://img.shields.io/github/downloads/yoyo520956/Henge/total?style=flat-square&color=2E6BFF&labelColor=111111" alt="Downloads"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/yoyo520956/Henge?style=flat-square&color=2E6BFF&labelColor=111111" alt="GPL-2.0-or-later"></a>
</p>

Download macOS, install it on the device, and use it.

- **Own emulator** — iOS gives apps no hypervisor, so Henge runs the Mac's arm64 code through its own JIT, with its own MMU and devices. It doesn't use QEMU or Virtualization.framework.
- **Installs on the device** — Henge downloads Apple's restore image and restores it the way a Mac does. No Mac needed, and nothing is decrypted or patched.
- **Graphics** — macOS draws through a virtual GPU, and Henge replays its commands with Metal. Safari and Electron apps like Discord draw on it.
- **Touch** — The screen is a Magic Trackpad 2: two fingers to scroll, and the Mac's own gestures work on it — three-finger swipes for Spaces and Mission Control and more. The volume buttons are its buttons: up clicks, down right-clicks, hold to drag. Esc, Tab, Control, Option and Command sit above the keyboard.
- **Keyboard and mouse** — On iPad, a Magic Keyboard or a Bluetooth keyboard and mouse drive the Mac directly.
- **External display** — During a Mac session, connect a display with a video-capable USB-C cable or a USB-C/HDMI dock. The mode activates automatically: the monitor shows the Mac, while the iPhone or iPad keeps its trackpad and keyboard controls. Disconnect to return the image to the device. The existing guest resolution is preserved. On iOS 17–26 the same happens through an older iOS route, not yet tried on hardware; outside a Mac session the display mirrors the device. USB-C video is user-confirmed on an iPhone 17 Pro running iOS 27 (development build 0.1/2).
- **Sharing** — Copy and paste between macOS and the device, and a shared folder that shows up in Files and on the Mac.
- **Fits the screen** — On iPad, a new Mac gets a screen the shape of the iPad's, so there are no black bars. On an iPhone it goes further: the Mac is drawn at the phone's own point size, so its icons and fonts are the size the phone's own are, not a desktop shrunk to fit.

On an iPhone 17 Pro, macOS reaches the lock screen in about 15 seconds. Discord installs, opens in about 15 seconds, logs in and sends messages.

## 这个版本做了什么

这是 [Leviidev/Henge](https://github.com/Leviidev/Henge) 的修改版（GPL-2.0 允许任何人下载、修改、再分发，`LICENSE` 见上游条款）。除上游功能外，它针对**小内存 iPhone（4GB）**做了可用性改造，并把界面完整译为**简体中文**：

- **参数按设备定死**：4GB 设备固定 2 个虚拟 CPU + 3GB 内存（guest 用文件承载，iOS 不把它计入 App 限额）+ 30Hz + 512MB 代码缓存，并关闭空闲 CPU 自旋。设置界面里不可再调，每次启动都按这个来。
- **CPU 少反而更快**：每个虚拟 CPU 是真实线程，空闲自旋在多核时每个核都在烧 CPU；2 核让显示和 JIT 拿回本该属于它们的时间。
- **屏幕按手机适配**：iPhone 上 Mac 以「与 iPhone 相同的点尺寸」绘制（Retina 2x），图标、菜单、字体与 iPhone 原生大小一致，画面正好铺满屏幕，不再是被缩小到三分之一的样子。
- **轻量化脚本**：Mac 里一条命令关掉窗口/Dock 动画、桌面小组件、屏幕保护程序、动态壁纸、软件更新检查与 App Store 自动更新，并给出把磁盘排除出 Spotlight 索引的办法（这一步最省内存）。
- **后台心跳**：每 5 分钟检查 Henge 自身、Mac 的内存占用并裁剪日志，降低 4GB 设备上被 iOS 杀后台的概率。
- **简体中文**：全部界面 429 条文案，包括心跳设置与安装说明。

**兼容性**：本仓库的预编译 IPA 只在 iPhone SE 3（4GB / A15）上实测过。iPhone 17 Pro、iPad 请直接使用[上游发布版](https://github.com/Leviidev/Henge/releases)，或从本仓库自行构建。本仓库只提供源码与自建产物，不提供 Apple 的 restore image（安装时由 Henge 自行从 Apple 下载）。

## Install

Sideload `Henge.ipa` from [Releases](https://github.com/Leviidev/Henge/releases) with SideStore or AltStore, or install `Henge.tipa` with TrollStore or TrollStore Lite. To get updates in SideStore or AltStore, add Henge's source, `https://raw.githubusercontent.com/Leviidev/Henge/main/repo.json`, or `https://itslevii.dev/repo.json` for all of Leviidev's apps. iOS or iPadOS 17 or later, on an A14 or M1 chip or newer. So far it's tested only on an iPhone 17 Pro: iPad support is new and hasn't run on a real iPad yet.

- **JIT** is required: StikDebug, TrollStore (which stops at iOS 17.0), TrollStore Lite (which needs a jailbreak), a jailbreak on its own, or the StikJIT helper built into Henge (iOS 26 or later).
- **Storage:** about 43 GB free for macOS Sequoia. That's 17 GB for the download, which you can delete afterwards, and 26 GB for the Mac.
- **Memory:** the device decides, not you: a 4 GB phone gets a 3 GB Mac on 2 virtual CPUs, an 8 GB device a 6 GB one, and so on (see `PerformancePlan` in the source). A guest larger than the phone's spare RAM is backed by a file, whose pages iOS does not count against the app's limit. Sign Henge with the increased memory limit entitlement if your certificate has it.

Then open the Install tab, pick macOS Sequoia 15.6.1, and keep Henge open with the device plugged in. Tahoe 26.6.2 and macOS 27.2 are offered too: both install and run on an iPhone 17 Pro, though Tahoe's first setup is slow and macOS 27 is the slowest (Safari's pages may stay blank on it). Sonoma 14.6.1 and Ventura 13.6 are smaller downloads (14.1 and 12.3 GB) for devices short on storage: they install, set up, and run Safari (both tested on an iPhone 17 Pro). Monterey isn't offered yet: it installs, but its desktop never appears.

## Sharing with the Mac

Do this once for each Mac: open Terminal on the Mac, then in Henge open Details and tap **Type the Set Up Command**. Press Return on the Mac, and choose Allow when macOS asks about `henge-agent` and local networks. It needs the Mac's keyboard layout to be U.S.

Then a Henge folder in the Mac's home folder is the same folder as Files › Henge › Shared. What you copy on the Mac is copied on the device too, and the paste button pastes from the device into the Mac.

## Known limits

- Signing in to an Apple Account inside macOS fails with a verification error.
- Graphics are tested on macOS's own apps, Chrome, Firefox, VS Code and Discord. Other apps may draw wrongly.
- On macOS Sonoma, switching to a dynamic wallpaper (such as Sonoma) can stop the screen updating; opening any app brings it back. On Ventura, the Calendar icon in the Dock is missing its date.
- For the first few minutes after you log in, macOS is busy starting up in the background, so apps open more slowly.
- Only one Mac can start per launch. Quit Henge and open it again to start another, and to start one again after restarting or shutting down macOS.
- iPadOS keeps some keyboard shortcuts for itself, such as Command-Tab.
- It's emulation, so it runs slower than a real Mac.

## Screenshots

<table>
  <tr>
    <td align="center" colspan="3"><img src="Screenshots/ipad.jpg" alt="Discord on an iPad"><br><sub>iPad</sub></td>
  </tr>
  <tr>
    <td align="center" width="33%"><img src="Screenshots/macs.png" alt="Macs"><br><sub>Macs</sub></td>
    <td align="center" width="33%"><img src="Screenshots/trackpad.png" alt="Trackpad"><br><sub>Trackpad</sub></td>
    <td align="center" width="33%"><img src="Screenshots/install.png" alt="Install macOS"><br><sub>Install macOS</sub></td>
  </tr>
</table>

<sub>Captured on a Mac: the app's own screens with sample data, at iPad and iPhone sizes, showing a frame from Henge's renderer.</sub>

## Building

To use Henge, install the [latest release](https://github.com/Leviidev/Henge/releases). Every change lands on `main` as it's made, so `main` can be unfinished between releases.

On a Mac with Xcode 27 or later and `xcodegen`. Henge takes StikJIT, on-device pairing, libslirp and glib from a built [Husk](https://github.com/Leviidev/Husk) checkout at `~/Documents/Coding/Husk` (set `HUSK` to use another path):

```bash
ios/scripts/fetch_deps.sh
tools/build_ios_restore.sh
make ios-lib
ios/scripts/package_ipa.sh
```

That produces `~/Desktop/Henge.ipa`, and `package_ipa.sh --trollstore` writes `Henge.tipa`.

`make` builds the engine for the Mac, `build/hengevm`, and `make test` runs its tests.

## Licence

GPL-2.0-or-later. Henge compiles in usbmuxd (GPLv2 or GPLv3) and code from Husk (GPL-2.0-or-later), so the shipped binary is a combined GPL work. It cannot go on the App Store. See [docs/licensing.md](docs/licensing.md).

macOS and the Mac's boot ROM are Apple's and aren't part of Henge. Henge downloads both from Apple when you install.
