# 📐 编码规范与技术标准

## Python编码规范

### 通用原则
- 遵循 PEP 8 风格指南
- 使用Python 3.10+
- 类型提示必须完整
- 文档字符串用Docstring

### 文件结构

```python
"""
Module docstring - 简述模块功能
作者: xxxx
最后更新: 2026-07-21
"""

from typing import Optional, Dict, List
import asyncio
from dataclasses import dataclass

# ===== 数据模型 (最上面) =====
@dataclass
class MyModel:
    """数据模型的Docstring"""
    field1: str
    field2: int

# ===== 工具函数 =====
def helper_function(param: str) -> str:
    """函数说明"""
    pass

# ===== 主要类 =====
class MyClass:
    """类说明"""
    
    def __init__(self):
        pass
    
    def public_method(self) -> None:
        """公开方法"""
        pass
    
    def _private_method(self) -> None:
        """私有方法"""
        pass

# ===== 主程序入口 =====
if __name__ == "__main__":
    pass
```

### 命名约定

| 对象 | 规则 | 示例 |
|------|------|------|
| 模块 | 小写_下划线 | `content_analysis_agent.py` |
| 类 | PascalCase | `ContentAnalysisAgent` |
| 方法/函数 | snake_case | `process_request()` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRIES = 3` |
| 私有方法 | _snake_case | `_internal_process()` |
| 变量 | snake_case | `user_request` |

### 类型提示

```python
from typing import Optional, List, Dict, Tuple, Callable

# ✅ 好的例子
def process_data(
    input_data: Dict[str, any],
    timeout: Optional[int] = None
) -> List[str]:
    """处理数据
    
    Args:
        input_data: 输入数据字典
        timeout: 超时时间（秒）
    
    Returns:
        处理结果列表
    """
    pass

# ❌ 不好的例子
def process_data(input_data, timeout=None):
    pass
```

### Docstring格式

```python
def method_name(param1: str, param2: int) -> bool:
    """一句话简述功能。
    
    详细说明（如有必要）。
    可以写多行来解释复杂逻辑。
    
    Args:
        param1: 参数1说明
        param2: 参数2说明
    
    Returns:
        返回值说明
    
    Raises:
        ValueError: 当参数无效时
        TimeoutError: 当超时时
    
    Example:
        >>> result = method_name("test", 10)
        >>> print(result)
        True
    """
    pass
```

### 异步编程规范

```python
# ✅ 异步函数定义
async def async_operation(self, data: str) -> Dict:
    """执行异步操作"""
    result = await some_async_call(data)
    return result

# ✅ 等待多个协程
async def parallel_operations(self):
    results = await asyncio.gather(
        self.task1(),
        self.task2(),
        self.task3(),
        return_exceptions=True
    )
    return results

# ✅ 带超时的异步操作
async def operation_with_timeout(self):
    try:
        result = await asyncio.wait_for(
            self.long_operation(),
            timeout=30.0
        )
    except asyncio.TimeoutError:
        logger.error("Operation timed out")
        raise
```

---

## Agent编程规范

### BaseAgent抽象类

```python
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseAgent(ABC):
    """所有Agent的基类"""
    
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.logger = get_logger(name)
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务
        
        Args:
            task: 任务字典
        
        Returns:
            结果字典
        """
        pass
    
    @abstractmethod
    async def handle_error(self, error: Exception) -> None:
        """处理错误"""
        pass
```

### Agent实现模板

```python
from core.agents.base_agent import BaseAgent
from core.models import Message, Result

class MyAgent(BaseAgent):
    """功能描述"""
    
    async def execute(self, task: Dict) -> Dict:
        """主处理逻辑"""
        try:
            # 1. 验证输入
            self._validate_input(task)
            
            # 2. 处理逻辑
            result = await self._process(task)
            
            # 3. 返回结果
            return self._format_result(result, success=True)
        
        except Exception as e:
            self.logger.error(f"Error: {e}", exc_info=True)
            return self._format_result(None, success=False, error=str(e))
    
    def _validate_input(self, task: Dict) -> None:
        """验证输入数据"""
        required_fields = ["field1", "field2"]
        for field in required_fields:
            if field not in task:
                raise ValueError(f"Missing required field: {field}")
    
    async def _process(self, task: Dict) -> Any:
        """核心处理逻辑"""
        # 实现具体逻辑
        pass
    
    def _format_result(
        self, 
        data: Any = None, 
        success: bool = True, 
        error: str = None
    ) -> Dict:
        """格式化结果"""
        return {
            "success": success,
            "data": data,
            "error": error,
            "agent_id": self.agent_id
        }
```

---

## 消息格式规范

### 消息结构

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class Message:
    """消息数据模型"""
    msg_id: str
    timestamp: str  # ISO 8601格式
    sender: str
    receiver: str
    msg_type: str  # task/result/error/heartbeat
    task_type: Optional[str] = None
    priority: int = 1
    timeout: int = 300
    payload: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending/processing/success/failed
    result: Optional[Dict] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "msg_id": self.msg_id,
            "timestamp": self.timestamp,
            "sender": self.sender,
            "receiver": self.receiver,
            "msg_type": self.msg_type,
            "task_type": self.task_type,
            "priority": self.priority,
            "timeout": self.timeout,
            "payload": self.payload,
            "status": self.status,
            "result": self.result,
            "error": self.error
        }
```

### 消息生成示例

```python
import uuid
from datetime import datetime

def create_message(
    sender: str,
    receiver: str,
    msg_type: str,
    payload: Dict,
    task_type: Optional[str] = None
) -> Message:
    """创建消息"""
    return Message(
        msg_id=f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}",
        timestamp=datetime.utcnow().isoformat() + "Z",
        sender=sender,
        receiver=receiver,
        msg_type=msg_type,
        task_type=task_type,
        payload=payload
    )
```

---

## 日志规范

### 日志配置

```python
import logging
from logging.handlers import RotatingFileHandler

def get_logger(name: str) -> logging.Logger:
    """获取或创建logger"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 文件处理器
        file_handler = RotatingFileHandler(
            filename=f"logs/{name}.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 格式化
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)
    
    return logger
```

### 日志使用规范

```python
logger.debug("Detailed info for debugging")  # 开发/调试
logger.info("Normal operation info")         # 重要事件
logger.warning("Something unexpected")       # 警告/可恢复
logger.error("Error occurred", exc_info=True)  # 错误（带堆栈）
logger.critical("Critical error")            # 严重问题
```

---

## 测试规范

### 测试文件命名

```
test_module_name.py  # 测试文件
test_*.py            # 测试模块
*_test.py            # 测试模块
```

### 测试用例结构

```python
import pytest
import asyncio

class TestMyAgent:
    """Agent测试类"""
    
    @pytest.fixture
    def agent(self):
        """创建测试用的Agent实例"""
        return MyAgent(agent_id="test_001", name="test")
    
    @pytest.mark.asyncio
    async def test_successful_execution(self, agent):
        """测试成功执行"""
        task = {"field1": "value", "field2": 10}
        result = await agent.execute(task)
        
        assert result["success"] is True
        assert result["data"] is not None
    
    @pytest.mark.asyncio
    async def test_invalid_input(self, agent):
        """测试无效输入"""
        task = {"field1": "value"}  # 缺少field2
        
        with pytest.raises(ValueError):
            await agent.execute(task)
    
    @pytest.mark.asyncio
    async def test_timeout(self, agent):
        """测试超时处理"""
        task = {"field1": "value", "field2": 10, "timeout": 0.1}
        
        with pytest.raises(asyncio.TimeoutError):
            await agent.execute(task)
```

### 测试覆盖率要求

- 单元测试覆盖率 ≥ 80%
- 关键路径覆盖率 100%
- 异常路径覆盖率 ≥ 80%

---

## 错误处理规范

### 自定义异常

```python
class AgentException(Exception):
    """Agent基础异常"""
    pass

class TaskValidationError(AgentException):
    """任务验证错误"""
    pass

class MaterialNotFoundError(AgentException):
    """素材未找到"""
    pass

class VideoCompositionError(AgentException):
    """视频合成错误"""
    pass
```

### 异常处理模式

```python
# ✅ 好的异常处理
try:
    result = await agent.execute(task)
except TaskValidationError as e:
    logger.warning(f"Task validation failed: {e}")
    return {"success": False, "error": "Invalid task"}
except AgentException as e:
    logger.error(f"Agent error: {e}", exc_info=True)
    raise
except Exception as e:
    logger.critical(f"Unexpected error: {e}", exc_info=True)
    raise

# ❌ 不好的异常处理
try:
    result = await agent.execute(task)
except:
    pass  # 捕获所有异常但不处理
```

---

## Git提交规范

### Commit Message格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型 (type)

- **feat**: 新功能
- **fix**: 修复bug
- **docs**: 文档更新
- **test**: 添加或修改测试
- **refactor**: 代码重构（不修改功能）
- **perf**: 性能优化
- **chore**: 构建、依赖、工具更新

### 示例

```
feat(content-analysis): implement requirement parsing
  
- 添加需求解析模块
- 支持5种分类识别
- 集成LLM分析

Closes #123
```

### 提交前检查清单

- [x] 代码符合PEP 8
- [x] 类型提示完整
- [x] 单元测试通过
- [x] 日志完善
- [x] Docstring完整
- [x] 没有debug代码

---

## 代码审查检查清单

### 功能正确性
- [x] 是否符合需求
- [x] 边界条件处理
- [x] 异常处理完善
- [x] 性能可接受

### 代码质量
- [x] 命名清晰
- [x] 逻辑简洁
- [x] 没有重复代码
- [x] 复杂度合理

### 文档与测试
- [x] Docstring完整
- [x] 测试覆盖
- [x] 日志适当

---

*最后更新: 2026-07-21*
*规范版本: 1.0*
