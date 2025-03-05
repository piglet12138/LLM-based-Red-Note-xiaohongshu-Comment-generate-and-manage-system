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
        """格式化提示词"""
        prompt = self.user_prompt_template.format(
            title=title,
            description=description,
            tags=tags
        )
        
        if base_idea:
            prompt = f"请基于以下观点：{base_idea}\n\n" + prompt
            
        return prompt

class PromptManager:
    def __init__(self, prompts_file: str = "prompts.json"):
        self.prompts_file = prompts_file
        self.personalities: Dict[str, PromptTemplate] = {}
        self.load_prompts()

    def load_prompts(self):
        """加载提示词配置"""
        try:
            if not os.path.exists(self.prompts_file):
                self.create_default_prompts()
                
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.personalities = {
                key: PromptTemplate(
                    name=info["name"],
                    description=info["description"],
                    system_prompt=info["system_prompt"],
                    user_prompt_template=info["user_prompt_template"]
                )
                for key, info in data["personalities"].items()
            }
        except Exception as e:
            print(f"加载提示词配置失败: {str(e)}")
            self.create_default_prompts()

    def create_default_prompts(self):
        """创建默认提示词配置"""
        default_prompts = {
            "personalities": {
                "tieba": {
                    "name": "贴吧老哥",
                    "description": "攻击力强，看不惯就骂",
                    "system_prompt": "你是一个从贴吧转战小红书的嘴臭老哥，具有很强的攻击性，善于看破事情的本质，发表一针见血的评论。",
                    "user_prompt_template": "请直接输出一条针对这篇小红书帖子的评论，不要解释思考过程。要求：\n1. 评论一针见血，直接开喷\n2. 使用贴吧特色网络用语\n3. 评论简短有力，不超过20字\n4. 适当添加表情，展现嘲讽的意味\n\n帖子信息：\n标题：{title}\n描述：{description}\n标签：{tags}"
                },
                # ... 其他默认人格配置 ...
            }
        }
        
        with open(self.prompts_file, 'w', encoding='utf-8') as f:
            json.dump(default_prompts, f, ensure_ascii=False, indent=2)
        
        self.load_prompts()

    def get_personality_names(self) -> Dict[str, str]:
        """获取所有人格的名称和描述"""
        return {key: f"{p.name} - {p.description}" for key, p in self.personalities.items()}

    def get_prompt_template(self, personality_key: str) -> Optional[PromptTemplate]:
        """获取指定人格的提示词模板"""
        return self.personalities.get(personality_key) 