import json
import os
from datetime import datetime
import time
import sqlite3
from openai import OpenAI
import random
from prompt_manager import PromptManager, PromptTemplate
import re



class CommentManager:
    def __init__(self):
        self.comments_file = "xhs_comments.json"
        self.db_path = 'download/ExploreData.db'
        self.prompt_manager = PromptManager()
        self.load_comments()
        self.update_posts_from_db()
        self.setup_ai()
        self.auto_generate_comments()

    def setup_ai(self):
        """设置AI配置"""
        os.environ["OPENAI_API_KEY"] = "sk-saoyuxaudkkvxnqyfeoonpagqrnoqomyazphdbzqaraahdwi"   #ds: "sk-saoyuxaudkkvxnqyfeoonpagqrnoqomyazphdbzqaraahdwi" # gpt "sk-mTLkf5SuDNKW2B1D5xQbDljybrG37LVxVQyIDwTz1io9l1iX"
        os.environ["OPENAI_BASE_URL"] =  "https://api.siliconflow.cn/v1"                       #ds  "https://api.siliconflow.cn/v1"  gpt # "https://api.bianxie.ai/v1"
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def generate_comment(self, post_data):
        """使用ChatGPT生成评论 - 已弃用，请使用 generate_comment_with_personality"""
        return self.generate_comment_with_personality(post_data)

    def generate_comment_with_prompt(self, post_data, base_idea=None):
        """使用ChatGPT生成评论 - 已弃用，请使用 generate_comment_with_personality"""
        return self.generate_comment_with_personality(post_data, base_idea=base_idea)

    def display_menu(self):
        """显示主菜单"""
        try:
            while True:
                print("\n" + "="*80)
                print("评论管理系统")
                print("="*80)
                print("\n选择功能:")
                print("1. 查看所有帖子")
                print("2. 查看未评论帖子")
                print("q. 退出程序")
                
                choice = input("\n请选择功能 (1/2/q): ").strip().lower()
                
                if choice == 'q':
                    print("\n退出程序...")
                    break
                elif choice == '1':
                    self.display_all_posts()
                elif choice == '2':
                    self.process_unsent_posts()
                else:
                    print("\n❌ 无效的选择，请重试")

        except Exception as e:
            print(f"操作过程中出错: {str(e)}")

    def display_all_posts(self):
        """显示所有帖子"""
        posts = self.get_all_comments()
        if not posts:
            print("\n没有帖子记录")
            return

        print(f"\n找到 {len(posts)} 条帖子")
        print("\n查看模式:")
        print("1. 逐个查看")
        print("2. 查看全部")
        mode = input("\n请选择查看模式 (1/2): ").strip()

        if mode not in ['1', '2']:
            print("\n❌ 无效的选择，返回主菜单")
            return

        print("\n" + "="*80)
        
        # 显示所有帖子
        for post_id, post_data in posts.items():
            status = "✅ 已评论" if post_data.get("is_sent", False) else "⏳ 未评论"
            sent_time = post_data.get("sent_time", "未评论")
            
            print(f"\n📝 帖子信息: ({status})")
            print(f"帖子ID: {post_id}")
            print(f"评论状态: {status}")
            print(f"评论时间: {sent_time}")
            print(f"作者主页: {post_data['author_url']}")
            print(f"帖子标题: {post_data['title']}")
            description = post_data.get('description', '')
            if len(description) > 50:
                description = description[:50] + "..."
            print(f"帖子描述: {description}")
            if post_data.get('comment'):
                print(f"评论内容: {post_data['comment']}")
            print("-"*80)
            
            # 只在逐个查看模式下提供操作选项
            if mode == '1':
                while True:
                    print("\n操作选项:")
                    print("1. 重新生成评论")
                    print("2. 标记为未评论")
                    if not post_data.get("is_sent", False):
                        print("3. 进入未评论处理模式")
                    print("n. 查看下一条")
                    print("q. 退出到主菜单")
                    
                    choice = input("\n请选择操作: ").strip().lower()
                    
                    if choice == 'q':
                        return
                    elif choice == 'n':
                        break
                    elif choice == '1':
                        while True:
                            comment = self.generate_comment_with_personality(post_data)
                            if comment:
                                print(f"\n生成的评论: {comment}")
                                print("\n请选择操作:")
                                print("1. 接受这条评论")
                                print("2. 重新生成")
                                print("3. 拒绝并返回")
                                
                                sub_choice = input("\n请选择 (1/2/3): ").strip()
                                
                                if sub_choice == '1':
                                    self.add_comment(post_id, comment)
                                    print("\n✅ 已保存评论")
                                    break
                                elif sub_choice == '2':
                                    continue
                                elif sub_choice == '3':
                                    break
                                else:
                                    print("\n❌ 无效的选择，请重试")
                            else:
                                print("\n❌ 评论生成失败")
                            break
                    elif choice == '2':
                        self.mark_comment_unsent(post_id)
                        print("\n✅ 已标记为未评论")
                        break
                    elif choice == '3' and not post_data.get("is_sent", False):
                        self.process_single_unsent_post(post_id, post_data)
                        break
                    else:
                        print("\n❌ 无效的选择，请重试")

        # 在查看全部模式下，显示完所有帖子后等待用户确认
        if mode == '2':
            print("\n已显示所有帖子")
            input("按回车键返回主菜单...")

    def process_unsent_posts(self):
        """处理未评论帖子"""
        unsent_posts = self.get_unsent_comments()
        if not unsent_posts:
            print("\n没有未评论的帖子")
            return

        print(f"\n找到 {len(unsent_posts)} 条未评论帖子")
        
        for post_id, post_data in unsent_posts.items():
            result = self.process_single_unsent_post(post_id, post_data)
            if result == 'quit':
                break
            elif result == 'next':
                continue

    def process_single_unsent_post(self, post_id, post_data):
        """处理单个未评论帖子"""
        print("\n" + "="*80)
        print("📝 当前帖子信息:")
        print(f"帖子ID: {post_id}")
        print(f"作者主页: {post_data['author_url']}")
        print(f"帖子标题: {post_data['title']}")
        description = post_data.get('description', '')
        if len(description) > 50:
            description = description[:50] + "..."
        print(f"帖子描述: {description}")
        if post_data.get('comment'):
            print(f"当前评论: {post_data['comment']}")
            if post_data.get('last_base_idea'):
                print(f"上次使用的观点: {post_data['last_base_idea']}")
        print("-"*80)
        
        while True:
            print("\n操作选项:")
            if not post_data.get('comment'):
                print("1. 生成评论")
            else:
                print("1. 重新生成评论")
            print("2. 标记为已评论并继续")
            print("n. 跳过当前帖子")
            print("q. 退出到主菜单")
            
            choice = input("\n请选择操作 (1/2/n/q): ").strip().lower()
            
            if choice == 'q':
                return 'quit'
            elif choice == 'n':
                return 'next'
            elif choice == '1':
                self.process_comment_generation(post_id, post_data)
            elif choice == '2':
                self.mark_comment_sent(post_id)
                print("\n✅ 已标记为已评论")
                return 'next'
            else:
                print("\n❌ 无效的选择，请重试")

    def load_comments(self):
        """从JSON文件加载评论数据"""
        try:
            if os.path.exists(self.comments_file):
                with open(self.comments_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                print(f"\n📝 已加载评论数据文件")
            else:
                self.data = {
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "posts": {}
                }
                print(f"\n📝 创建新的评论数据文件")
        except Exception as e:
            print(f"\n❌ 加载评论数据失败: {str(e)}")
            self.data = {
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "posts": {}
            }

    def save_comments(self):
        """保存评论数据到JSON文件"""
        self.data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.comments_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def is_comment_generated(self, post_id):
        """检查帖子是否已生成评论"""
        return post_id in self.data["posts"] and self.data["posts"][post_id]["comment"] is not None

    def is_comment_sent(self, post_id):
        """检查评论是否已发送"""
        return (post_id in self.data["posts"] and 
                self.data["posts"][post_id].get("is_sent", False))

    def add_post(self, post_info):
        """添加新帖子信息"""
        post_id = post_info['id']
        if post_id not in self.data["posts"]:
            self.data["posts"][post_id] = {
                "title": post_info['title'],
                "description": post_info['description'],
                "author": post_info['author'],
                "author_url": post_info['author_url'],
                "tags": post_info['tags'],
                "comment": None,
                "is_generated": False,
                "generated_time": None,
                "is_sent": False,
                "sent_time": None
            }
            self.save_comments()

    def add_comment(self, post_id, comment, base_idea=None):
        """添加评论，可选择保存基本观点"""
        if post_id in self.data["posts"]:
            self.data["posts"][post_id].update({
                "comment": comment,
                "is_generated": True,
                "generated_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_base_idea": base_idea  # 保存基本观点
            })
            self.save_comments()

    def mark_comment_sent(self, post_id):
        """标记评论已发送"""
        if post_id in self.data["posts"]:
            self.data["posts"][post_id].update({
                "is_sent": True,
                "sent_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            self.save_comments()

    def get_unsent_comments(self):
        """获取未发送的评论"""
        return {
            post_id: post_data
            for post_id, post_data in self.data["posts"].items()
            if not post_data.get("is_sent", False)
        }

    def get_all_comments(self):
        """获取所有评论"""
        return self.data["posts"]

    def get_pending_posts(self):
        """获取待生成评论的帖子"""
        return {
            post_id: data for post_id, data in self.data["posts"].items()
            if not data.get("is_generated")
        }

    def _display_comments_list(self, comments, status_text):
        """显示评论列表"""
        if not comments:
            print(f"\n没有{status_text}的评论")
            return

        print(f"\n找到 {len(comments)} 条{status_text}评论")
        print("\n" + "="*80)
        
        # 创建编号映射
        numbered_comments = list(comments.items())
        
        # 显示带编号的评论列表
        for idx, (post_id, post_data) in enumerate(numbered_comments, 1):
            status = "✅ 已发送" if post_data.get("is_sent", False) else "⏳ 未发送"
            sent_time = post_data.get("sent_time", "未发送")
            
            print(f"\n[{idx}] 帖子信息: ({status})")
            print(f"帖子ID: {post_id}")
            print(f"发送状态: {status}")
            print(f"发送时间: {sent_time}")
            print(f"作者主页: {post_data['author_url']}")
            print(f"帖子标题: {post_data['title']}")
            description = post_data.get('description', '')
            if len(description) > 50:
                description = description[:50] + "..."
            print(f"帖子描述: {description}")
            print(f"评论内容: {post_data['comment']}")
            print("-"*80)
            
            # 保存当前显示的帖子ID，用于鼠标右键标记
            self.current_displayed_post = post_id

    def mark_comment_unsent(self, post_id):
        """标记评论为未发送"""
        if post_id in self.data["posts"]:
            self.data["posts"][post_id]["is_sent"] = False
            self.data["posts"][post_id]["sent_time"] = None
            self.save_comments()

    def process_comment_generation(self, post_id, post_data):
        """处理评论生成过程"""
        while True:
            # 一级菜单：显示所有可用人格
            personalities = self.prompt_manager.get_personality_names()
            print("\n请选择评论人格:")
            for idx, (key, desc) in enumerate(personalities.items(), 1):
                print(f"{idx}. {desc}")
            print(f"{len(personalities) + 1}. 自定义人格")
            print("q. 返回上级菜单")
            
            choice = input(f"\n请选择 (1-{len(personalities) + 1}/q): ").strip().lower()
            
            if choice == 'q':
                return
            
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(personalities):
                    # 选择预设人格
                    personality_key = list(personalities.keys())[choice_num - 1]
                    personality_template = self.prompt_manager.get_prompt_template(personality_key)
                    if self.handle_generation_with_template(post_id, post_data, personality_template):
                        return  # 如果评论被接受，直接返回上级菜单
                    
                elif choice_num == len(personalities) + 1:
                    # 自定义人格
                    custom_template = self.create_custom_personality()
                    if custom_template:
                        if self.handle_generation_with_template(post_id, post_data, custom_template):
                            # 询问是否保存自定义人格
                            if input("\n是否保存这个人格配置？(y/n): ").strip().lower() == 'y':
                                name = input("请为这个人格配置起一个唯一的标识符(英文): ").strip()
                                self.prompt_manager.add_personality(name, custom_template)
                                print("\n✅ 人格配置已保存")
                            return  # 评论被接受后直接返回上级菜单
                else:
                    print("\n❌ 无效的选择")
                    continue
                
            except ValueError:
                print("\n❌ 请输入有效的数字")
                continue

    def create_custom_personality(self):
        """创建自定义人格"""
        print("\n=== 创建自定义人格 ===")
        print("以下是理中客人格的示例，请参考格式创建您的自定义人格。")
        
        try:
            print("\n【人格名称示例】")
            print("理中客")
            print("- 简短且具有代表性的名称")
            name = input("\n请输入人格名称: ").strip()
            if not name:
                print("❌ 名称不能为空")
                return None
            
            print("\n【人格描述示例】")
            print("基于事实，客观分析，有理有据")
            print("- 描述这个人格的主要特点和说话风格")
            description = input("\n请输入人格描述: ").strip()
            if not description:
                print("❌ 描述不能为空")
                return None
            
            print("\n【系统提示词示例】")
            print("你是一个理性客观的评论员，善于分析事物的本质，提供有理有据的见解。")
            print("- 用于设定AI的基础人格")
            print("- 建议包含身份定位和行为特征")
            system_prompt = input("\n请输入系统提示词: ").strip()
            if not system_prompt:
                print("❌ 系统提示词不能为空")
                return None
            
            print("\n【用户提示词模板示例】")
            print("""请直接输出一条针对这篇小红书帖子的评论，不要解释思考过程。要求：
1. 评论客观理性，有理有据
2. 从多个角度分析问题
3. 评论可以稍长，但不超过50字
4. 使用专业但通俗的语言

帖子信息：
标题：{title}
描述：{description}
标签：{tags}""")
            print("\n- 必须包含 {title}、{description}、{tags} 这些占位符")
            print("- 明确指出评论的具体要求")
            user_prompt = input("\n请输入用户提示词模板: ").strip()
            if not user_prompt:
                print("❌ 用户提示词模板不能为空")
                return None
            
            # 验证用户提示词模板是否包含必要的占位符
            required_placeholders = ['{title}', '{description}', '{tags}']
            missing_placeholders = [p for p in required_placeholders if p not in user_prompt]
            if missing_placeholders:
                print(f"\n❌ 用户提示词模板缺少以下占位符: {', '.join(missing_placeholders)}")
                return None
            
            print("\n=== 人格配置预览 ===")
            print(f"名称: {name}")
            print(f"描述: {description}")
            print(f"系统提示词: {system_prompt}")
            print(f"用户提示词模板: {user_prompt}")
            
            if input("\n确认创建这个人格配置？(y/n): ").strip().lower() != 'y':
                print("\n已取消创建")
                return None
            
            return PromptTemplate(
                name=name,
                description=description,
                system_prompt=system_prompt,
                user_prompt_template=user_prompt
            )
            
        except Exception as e:
            print(f"\n❌ 创建自定义人格失败: {str(e)}")
            return None

    def handle_generation_with_template(self, post_id, post_data, personality_template):
        """使用指定模板处理评论生成"""
        while True:
            print("\n请选择生成方式:")
            print("1. 直接生成评论")
            print("2. 输入基本观点后生成")
            print("q. 返回上级菜单")
            
            sub_choice = input("\n请选择 (1/2/q): ").strip().lower()
            
            if sub_choice == 'q':
                return False
                
            base_idea = None
            if sub_choice == '2':
                base_idea = input("\n请输入您的基本观点: ").strip()
                if not base_idea:
                    print("\n❌ 观点不能为空")
                    continue
            elif sub_choice != '1':
                print("\n❌ 无效的选择")
                continue
            
            comment = self.generate_comment_with_personality(
                post_data,
                base_idea=base_idea,
                personality_template=personality_template
            )
            
            if comment:
                print(f"\n生成的评论: {comment}")
                print("\n请选择操作:")
                print("1. 接受这条评论")
                print("2. 重新生成")
                print("3. 拒绝并返回")
                
                action = input("\n请选择 (1/2/3): ").strip()
                
                if action == '1':
                    self.add_comment(post_id, comment, base_idea)
                    print("\n✅ 已保存评论")
                    return True  # 返回 True 表示评论已被接受
                elif action == '2':
                    continue  # 继续生成新的评论
                elif action == '3':
                    return False  # 返回 False 表示用户拒绝了评论
                else:
                    print("\n❌ 无效的选择")
            else:
                print("\n❌ 评论生成失败")
                return False

    def generate_comment_with_personality(self, post_data, base_idea=None, personality_template=None):
        """使用指定人格生成评论"""
        tags = post_data.get('tags', [])
        if isinstance(tags, str):
            tags = tags.split('#')
        tags = [tag.strip() for tag in tags if tag.strip()]
        
        if personality_template:
            system_prompt = personality_template.system_prompt
            user_prompt = personality_template.format_prompt(
                title=post_data.get('title', ''),
                description=post_data.get('description', ''),
                tags=' '.join(tags),
                base_idea=base_idea
            )
        else:
            # 使用默认的理中客人格
            personality_template = self.prompt_manager.get_prompt_template('rational')
            if not personality_template:
                print("❌ 无法加载理中客人格模板")
                return None
            system_prompt = personality_template.system_prompt
            user_prompt = personality_template.format_prompt(
                title=post_data.get('title', ''),
                description=post_data.get('description', ''),
                tags=' '.join(tags),
                base_idea=base_idea
            )

        try:
            response = self.client.chat.completions.create(
                model="Pro/deepseek-ai/DeepSeek-R1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2048,  # 增加 token 限制以获取完整输出
                temperature=0.7
            )
            
            comment = response.choices[0].message.content.strip()
            
            # 如果输出超过100个字符，认为是思维链输出
            if len(comment) > 100:
                # 按换行符分割，获取非空行
                lines = [line.strip() for line in comment.split('\n') if line.strip()]
                if lines:
                    # 取最后一行
                    last_line = lines[-1]
                    # 如果最后一行包含句号，取最后一句完整的话
                    if '。' in last_line:
                        sentences = [s.strip() for s in last_line.split('。') if s.strip()]
                        comment = sentences[-1]
                    else:
                        comment = last_line
        
            return comment
            
        except Exception as e:
            print(f"生成评论失败: {str(e)}")
            return None

    def update_posts_from_db(self):
        """从数据库更新帖子信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
            SELECT 
                作品ID,
                作品标题,
                作品描述,
                作品标签,
                作者昵称,
                作者链接,
                评论数量
            FROM explore_data
            WHERE 作者链接 IS NOT NULL
            """
            
            cursor.execute(query)
            new_posts_count = 0
            
            for row in cursor.fetchall():
                post_id = row[0]
                if post_id not in self.data["posts"]:
                    new_posts_count += 1
                    self.data["posts"][post_id] = {
                        "title": row[1],
                        "description": row[2],
                        "tags": row[3].split('#') if row[3] else [],
                        "author": row[4],
                        "author_url": row[5],
                        "comment": None,
                        "is_generated": False,
                        "generated_time": None,
                        "is_sent": False,
                        "sent_time": None,
                        "last_base_idea": None
                    }
            
            conn.close()
            
            if new_posts_count > 0:
                self.save_comments()
                print(f"\n✨ 从数据库更新了 {new_posts_count} 条新帖子")
            
        except sqlite3.Error as e:
            print(f"\n❌ 数据库读取错误: {str(e)}")
        except Exception as e:
            print(f"\n❌ 更新帖子时出错: {str(e)}")

    def auto_generate_comments(self):
        """自动为未生成评论的帖子生成评论，使用理中客人格"""
        pending_posts = {
            post_id: post_data 
            for post_id, post_data in self.data["posts"].items()
            if not post_data.get('comment')
        }
        
        if not pending_posts:
            return
        
        print(f"\n发现 {len(pending_posts)} 条未生成评论的帖子")
        print("开始自动生成评论（使用理中客人格）...")
        
        # 获取理中客人格模板
        rational_template = self.prompt_manager.get_prompt_template('rational')
        if not rational_template:
            print("❌ 无法加载理中客人格模板，自动生成评论失败")
            return
        
        success_count = 0
        for post_id, post_data in pending_posts.items():
            print(f"\n处理帖子: {post_data['title']}")
            try:
                comment = self.generate_comment_with_personality(post_data, personality_template=rational_template)
                if comment:
                    self.add_comment(post_id, comment)
                    success_count += 1
                    print(f"✅ 已生成评论: {comment}")
                else:
                    print(f"❌ 帖子 {post_id} 评论生成失败")
            except Exception as e:
                print(f"❌ 处理帖子 {post_id} 时出错: {str(e)}")
            
            # 添加短暂延迟，避免请求过快
            time.sleep(random.uniform(1, 3))
        
        if success_count > 0:
            print(f"\n✨ 成功为 {success_count} 条帖子生成了评论")
        else:
            print("\n❌ 没有成功生成任何评论")


def main():
    manager = CommentManager()
    manager.display_menu()

if __name__ == "__main__":
    main()