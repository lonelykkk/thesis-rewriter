"""
论文降重 & 降AI核心处理引擎

降重策略：
1. 同义词替换（基于内置词库）
2. 句式转换（主动↔被动、否定前置等）
3. 词语增删（添加修饰词、删除冗余词）
4. 长短句互换

降AI策略：
1. 增加口语化过渡词
2. 打破过于规整的句式结构
3. 添加限定性表达
4. 插入研究者视角
5. 增加轻微的不完美（如适当冗余）
"""

import re
import random
import jieba
from .synonym_dict import SYNONYM_DICT, SENTENCE_PATTERNS


class ThesisRewriter:
    """论文降重降AI核心类"""

    def __init__(self, api_key=None, api_base_url=None, api_model=None, custom_prompt=""):
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.api_model = api_model
        self.custom_prompt = custom_prompt.strip()

        # 词性缓存
        self._pos_cache = {}

        # 学术高频词（避免替换的核心术语）
        self.core_terms = {
            "算法", "模型", "神经网络", "深度学习", "机器学习",
            "卷积", "循环", "注意力", "梯度", "损失函数",
            "分类器", "回归", "聚类", "降维", "正则化",
            "数据集", "训练集", "测试集", "验证集",
            "准确率", "精确率", "召回率", "F1值", "AUC",
            "CPU", "GPU", "TPU", "API", "GUI",
            "Python", "Java", "C++", "TensorFlow", "PyTorch",
        }

    def rewrite(self, text, mode="both"):
        """
        主入口：对论文文本进行降重/降AI处理

        Args:
            text: 输入文本
            mode: "reduce"（仅降重）, "deai"（仅降AI）, "both"（两者）

        Returns:
            dict: {"original": 原文, "rewritten": 改写后文本,
                   "changes": 改动统计}
        """
        if not text or not text.strip():
            return {"original": text, "rewritten": text, "changes": {"total": 0, "details": []}}

        # 如果配置了API密钥，优先使用AI改写
        if self.api_key:
            return self._rewrite_via_api(text, mode)

        # 否则使用内置引擎
        return self._rewrite_local(text, mode)

    def _rewrite_local(self, text, mode):
        """本地引擎处理"""
        changes = []
        paragraphs = text.strip().split("\n")
        new_paragraphs = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                new_paragraphs.append("")
                continue

            # 按句号、问号、感叹号、分号、冒号分割
            sentences = re.split(r'(?<=[。！？；：])', para)
            new_sentences = []

            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue

                original = sent
                modified = sent

                if mode in ("reduce", "both"):
                    modified = self._apply_synonym_replacement(modified, changes)
                    modified = self._apply_sentence_transformation(modified, changes)
                    modified = self._apply_word_adjustment(modified, changes)

                if mode in ("deai", "both"):
                    modified = self._apply_humanize(modified, changes)

                # 确保处理后的文本合理
                if modified and modified != original:
                    new_sentences.append(modified)
                else:
                    new_sentences.append(original)

            new_paragraphs.append("".join(new_sentences))

        rewritten = "\n".join(new_paragraphs)

        # 去重统计
        unique_changes = []
        seen = set()
        for c in changes:
            key = (c["type"], c["original"][:20])
            if key not in seen:
                seen.add(key)
                unique_changes.append(c)

        return {
            "original": text,
            "rewritten": rewritten,
            "changes": {
                "total": len(unique_changes),
                "details": unique_changes[:50],  # 最多返回50条
            },
        }

    def _apply_synonym_replacement(self, text, changes):
        """同义词替换"""
        words = jieba.lcut(text)
        new_words = []
        replaced_indices = set()

        for i, word in enumerate(words):
            if i in replaced_indices:
                new_words.append(word)
                continue

            # 跳过核心术语、短词（小于2字）、标点
            if (word in self.core_terms or len(word) < 2 or
                    re.match(r'^[，。！？；：、""''（）《》【】\s]+$', word)):
                new_words.append(word)
                continue

            # 检查是否有同义词（优先替换2字以上的词）
            if word in SYNONYM_DICT and len(SYNONYM_DICT[word]) > 0:
                # 70%概率替换
                if random.random() < 0.7:
                    synonym = random.choice(SYNONYM_DICT[word])
                    new_words.append(synonym)
                    changes.append({
                        "type": "synonym",
                        "original": word,
                        "modified": synonym,
                    })
                    continue

            new_words.append(word)

        return "".join(new_words)

    def _apply_sentence_transformation(self, text, changes):
        """句式变换"""
        modified = text

        # 1. "是...的"句式变换
        modified = re.sub(
            r'是(重要的|关键的|必要的|显著的|明显的)([^。]*?)的',
            self._random_replace,
            modified
        )

        # 2. 把字句 ↔ 被字句
        ba_pattern = re.compile(r'把(\w+)')
        if ba_pattern.search(modified) and random.random() < 0.5:
            modified = ba_pattern.sub(r'将\1', modified)

        bei_pattern = re.compile(r'被(\w+)')
        if bei_pattern.search(modified) and random.random() < 0.5:
            modified = bei_pattern.sub(r'由\1', modified)

        # 3. 部分"对...进行..."变换
        dui_pattern = re.compile(r'对(\w+)进行(\w+)')
        if dui_pattern.search(modified) and random.random() < 0.4:
            modified = dui_pattern.sub(r'\2\1', modified)

        if modified != text:
            changes.append({
                "type": "transformation",
                "original": text[:30],
                "modified": modified[:30],
            })

        return modified

    def _apply_word_adjustment(self, text, changes):
        """词语增删调整"""
        modified = text

        # 1. 删除冗余修饰词
        redundant_words = [
            (r'非常地', '非常'), (r'极其地', '极其'),
            (r'特别地', '特别'), (r'相当地', '相当'),
        ]
        for old, new in redundant_words:
            if old in modified and random.random() < 0.6:
                modified = modified.replace(old, new)

        # 2. 添加学术修饰词（概率性地）
        if random.random() < 0.15:
            modifiers = [
                ("该", "该"),
                ("相关", "相关"),
                ("上述", "上述"),
                ("本文", "本文"),
            ]
            # 在句首添加
            if len(modified) > 10 and modified[0] not in "本该上述这种那":
                modifier = random.choice(modifiers)[0]
                modified = f"{modifier}{modified[0].lower()}{modified[1:]}"
                changes.append({
                    "type": "word_adjust",
                    "original": text[:15],
                    "modified": modified[:15],
                })

        return modified

    def _apply_humanize(self, text, changes):
        """降AI处理 - 让文本更像人类写作"""
        modified = text

        # 1. 插入口语化过渡词
        transitions = [
            "值得注意的是，", "需要指出的是，", "值得注意的是，",
            "从某种程度上说，", "事实上，", "实际上，",
            "总体而言，", "从某种意义上讲，", "不可否认，",
            "值得关注的是，", "需要强调的是，",
        ]

        # 在长句前（超过50字）插入过渡词
        if len(modified) > 50 and random.random() < 0.3:
            transition = random.choice(transitions)
            # 找到合适的插入点（句首或逗号后）
            insert_pos = 0
            modified = modified[:insert_pos] + transition + modified[insert_pos:]
            changes.append({
                "type": "humanize_transition",
                "original": text[:20],
                "modified": modified[:20],
            })

        # 2. 打破过于规整的并列结构
        # 替换"第一，第二，第三"为更自然的表达
        pattern_order = re.compile(r'(第一[，,]|第二[，,]|第三[，,])')
        if pattern_order.search(modified) and random.random() < 0.4:
            replacements = {
                "第一，": "首先，",
                "第二，": "其次，",
                "第三，": "再次，",
                "第一,": "首先,",
                "第二,": "其次,",
                "第三,": "再次,",
            }
            for old, new in replacements.items():
                modified = modified.replace(old, new)
            changes.append({
                "type": "humanize_order",
                "original": text[:20],
                "modified": modified[:20],
            })

        # 3. 添加限定性表达（概率性）
        qualifiers = [
            ("是", "通常是"), ("会", "往往会"),
            ("可以", "通常可以"), ("具有", "一般具有"),
            ("体现", "在一定程度上体现"),
        ]
        for old, new in qualifiers:
            if old in modified and random.random() < 0.15:
                modified = modified.replace(old, new, 1)
                break

        # 4. 插入研究者视角
        if random.random() < 0.15:
            perspectives = [
                "本研究认为，", "笔者发现，",
                "通过分析可以看出，", "本文认为，",
            ]
            perspective = random.choice(perspectives)
            if modified.startswith("本文") or modified.startswith("本研究"):
                pass  # 已有视角
            elif len(modified) > 20:
                modified = perspective + modified[0].lower() + modified[1:]
                changes.append({
                    "type": "humanize_perspective",
                    "original": text[:20],
                    "modified": modified[:20],
                })

        # 5. 适当增删连接词
        if random.random() < 0.2:
            add_connectors = [
                ("，", "；与此同时，"),
                ("。", "。此外，"),
            ]
            for old, new in add_connectors:
                if old in modified and modified.count(old) > 1:
                    pos = modified.find(old, len(modified) // 3)
                    if pos > 0:
                        modified = modified[:pos] + new + modified[pos+len(old):]
                        break

        if modified != text:
            changes.append({
                "type": "humanize_other",
                "original": text[:15],
                "modified": modified[:15],
            })

        return modified

    @staticmethod
    def _random_replace(match):
        """替换匹配的句式"""
        variations = [
            f"对{match.group(2)}而言是{match.group(1)}的",
            f"{match.group(2)}具有{match.group(1)}意义",
            f"{match.group(2)}表现出{match.group(1)}特征",
        ]
        return random.choice(variations)

    def _rewrite_via_api(self, text, mode):
        """使用AI API进行改写（优先使用自定义prompt）"""
        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_base_url,
            )

            # 用户自定义prompt优先
            if self.custom_prompt:
                system_prompt = self.custom_prompt
            elif mode == "reduce":
                system_prompt = """你是一位专业的论文降重助手。请对以下学术文本进行降重处理，要求：
1. 保留原意和学术严谨性
2. 替换同义词、改变句式结构
3. 保持专业术语不变
4. 不要改变段落长度
5. 保持原有的引用格式

请直接输出改写后的文本，不要添加解释。"""
            elif mode == "deai":
                system_prompt = """你是一位论文降AI助手。请对以下文本进行人性化处理，要求：
1. 保持学术严谨性
2. 打破过于规整的句式结构
3. 添加适当的过渡词和限定词
4. 增加研究者的主观视角表达
5. 不要改变专业术语和核心论点

请直接输出改写后的文本，不要添加解释。"""
            else:
                system_prompt = """你是一位专业的论文降重和降AI助手。请对以下文本进行处理，要求：
1. 同义词替换和句式变换
2. 打破AI式规整结构，增加人性化表达
3. 保持学术严谨性和专业术语
4. 不要改变段落长度和核心论点

请直接输出改写后的文本，不要添加解释。"""

            response = client.chat.completions.create(
                model=self.api_model or "deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"请改写以下文本：\n\n{text}"},
                ],
                temperature=0.7,
                max_tokens=4096,
            )

            rewritten = response.choices[0].message.content.strip()
            return {
                "original": text,
                "rewritten": rewritten,
                "changes": {"total": "AI处理", "details": []},
            }

        except Exception as e:
            # API调用失败，回退到本地引擎
            return self._rewrite_local(text, mode)


# 简易批次处理
def batch_rewrite(text, mode="both", api_key=None, api_base_url=None, api_model=None):
    """批量处理接口"""
    rewriter = ThesisRewriter(
        api_key=api_key,
        api_base_url=api_base_url,
        api_model=api_model,
    )
    return rewriter.rewrite(text, mode)
