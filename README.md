## This is a project based on https://github.com/JoeanAmier/XHS-Downloader.git, which enables users to download posts info when browsing xiaohongshu.

# ⚠️ 免责声明
# 本项目为个人学习与技术验证用途，不涉及任何平台数据抓取或自动化发布行为。使用者应确保所有操作符合《网络安全法》《数据安全法》及相关平台规则，因滥用导致的后果由使用者自行承担。意在培养健康友善的冲浪习惯，为良好健康的网络环境助力，仅供娱乐。
## Motivation：一款基于大语言模型的评论创作辅助工具，帮助用户提升评论质量与创作效率。通过预设人格与上下文学习，生成符合网络文明规范的友善评论，严禁用于任何形式的自动化发布、商业营销或数据爬取。
## 使用方法：
### 1. XHS-Downloader_V2.4_Windows_X64，运行main，设置好下载目录，并打开软件监听模式
![image](https://github.com/user-attachments/assets/317b7dc6-0f4f-467e-83ae-ce6147ea76b1)
### 2. 浏览小红书，对感兴趣的帖子点击分享按钮，软件将自动下载帖子相关信息
### 3. 浏览一定数量帖子后，运行comment.py
注：脚本的评论生成基于LLM的api调用，项目提供了一个demo包含可用的api，请勿滥用
### 4.使用系统浏览帖子摘要并调整评论，
### 5.每次生成3条候选评论，必须经用户手动选择与修改后才可复制使用
![image](https://github.com/user-attachments/assets/e7400569-45f7-4e89-aa34-a1cbe705bcb8)
![image](https://github.com/user-attachments/assets/cddcc35d-3ecd-4e2c-a794-3d1e78358f05)
![image](https://github.com/user-attachments/assets/1793b8ba-f665-4e88-ab8f-d135653cb654)
![image](https://github.com/user-attachments/assets/a43c317f-223d-4103-aa8a-687cb52ff3c0)
相关功能可自行探索，目前还不支持读取图片

开发者声明

数据安全：所有输入内容仅暂存于本地内存，关闭程序后自动清除

禁止行为清单：

❌ 绕过平台内容审核机制

❌ 批量生成相同/相似评论

❌ 用于商业推广或虚假流量制造


3月5日更新： 重新生成评论时可以选择3中预设人格了。支持自定义人格

3月7日更新： 使用了 In Context Learning，通过 3 shots learning 提高评论质量与输出稳定性；现在每次生成3条备选评论供用户选择；提出了一种基于大模型的选择困难症治疗方案，现在可以自动选择人格了。 修复了很多bug。
