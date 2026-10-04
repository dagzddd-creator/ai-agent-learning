# 接真实 API 的 4 步模板 + 你踩过的坑

> 适用：任何"去外部服务器取数据"的工具（天气、汇率、翻译、新闻……）。
> 这是基于你实战 get_real_weather 总结的，不是抄教材，是你自己踩出来的。

## 一、4 步链（核心口诀）

```
给一个参数（如城市名）
     │
     ▼
① 拼 URL           f"https://wttr.in/{city}?format=j1"
     │
     ▼
② 发请求           requests.get(url, timeout=5)   → 拿到 resp
     │
     ▼
③ 解析 JSON        data = resp.json()  （文本 → Python字典）
     │
     ▼
④ 取出想要的值      data["current_condition"][0]["temp_C"]
     │
     ▼
  打包返回            {"city": ..., "temperature_c": ...}
```

**浓缩一句：拼 → 发(requests.get) → 解(.json) → 取 → 返回。**

任何接 API 的工具（汇率/天气/翻译/新闻）都是这个骨架，只是 URL 和取值路径不同。

## 二、为什么要 try/except？（双保险）

真实 API **每一步都可能失败**，单靠一个 try 不够，要"双重保险"：

```python
try:
    resp = requests.get(url, timeout=5)      # 可能①：网络断了
    data = resp.json()                       # 可能②：返回的不是合法JSON
    temp = int(data["current_condition"][0]["temp_C"])  # 可能③：字段名变了/不是数字
except requests.RequestException as e:
    return {"error": f"请求失败：{e}"}        # 拦住"网络错"
except (KeyError, ValueError) as e:
    return {"error": f"解析失败：{e}"}        # 拦住"数据不对"
```

**坑（你亲历）：不写 except → 服务器一抽风，整个 Agent 崩溃。**
**真理（复习）：工具永远必须"返回一个字典（哪怕含 error）"，绝不自己崩溃。**

这和模拟工具的 `.get()` 是同一个道理——只是模拟工具用 `if 判断`，真实 API 用 `try/except`。目标一样：**把"失败"变成"能回传给模型的结果"。**

## 三、具体踩过的坑（全是你自己撞出来的）

| 坑 | 错 | 对 | 为什么 |
|---|---|---|---|
| JSON 类型 | `"type": "str"` | `"type": "string"` | JSON Schema 没有 `str`，只有 `string`/`integer`/`number`/`boolean` |
| 温度是字符串 | `temp_C` 直接用 | `temp = int(temp)` | 接口返回 `"24"` 是字符串；直接比较 `"9">"20"` 会出错 |
| 取列表元素 | 直接取 | `[0]` | `current_condition` 是数组，取第一个用 `[0]` |
| 多级取值 | 读 `data["temp_C"]` | `data["current_condition"][0]["temp_C"]` | 一层层剥：data → current_condition → 第0个 → temp_C |
| condition 逻辑 | `"多云" if temp>=20` 反了 | `"晴" if temp>=20 else "多云"` | >=20 应该是"晴"，别写反 |
| description | `"支持许多城市"` | 写范围 + 示例 | "支持全球主要城市（中英文均可），例如北京/Beijing/东京" |

## 四、对比表：模拟工具 vs 真实API工具

| 维度 | 模拟工具（死表） | 真实 API 工具 |
|---|---|---|
| 数据来源 | 代码里写死 `_CITY_TEMP` | 服务器实时返回 |
| 读数据 | `.get()` + if 判空 | 发请求 + `.json()` + try/except |
| 失败处理 | return {"error": ...} | except → return {"error": ...} |
| 适用范围 | 固定、不变的数据 | 变化、需联网的数据 |

**判断用哪种**：天气/汇率这种天天变的 → 真实 API；穿搭规则这种相对固定的 → 可本地写死。

## 五、防乱编的职责分离（进阶意识）

```python
"desc_en": desc,   # ← 返回原始英文数据给模型
```

**为什么返回英文原文，而不是自己翻译成中文？**

> 工具负责"给真相"，模型负责"表达/翻译/组织语言"。
> 工具层自己硬翻容易翻错（= 给了模型错误事实）；返回原始英文，模型会自动且正确地转述成中文。

这个原则你亲眼验证过：intercepted 时模型把 `Patchy rain` 正确翻译成了"零星小雨"。
**职责分离是防乱编的关键——工具层绝不编造，只传递原始真实数据。**

## 六、自查清单（写下一个真实API工具时对着过）

- [ ] import requests（没装就 `pip install requests`）
- [ ] 用 f-string 拼 URL，参数动态拼进去
- [ ] timeout 设了没（防止傻等）
- [ ] try/except 双保险（网络错 + 解析错）都写了
- [ ] 数值字段记得 `int()/float()` 转换
- [ ] 数组取值记得 `[0]`
- [ ] description 写了支持范围 + 示例（防模型乱传参数）
- [ ] 返回"原始数据字段"给模型，别在工具里硬翻译

---
*把这段吃透，你就能把任意"只会死表"的工具升级成"接真实数据"。这是 Agent 很重要的工程体味。*