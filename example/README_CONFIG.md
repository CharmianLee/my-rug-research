# 配置说明

## 使用方法

1. **复制配置文件**：
   ```bash
   cp .env.example .env
   ```

2. **编辑配置文件**：
   修改 `.env` 文件中的配置项：
   - `OPENAI_API_KEY`: 设置您的API密钥
   - `OPENAI_BASE_URL`: 设置您的LLM代理站URL

3. **加载环境变量**：
   在运行脚本前执行：
   ```bash
   export $(cat .env | xargs)
   ```
   
   或者在脚本中直接设置环境变量：
   ```bash
   OPENAI_API_KEY="your_key" OPENAI_BASE_URL="https://your-proxy.com/v1" python main.py
   ```

## 代理站配置示例

### 常见的代理站URL格式：
- `https://api.chatanywhere.com.cn/v1`
- `https://api.openai-sb.com/v1`  
- `https://your-custom-proxy.com/v1`

### 注意事项：
- 确保代理站URL以 `/v1` 结尾
- API密钥格式需要与所用代理站兼容
- 某些代理站可能需要特殊的认证方式

## 修改说明

脚本已修改为：
1. 通过环境变量 `OPENAI_API_KEY` 读取API密钥
2. 通过环境变量 `OPENAI_BASE_URL` 读取自定义的代理站URL
3. 如果未设置环境变量，将使用OpenAI官方API地址作为默认值