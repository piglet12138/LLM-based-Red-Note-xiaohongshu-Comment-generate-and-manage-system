import json
import os
from typing import Dict, Optional

class PromptTemplate:
    def __init__(self, name: str, description: str, system_prompt: str, user_prompt_template: str):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.user_prompt_template = user_prompt_template

    def format_prompt(self, title: str, description: str, tags: str, base_idea: Optional[str] = None) -> str:
        """格式化提示词，保持原始模板格式"""
        # 直接使用模板中的格式，替换变量
        prompt = self.user_prompt_template.replace("{title}", title)
        prompt = prompt.replace("{description}", description)
        prompt = prompt.replace("{tags}", tags)
        
        # 如果有基础观点，添加到提示词中
        if base_idea:
            prompt = f"请基于以下观点：{base_idea}\n\n" + prompt
            
        return prompt

class PromptManager:
    def __init__(self):
        self.prompts_file = "prompts.json"
        self.personalities = {}
        self.load_prompts()

    def load_prompts(self):
        """从JSON文件加载提示词配置"""
        try:
            # 清空当前内存中的配置
            self.personalities = {}
            
            if os.path.exists(self.prompts_file):
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if isinstance(data, dict) and "personalities" in data:
                    # 加载文件中的所有人格配置
                    for key, config in data["personalities"].items():
                        try:
                            self.personalities[key] = PromptTemplate(
                                name=config["name"],
                                description=config["description"],
                                system_prompt=config["system_prompt"],
                                user_prompt_template=config["user_prompt_template"]
                            )
                        except KeyError as e:
                            print(f"❌ 人格配置 '{key}' 缺少必要字段: {e}")
                            continue
                else:
                    print("❌ JSON文件格式不正确，缺少 'personalities' 字段")
            else:
                print(f"❌ 配置文件不存在: {self.prompts_file}")
            
            # 如果没有任何人格配置（文件不存在或为空），加载默认配置
            if not self.personalities:
                self._create_default_prompts()
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON文件格式错误: {str(e)}")
            self._create_default_prompts()
        except Exception as e:
            print(f"❌ 加载提示词配置失败: {str(e)}")
            self._create_default_prompts()

    def _create_default_prompts(self):
        """创建默认的提示词配置"""
        default_prompts = {
            "personalities": {
                "rational": {
                    "name": "理中客",
                    "description": "基于事实，客观分析，有理有据",
                    "system_prompt": "你是一个理性客观的评论员，善于分析事物的本质，提供有理有据的见解。",
                    "user_prompt_template": """请生成3条不同风格的评论，每条评论都要符合以下要求：
1. 评论客观理性，有理有据
2. 从多个角度分析问题
3. 每条评论不超过50字
4. 使用专业但通俗的语言

帖子信息：
标题：{title}
描述：{description}
标签：{tags}"""
                },
                "tieba": {
                    "name": "贴吧老哥",
                    "description": "攻击力强，看不惯就骂",
                    "system_prompt": "你是一个从贴吧转战小红书的嘴臭老哥，具有很强的攻击性，善于看破事情的本质，发表一针见血的评论。",
                    "user_prompt_template": """请生成3条不同风格的评论，每条评论都要符合以下要求：
1. 评论一针见血，直接开喷
2. 使用贴吧特色网络用语
3. 每条评论不超过20字
4. 适当添加表情，展现嘲讽的意味

帖子信息：
标题：{title}
描述：{description}
标签：{tags}"""
                },
                "positive": {
                    "name": "小粉红",
                    "description": "具有社会责任感，传播正能量",
                    "system_prompt": "你是一个极具社会责任感的知识分子，喜欢分析社会现象，传播正能量，弘扬社会主义核心价值观。",
                    "user_prompt_template": """请生成3条不同风格的评论，每条评论都要符合以下要求：
1. 评论积极向上，传播正能量
2. 符合社会主义核心价值观
3. 每条评论不超过30字
4. 适当添加积极正面的表情

帖子信息：
标题：{title}
描述：{description}
标签：{tags}"""
                }
            }
        }
        
        # 保存默认配置到文件
        with open(self.prompts_file, 'w', encoding='utf-8') as f:
            json.dump(default_prompts, f, ensure_ascii=False, indent=2)
        
        # 加载默认配置到内存
        self.load_prompts()

    def get_personality_names(self) -> Dict[str, str]:
        """获取所有人格的名称和描述"""
        return {key: f"{p.name} - {p.description}" for key, p in self.personalities.items()}

    def get_prompt_template(self, personality_key: str) -> Optional[PromptTemplate]:
        """获取指定人格的提示词模板"""
        return self.personalities.get(personality_key)

    def add_personality(self, key: str, template: PromptTemplate):
        """添加新的人格配置"""
        try:
            # 首先检查文件是否存在
            if not os.path.exists(self.prompts_file):
                data = {"personalities": {}}
            else:
                try:
                    with open(self.prompts_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    # 确保数据结构正确
                    if not isinstance(data, dict) or "personalities" not in data:
                        data = {"personalities": {}}
                except json.JSONDecodeError:
                    print("❌ JSON文件损坏，将创建新的配置")
                    data = {"personalities": {}}
            
            # 添加或更新人格配置
            data["personalities"][key] = {
                "name": template.name,
                "description": template.description,
                "system_prompt": template.system_prompt,
                "user_prompt_template": template.user_prompt_template
            }
            
            # 安全地写入文件
            temp_file = self.prompts_file + '.tmp'
            try:
                # 先写入临时文件
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # 如果写入成功，替换原文件
                if os.path.exists(self.prompts_file):
                    os.replace(temp_file, self.prompts_file)
                else:
                    os.rename(temp_file, self.prompts_file)
                    
                # 更新内存中的配置
                self.personalities[key] = template
                print(f"✅ 成功保存人格配置: {template.name}")
                
            except Exception as e:
                # 如果出错，清理临时文件
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                raise e
                
        except Exception as e:
            print(f"❌ 保存人格配置失败: {str(e)}")
            # 如果发生错误，重新加载配置确保内存中的数据正确
            self.load_prompts()

    def get_personalities(self) -> Dict[str, PromptTemplate]:
        """获取所有人格配置"""
        if not hasattr(self, 'personalities'):
            self.load_prompts()
        return self.personalities 