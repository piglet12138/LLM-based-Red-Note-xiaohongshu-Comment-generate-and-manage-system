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
        os.environ["OPENAI_API_KEY"] = "your_api_key"                          #you can try this but not abuse ds: "sk-saoyuxaudkkvxnqyfeoonpagqrnoqomyazphdbzqaraahdwi" #
        os.environ["OPENAI_BASE_URL"] =  "your_base_url"                       #ds  "https://api.siliconflow.cn/v1"    
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
            print("\n请选择评论生成模式:")
            print("1. 直接生成评论")
            print("2. 输入基本观点后生成")
            print("3. 选择评论人格")
            print("q. 返回上级菜单")
            
            mode = input("\n请选择模式 (1/2/3/q): ").strip().lower()
            
            if mode == 'q':
                return
            
            base_idea = None
            personality_template = None
            
            if mode == '2':
                base_idea = input("\n请输入您的基本观点: ").strip()
                if not base_idea:
                    print("\n❌ 观点不能为空")
                    continue
            elif mode == '3':
                # 显示可用的人格
                personalities = self.prompt_manager.get_personality_names()
                print("\n可选择的评论人格:")
                for idx, (key, desc) in enumerate(personalities.items(), 1):
                    print(f"{idx}. {desc}")
                print(f"{len(personalities) + 1}. 自定义人格")
                
                try:
                    choice = int(input(f"\n请选择人格 (1-{len(personalities) + 1}): ").strip())
                    if 1 <= choice <= len(personalities):
                        # 获取对应的personality key
                        personality_key = list(personalities.keys())[choice - 1]
                        personality_template = self.prompt_manager.get_prompt_template(personality_key)
                    elif choice == len(personalities) + 1:
                        # 自定义人格
                        print("\n请设置自定义人格:")
                        name = input("人格名称: ").strip()
                        description = input("人格描述: ").strip()
                        system_prompt = input("系统提示词: ").strip()
                        user_prompt = input("用户提示词模板: ").strip()
                        
                        personality_template = PromptTemplate(
                            name=name,
                            description=description,
                            system_prompt=system_prompt,
                            user_prompt_template=user_prompt
                        )
                    else:
                        print("\n❌ 无效的选择")
                        continue
                except ValueError:
                    print("\n❌ 请输入有效的数字")
                    continue
            elif mode != '1':
                print("\n❌ 无效的选择，请重试")
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
                
                sub_choice = input("\n请选择 (1/2/3): ").strip()
                
                if sub_choice == '1':
                    self.add_comment(post_id, comment, base_idea)
                    print("\n✅ 已保存评论")
                    return
                elif sub_choice == '2':
                    continue
                elif sub_choice == '3':
                    return
                else:
                    print("\n❌ 无效的选择，请重试")
            else:
                print("\n❌ 评论生成失败")
            return

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

    def generate_default_prompt(self, post_data, base_idea=None):
        """生成默认的提示词"""
        tags = post_data.get('tags', [])
        if isinstance(tags, str):
            tags = tags.split('#')
        tags = [tag.strip() for tag in tags if tag.strip()]
        
        if base_idea:
            prompt = f"""
请直接输出一条针对这篇小红书帖子的评论，不要解释思考过程。要求：
1. 保持原有观点的核心意思：{base_idea}
2. 评论简短有力，不超过20字
3. 使用网络用语，让评论更接地气
4. 适当添加表情，展现嘲讽的意味

帖子信息：
标题：{post_data.get('title', '')}
描述：{post_data.get('description', '')}
标签：{' '.join(tags)}

直接输出评论内容，不要有任何解释或思考过程。
"""
        else:
            prompt = f"""
请直接输出一条针对这篇小红书帖子的评论，不要解释思考过程。要求：
1. 评论一针见血，有理有据，合理中肯
2. 要与帖子内容强相关，有明确的观点
3. 评论简短有力，不超过20字
4. 使用网络用语，让评论更接地气
5. 适当添加表情，展现嘲讽的意味

帖子信息：
标题：{post_data.get('title', '')}
描述：{post_data.get('description', '')}
标签：{' '.join(tags)}

直接输出评论内容，不要有任何解释或思考过程。
"""
        return prompt

def main():
    manager = CommentManager()
    manager.display_menu()

if __name__ == "__main__":
    main()