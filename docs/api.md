# API 文档

## 接口概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / | 首页 |
| POST | /rewrite | 提交文本处理请求 |
| GET | /compare | 结果对比页面 |

---

## POST /rewrite

提交论文文本进行降重/降AI处理。

### 请求体

```json
{
    "text": "需要处理的论文文本...",
    "mode": "both"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | 是 | 论文文本内容，最长50000字 |
| mode | string | 否 | 处理模式：`both`（全面优化）、`reduce`（仅降重）、`deai`（仅降AI），默认`both` |

### 响应

```json
{
    "success": true,
    "original": "原文内容...",
    "rewritten": "改写后内容...",
    "changes": {
        "total": 15,
        "details": [
            {
                "type": "synonym",
                "original": "研究",
                "modified": "探讨"
            }
        ]
    }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 是否成功 |
| original | string | 原文 |
| rewritten | string | 改写后文本 |
| changes.total | number/string | 改动数量（AI模式返回"AI处理"） |
| changes.details | array | 改动详情列表 |

### 错误响应

```json
{
    "success": false,
    "error": "错误信息"
}
```

| HTTP状态码 | 说明 |
|-----------|------|
| 400 | 请求参数错误 |
| 500 | 服务器内部错误 |

---

## 错误码

| 错误信息 | 说明 |
|---------|------|
| 请求数据为空 | 未发送JSON请求体 |
| 请输入论文文本 | text为空 |
| 文本过长 | 超过50000字限制 |
| 无效的处理模式 | mode参数不在允许范围内 |
| 处理失败：... | 服务器处理异常 |
