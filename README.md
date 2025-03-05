## This is a project based on https://github.com/JoeanAmier/XHS-Downloader.git, which enables users to download posts info when browsing xiaohongshu.

# 此项目是一个自动管理小红书评论以及基于大模型生成评论的管理系统，主要用于方便快捷大量生成评论。意在培养健康友善的冲浪习惯，为良好健康的网络环境助力，仅供娱乐。
## Motivation： 最初打算做一个全自动评论脚本，但由于平台政策与相关法律法规，以及小红书对爬虫与自动脚本的限制，现在需要手动浏览网页与手动评论。
## 使用方法：
### 1. XHS-Downloader_V2.4_Windows_X64，运行main，设置好下载目录，并打开软件监听模式
![image](https://github.com/user-attachments/assets/317b7dc6-0f4f-467e-83ae-ce6147ea76b1)
### 2. 浏览小红书，对感兴趣的帖子点击分享按钮，软件将自动下载帖子相关信息
### 3. 浏览一定数量帖子后，运行comment.py，脚本将自动读取数据库信息并生成评论
注：脚本的评论生成基于LLM的api调用，项目提供了一个demo包含可用的api，请勿滥用
### 4.使用系统浏览帖子摘要并调整评论
### 5.手动复制评论并记录在系统中
![image](https://github.com/user-attachments/assets/e7400569-45f7-4e89-aa34-a1cbe705bcb8)
![image](https://github.com/user-attachments/assets/cddcc35d-3ecd-4e2c-a794-3d1e78358f05)
![image](https://github.com/user-attachments/assets/1793b8ba-f665-4e88-ab8f-d135653cb654)
![image](https://github.com/user-attachments/assets/a43c317f-223d-4103-aa8a-687cb52ff3c0)
相关功能可自行探索，目前还不支持读取图片
