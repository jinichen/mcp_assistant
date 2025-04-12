# AI 助手

## 概述
AI 助手是一个现代化的全栈应用程序，具有多模态功能，支持多种语言模型（LLM）和工具集成。它提供了一个直观的界面，用于与AI模型交互，并支持各种专业工具，如数学计算、天气查询等。

## 主要特性
- **多LLM支持**：支持OpenAI、Google、Anthropic和NVIDIA等多种语言模型
- **MCP工具集成**：通过Model Control Protocol (MCP)集成专业工具
- **响应式设计**：适配桌面和移动设备的现代化用户界面
- **认证系统**：安全的用户认证和会话管理
- **多语言支持**：支持中文和英文界面
- **实时聊天**：流畅的对话体验
- **文件上传**：支持文档和图片上传，让AI可以分析和处理文件内容

## 系统架构
AI 助手采用三层架构设计：

1. **前端**：使用Next.js构建的React应用
   - 使用Tailwind CSS实现响应式设计
   - 支持多语言国际化
   - 实时聊天界面
   - 文件上传和管理组件

2. **后端**：基于FastAPI的Python服务
   - RESTful API
   - 多LLM集成
   - MCP工具管理
   - 用户认证
   - 文件上传处理

3. **数据库**：PostgreSQL
   - 用户管理
   - 会话存储
   - 工具配置
   - 文件元数据存储

## 安装
快速开始：
```bash
# 克隆仓库
git clone https://github.com/你的用户名/ia-assistant.git
cd ia-assistant

# 设置后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 设置前端
cd ../frontend
npm install
```

详细安装说明请参考[安装手册](INSTALLATION.md)。

## MCP工具集成
AI 助手通过Model Control Protocol (MCP)集成了多种专业工具：

### 可用工具
- **数学工具**：执行数学计算
- **天气工具**：查询天气信息
- **更多工具**：持续集成中...

### 启动MCP服务器
```bash
cd backend
python mcp_server.py
```

## 文件上传功能
AI 助手支持多种文件格式的上传：

### 支持的文件类型
- **文档**：PDF、DOCX、TXT、MD、CSV、JSON
- **图片**：JPG、JPEG、PNG、GIF、BMP、WEBP

### 使用方法
1. 点击聊天界面中的上传按钮
2. 选择要上传的文件类型（文档或图片）
3. 从本地选择文件上传
4. 上传成功后，文件将显示在聊天中，AI可以分析文件内容

## 使用指南
1. 访问前端界面：`http://localhost:3000`
2. 创建账户或登录
3. 开始对话，例如：
   - "计算 123 + 456"
   - "查询北京的天气"
   - "使用数学工具计算 789 * 321"
   - "上传文件并分析其内容"

## 开发
### 目录结构
```
ia-assistant/
├── backend/           # FastAPI后端服务
│   ├── app/          # 应用代码
│   ├── tests/        # 测试文件
│   └── requirements.txt
├── frontend/         # Next.js前端应用
│   ├── src/         # 源代码
│   ├── public/      # 静态资源
│   └── package.json
└── README.md        # 项目文档
```

### 配置
#### 后端配置
在`backend/.env`中设置：
```env
DATABASE_URL=postgresql://user:password@localhost:5432/ia_assistant
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
```

#### 前端配置
在`frontend/.env.local`中设置：
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 许可证
本项目采用MIT许可证。详见[LICENSE](LICENSE)文件。

## 致谢
感谢以下技术和服务：
- Next.js和React
- FastAPI
- PostgreSQL
- OpenAI、Google、Anthropic和NVIDIA的AI服务
- Tailwind CSS 