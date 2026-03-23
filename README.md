# Video Batch Downloader 全网视频批量下载工具

![icon](https://cdn.jsdelivr.net/gh/hwangzhun/youtube_downloader@main/resources/icons/app_icon_horizontal.png "Video Batch Downloader")

## 简介

Video Batch Downloader（video_bd）是一款基于 Python 开发的免费开源桌面应用程序，采用 PyQt5 构建用户界面，支持 YouTube、TikTok、Twitter/X、Instagram 等主流平台的视频批量下载。

> ⚠️ **说明**：本项目为二次开发版本，基于 [hwangzhun/youtube_downloader](https://github.com/hwangzhun/youtube_downloader) 原始项目进行功能扩展与改进，并非原作者发布的官方版本。感谢原作者的开源贡献。

## 更新日志

### v1.1.0（2026-03-23）
- **重命名**：项目从 `youtube_downloader` 更名为 `video_bd`，扩展为全网视频下载工具。
- **新增**：支持 TikTok 单视频、频道批量下载（如 `https://www.tiktok.com/@user/video/ID`、`https://www.tiktok.com/@user`）。
- **新增**：支持 Twitter/X、Instagram 等平台链接，依赖 yt-dlp 内置解析器。
- **优化**：URL 智能识别，单视频解析失败时自动尝试播放列表/频道展开，展开失败再回退单视频，两种途径均失败才报错。
- **优化**：Cookie 标签页新增"复制名称"和"去下载"按钮，方便快速获取浏览器插件。
- **优化**：针对 Chrome 127+ App-Bound 加密和数据库锁定，提供针对性错误提示与解决方案。
- **优化**：UI 自适应系统 DPI 缩放，高分屏下界面清晰可读。

### v1.0.0（2026-03-22）
- **优化**：合并单视频下载和多视频下载为统一的"视频下载"标签页，合并频道下载功能，操作更简洁直观。
- **新增**：视频下载标签页现支持直接输入频道链接（如 `https://www.youtube.com/@username`），可自动展开全部视频。
- **新增**：菜单栏新增"使用说明"入口，方便用户快速上手。
- **新增**：频道和播放列表的展开结果增加 90 分钟短效本地缓存，重复解析无需重复网络请求。
- **优化**：解析错误时，将弹出可滚动的错误详情弹框，支持全文选中及复制。

> 原始项目（v1.2.0 及以前）的更新日志请参见：[hwangzhun/youtube_downloader - Releases](https://github.com/hwangzhun/youtube_downloader/releases)


## 系统要求

- **操作系统**：Windows 10 或 Windows 11
- **硬盘空间**：至少 200MB 可用空间
- **网络连接**：稳定的互联网连接（访问境外平台需科学上网）
- **JavaScript 运行时**（推荐）：Node.js 或 Deno（用于 YouTube 视频信息提取）

## 支持平台

| 平台 | 单视频 | 播放列表 | 频道/用户主页 |
|------|--------|----------|--------------|
| YouTube | ✅ | ✅ | ✅ |
| TikTok | ✅ | — | ✅ |
| Twitter / X | ✅ | — | — |
| Instagram | ✅ | — | — |
| 其他 yt-dlp 支持站点 | ✅ | 视情况 | 视情况 |

## 主要功能

### 1. 视频下载（统一入口）
- 支持单个视频链接下载
- 支持批量粘贴多个视频链接（每行一个）
- 支持播放列表链接，自动展开列表中的所有视频
- 支持频道/用户主页链接（如 `https://www.youtube.com/@username`、`https://www.tiktok.com/@user`），自动展开全部视频
- URL 智能兜底：单视频解析失败自动尝试展开，展开失败自动回退单视频，双重兜底后才报错
- > ⚠️ 注意：频道链接和播放列表链接建议每次只输入一个
- 支持暂停 / 取消解析进程
- 可同时管理多个下载任务，实时显示每个任务的下载状态和进度

### 2. Cookie 管理
- 支持通过 yt-dlp 从本地浏览器（Chrome、Firefox、Edge 等）自动提取 Cookie
- 支持手动导入 Netscape 格式的 Cookie 文件（推荐插件：Get cookies.txt LOCALLY）
- 针对 Chrome 127+ App-Bound 加密给出针对性解决方案
- Cookie 有效性验证功能

### 3. 代理设置
- 支持配置 HTTP/HTTPS/SOCKS5 代理
- 解决网络访问限制问题
- 代理设置自动保存

### 4. 下载选项
- 自定义下载保存位置
- 支持选择视频清晰度和质量，默认提供最高画质选项
- 优先下载 MP4 格式，必要时自动转换为兼容格式

### 5. 版本管理
- 显示 `yt-dlp` 和 `ffmpeg` 的当前版本及最新版本信息
- 支持一键更新 `yt-dlp` 和 `ffmpeg` 至最新版本
- 自动检测并提示可用更新

## 使用方法

### 视频下载
1. 切换到"视频下载"标签页
2. 将视频、播放列表或频道链接粘贴到输入框中（支持多行，不同平台链接可混用）
3. 根据需要勾选"使用 Cookie"（可选）
4. 设置下载保存位置
5. 选择全局视频和音频质量（可为每个任务单独调整）
6. 点击"解析链接"按钮获取视频信息，频道和播放列表将自动展开
7. 解析完成后，点击"全部开始"按钮批量下载

### Cookie 设置
1. 切换到"Cookie"标签页
2. **方式一（推荐）**：选择浏览器，点击"提取 Cookie"（提取前请完全关闭对应浏览器）
3. **方式二**：安装浏览器插件 `Get cookies.txt LOCALLY`，导出文件后点击"浏览…"手动导入
4. Cookie 设置成功后，可用于下载需要登录或受区域限制的视频

> **Chrome 127+ 用户注意**：Chrome 启用了 App-Bound 加密，建议改用 Firefox 或 Edge 提取，或通过插件手动导出。

### 代理设置
1. 切换到"代理"标签页
2. 选择代理类型（HTTP/HTTPS/SOCKS5）
3. 输入代理服务器地址和端口
4. 如需要，输入用户名和密码
5. 点击"测试连接"验证代理是否可用
6. 点击"保存设置"保存代理配置

### 版本管理
1. 切换到"版本"标签页
2. 查看 `yt-dlp` 和 `ffmpeg` 的当前版本及最新版本信息
3. 若有新版本可用，点击对应"更新"按钮进行升级
4. 更新过程中可查看进度，完成后将显示新版本号

## 注意事项
1. **首次运行**：程序会自动下载 `yt-dlp` 和 `ffmpeg`，请确保网络连接正常
2. **下载时间**：下载高清视频可能需要较长时间，请耐心等待
3. **链接限制**：频道链接和播放列表链接建议每次只输入一个，可与多个单视频链接混用
4. **缓存机制**：频道/播放列表展开结果缓存 90 分钟；单视频信息缓存 24 小时，重复解析无需等待
5. **下载失败**：若下载失败，可尝试以下方法：
   - 使用 Cookie 功能（在"Cookie"标签页设置）
   - 配置代理（在"代理"标签页设置）
   - 选择其他视频质量
   - 检查网络连接
6. **更新工具**：更新 `ffmpeg` 可能需要较长时间，因其文件较大
7. **JavaScript 运行时**（重要）：YouTube 需要 JavaScript 来提取视频信息，建议安装 Node.js 或 Deno：
   - **Node.js**（推荐）：从 [nodejs.org](https://nodejs.org/) 下载并安装最新 LTS 版本
   - **Deno**：从 [deno.land](https://deno.land/) 下载并安装
   - 安装后程序会自动检测并使用，无需额外配置

## 常见问题

### Q1: 为什么无法下载某些视频？
**A**: 可能是由于视频存在地区限制或需要登录。建议尝试使用 Cookie 功能，或配置代理。

### Q2: TikTok 单视频链接解析失败怎么办？
**A**: 程序会自动进行双重尝试（单视频 → 展开 → 再试单视频），若仍失败，建议配置 Cookie 或代理后重试。

### Q3: 为什么下载按钮无法点击？
**A**: 必须设置下载保存位置才能启用下载按钮。

### Q4: 如何获取最佳视频质量？
**A**: 默认情况下，程序会自动选择最高画质。如需特定质量，可从下拉列表中选择。

### Q5: 如何更新 `yt-dlp` 和 `ffmpeg`？
**A**: 在"版本"标签页中点击对应的"更新"按钮即可。

### Q6: 出现 "No supported JavaScript runtime could be found" 错误怎么办？
**A**: 这是因为 YouTube 现在需要 JavaScript 运行时来提取视频信息。请安装以下任一运行时：
- **Node.js**（推荐）：访问 [nodejs.org](https://nodejs.org/) 下载并安装最新 LTS 版本
- **Deno**：访问 [deno.land](https://deno.land/) 下载并安装

安装完成后，确保运行时在系统 PATH 中（通常安装程序会自动配置），然后重启应用程序即可。

### Q7: 如何下载整个频道的视频？
**A**: 在"视频下载"标签页输入框中粘贴频道链接（如 `https://www.youtube.com/@username` 或 `https://www.tiktok.com/@user`），点击"解析链接"，程序将自动展开全部视频并加入下载队列。

### Q8: 如何设置代理？
**A**: 切换到"代理"标签页，选择代理类型，输入代理服务器地址和端口，如需要可输入用户名和密码，点击"测试连接"验证后保存设置即可。

### Q9: Cookie 提取失败怎么办？
**A**:
- **数据库锁定**（"Could not copy Chrome cookie database"）：完全退出浏览器（含托盘进程）后重试
- **Chrome 加密限制**（"Failed to decrypt with DPAPI"）：改用 Firefox 或 Edge 提取，或安装插件 `Get cookies.txt LOCALLY` 手动导出

## 技术支持

若使用过程中遇到问题，请查看应用程序日志文件，路径如下：
- **Windows**: `%APPDATA%\video_bd\logs\`

## 免责声明

本工具仅供个人学习与研究使用，请遵守各平台版权法规及服务条款，勿用于商业用途。用户需自行承担因使用本工具而产生的法律责任。

本项目为二次开发版本，原始项目版权归 [hwangzhun](https://github.com/hwangzhun) 所有，本版本的所有改动仅代表二次开发者的个人行为，与原作者无关。
