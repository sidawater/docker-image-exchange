self._llm_client# 《项目Python代码规范 v1.0》——必须严格遵守

你现在处于一个严格受控的代码库中，所有生成、修改、重构的 Python 代码必须 100% 符合以下规范，绝不允许任何例外。

## 1. package 与 module 命名(极其严格)
- package 和 module 名称必须为**单一小写词汇**，严禁使用下划线分词  
  正确：`manager`, `parser`, `utils`  
  错误：`data_manager`, `file_utils`, `my_parser`
- 如需表达复合含义，优先通过 package 拆分实现，而不是下划线  
  推荐：`manager/a.py`, `manager/b.py`  
  禁止：`a_manager.py`, `b_manager.py`

## 2. import 引用顺序与规则
- 严格顺序(每组之间空一行)：
  1. 标准库
  2. 第三方库
  3. 项目内部库(绝对引用或合理相对引用)
  4. 当前包/目录的本地模块(`.` 或 `./xxx`)
- 相对引用限制：
  - 只允许 `.` 和 `./xxx`，最多一个点
  - 严禁 `..`、`...` 或更深的相对导入
  - 禁止 `from __future__` 放在非文件顶部

## 3. 注释与文档字符串
- 统一使用 **Sphinx 风格 docstring**，禁止 Google、NumPy 或其他风格
- 除`#TODO`外，严禁使用单行注释
- docstring的语言首选英文

## 4. 代码复杂度
### 4.1 分支复杂度
- 一般情况下，单一函数/方法严禁超过50行(含注释)，复杂函数除外
- 复杂函数可以使用带有大量解释和用例的docstring, 但是代码部分严禁超过30行
### 4.2 调用复杂度
- 参数个数 ≤2 的函数：允许位置参数调用，也允许关键字调用
- 参数个数 ≥3 的函数：禁止纯位置参数调用(即禁止 `func(1, 2, 3)`)，必须使用关键字参数显式指明参数名(允许混合，如 `func(1, b=2, c=3)`)

## 4. FastAPI 
### 4.1 依赖注入(死规定)
- 严禁在路径函数中使用 `Depends(...)` 作为依赖注入
- 严禁在任何地方是引用和使用fastapi的 `Depends`

### 4.2 FastAPI 路由注册方式(死规定)
- 严禁使用装饰器模式(@app.get、@router.get 等)
- 统一使用以下方式注册路由：
  ```python
  router = APIRouter(prefix="/users", tags=["users"])
  router.add_api_route(
      path="/{user_id}",
      endpoint=get_user,
      methods=["GET"],
      response_model=UserOut,
      ...
  )
  ```

## 5. Sqlalchemy
- 严禁使用物理外键
- 严禁使用物理 sqlalchemy 的 relationship
