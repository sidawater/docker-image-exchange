# 一、《项目Python代码规范 v1.0 -- 必须严格遵守

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


# 二、Vite + React + TypeScript 代码规范 -- 必须严格遵守

你现在处于一个严格受控的前端代码库中，所有生成、修改、重构的代码必须 100% 符合以下规范，绝不允许任何例外。

## 1. 项目结构与文件命名（极其严格）
- 目录和文件名称必须为**小写 kebab-case**，严禁使用 camelCase 或下划线分词  
  正确：`components/user-card`, `hooks/use-auth`, `pages/home-page`  
  错误：`UserComponents`, `useAuth`, `data_manager.ts`
- 组件文件统一使用 **PascalCase.tsx**（如 `UserCard.tsx`）
- 如需表达复合含义，优先通过目录层级拆分实现，而不是复杂文件名  
  推荐：`features/user/profile.tsx`、`features/user/settings.tsx`  
  禁止：`userProfileAndSettings.tsx`
- 推荐目录结构（大型项目）：
  ```
  src/
  ├── assets/          # 静态资源（图像、字体等）
  ├── components/      # 可复用 UI 组件（按功能分组）
  ├── features/        # 特性模块（按业务域分组，包含组件、hooks、api 等）
  ├── hooks/           # 自定义 hooks
  ├── pages/           # 页面组件（路由入口）
  ├── routes/          # 路由配置
  ├── services/        # API 服务、外部接口调用
  ├── store/           # 状态管理（如 Zustand/Redux）
  ├── types/           # 全局类型定义
  ├── utils/           # 工具函数
  ├── App.tsx
  ├── main.tsx
  └── vite-env.d.ts
  ```

## 2. import 引用顺序与规则
- 严格顺序（每组之间空一行）：
  1. React 相关（`react` 等）
  2. 第三方库（`@tanstack/react-query`、`axios` 等）
  3. 项目内部绝对导入（使用 `@/` 别名，如 `import { api } from '@/services/api'`）
  4. 相对导入（同目录或子目录）
- 相对引用限制：
  - 优先使用绝对导入（通过 `vite.config.ts` 配置 `@` 别名指向 `src/`）
  - 相对导入只允许 `./` 或 `../`，最多一层 `../`
  - 严禁 `../../` 或更深的相对导入
- 禁止在文件顶部以外的地方使用动态 import（除代码分割场景）

## 3. 注释与文档字符串
- 统一使用 **JSDoc** 风格注释（支持 TypeScript 类型提示）
- 除 `// TODO` 或 `// FIXME` 外，严禁使用单行注释（`//`），复杂逻辑必须用 JSDoc 块注释解释
- 注释语言首选英文
- 所有导出组件、hooks、函数必须添加 JSDoc 描述
  示例：
  ```tsx
  /**
   * UserCard component displays user information.
   *
   * @param {UserCardProps} props - Component props
   * @returns {JSX.Element} Rendered component
   */
  export const UserCard: FC<UserCardProps> = ({ user }) => { ... }
  ```

## 4. 代码复杂度
### 4.1 分支复杂度
- 单一组件/函数严禁超过 100 行（含 JSX 和注释），复杂组件除外
- 复杂组件可以使用详细 JSDoc 解释，但纯逻辑代码部分严禁超过 60 行
- 鼓励拆分：大组件拆分为小组件，复杂逻辑提取为自定义 hooks

### 4.2 Props 与调用复杂度
- Props 个数 ≤ 3 的组件：允许解构使用，也允许直接访问
- Props 个数 ≥ 4 的组件：必须定义明确接口（`interface XXXProps`），并在调用时使用扩展语法（`{...props}`）或显式传递
- 组件 Props 必须显式定义 TypeScript 接口，禁止使用 `any` 或隐式 `PropsWithChildren`

## 5. TypeScript 配置（死规定）
- 必须启用 **strict: true**（包括 `strictNullChecks`、`noImplicitAny` 等所有严格选项）
- 禁止使用 `any`，必须使用 `unknown` 或具体类型
- 所有组件使用函数式组件 + React.FC 或明确返回类型
- 禁止 `as any` 类型断言，除非极端必要并添加注释解释
- 推荐使用 `satisfies` 关键字验证类型

## 6. React 最佳实践
- 统一使用 **函数式组件** 和 **Hooks**，严禁类组件
- 组件文件名与导出组件名一致（PascalCase）
- JSX 中禁止内联函数定义（除简单场景），复杂回调提取为 useCallback
- 状态管理优先使用 React Context + useReducer 或轻量库（如 Zustand），避免过度使用 Redux
- 所有组件默认导出，禁止多个导出组件同文件

## 7. 工具与风格统一（死规定）
- 必须集成 **ESLint** + **Prettier**，推荐基于 Airbnb（带 TypeScript 支持）或 @typescript-eslint/recommended
- 禁止禁用 ESLint 规则（`// eslint-disable-line`），必须修复问题
- 代码格式由 Prettier 统一处理（单引号、尾随逗号、2 空格缩进等）
- 推荐使用 **React StrictMode** 包裹根组件
- 路由统一使用 **React Router v6+** 的现代 API（如 `createBrowserRouter`）

# 三、API JSON 响应格式标准 -- 风格规范

## 1. 响应格式
```json
{
  "code": 0,
  "data": null,
  "msg": "success",
  "msg_code": "SUCCESS",
  "log_id": "20250101120000123456789",
  "request_time": 1672531200000,
  "response_time": 1672531200123,
  "version": "1.0"
}
```

## 1. 状态码定义

### 成功码
- 0: 成功
- 100: 创建成功
- 102: 成功无内容

### 客户端错误码
- 1000: 请求参数错误
- 1001: 未认证
- 1002: 权限不足
- 1003: 资源不存在
- 1009: 数据验证失败
- 1204: 分页参数无效

### 服务端错误码
- 2000: 服务器内部错误
- 2002: 服务不可用
- 2100: 数据库错误

## 3. RESTful 接口规范
```
GET    /api/v1/resources          # 列表
POST   /api/v1/resources          # 创建
GET    /api/v1/resources/{id}     # 详情
PUT    /api/v1/resources/{id}     # 更新
DELETE /api/v1/resources/{id}     # 删除
```

## 4. 分页规范
请求参数：`limit`（默认20）, `offset`（默认0）, `sort`

分页响应：
```json
{
  "items": [],
  "pagination": {
    "total": 100,
    "limit": 20,
    "offset": 0,
    "has_previous": false,
    "has_next": true
  }
}
```

## 5. 示例
```json
{"code":0,"data":{},"msg":"success"}
{"code":0,"data":{"items":[],"pagination":{}}}
{"code":1000,"data":null,"msg":"参数错误"}
```
