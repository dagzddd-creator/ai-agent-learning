import os
os.environ["HF_HOME"] = r"D:\study-practice\rag-demo\models"      # 复用已下载的模型
os.environ["SENTENCE_TRANSFORMERS_HOME"] = r"D:\study-practice\rag-demo\models"
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"                # 国内镜像

# 第①步：写导入和"资料库"
# 环境配置：模型缓存指到 D 盘已下载好的目录 + 用国内镜像（不加会去连 huggingface.co 超时）
import os
os.environ["HF_HOME"] = r"D:\study-practice\rag-demo\models"
os.environ["SENTENCE_TRANSFORMERS_HOME"] = r"D:\study-practice\rag-demo\models"
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from sentence_transformers import SentenceTransformer
from sentence_transformers import util

model = SentenceTransformer("BAAI/bge-small-zh-v1.5")   # 和之前一样

# 你的"资料库"：3 段小知识（模拟你的笔记）
knowledge = [
    "三步法是写函数、写菜单、注册三件事。",
    "RAG全称是检索增强生成，先检索再回答。",
    "接真实API要拼URL、发请求、解析json取数据。",
]

kb_embeddings = model.encode(knowledge)   # 3段资料 → 3个向量

question = "什么是三步法？"
q_embedding = model.encode([question])       # 注意：传 list

# 用 util.cos_sim 算提问和每段资料的相似度
scores = util.cos_sim(q_embedding, kb_embeddings)[0]   # 取第一行

# 找出相似度最高的那段资料的索引
best_idx = int(scores.argmax())
print("最相关的资料：", knowledge[best_idx])

context = knowledge[best_idx]
prompt = f"参考资料：{context}\n\n问题：{question}\n请基于参考资料回答："

# 这里用基元律动，复用你 agent-basics/.env
import os
from dotenv import load_dotenv
load_dotenv("agent-basics/.env")
from openai import OpenAI
client = OpenAI(api_key=os.getenv("LLM_API_KEY"), base_url=os.getenv("LLM_BASE_URL"))
resp = client.chat.completions.create(
    model=os.getenv("LLM_MODEL", "deepseek-v4-flash-0731"),
    messages=[{"role": "user", "content": prompt}],
)
print(resp.choices[0].message.content)