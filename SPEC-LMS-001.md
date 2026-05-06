# SPEC-LMS-001：初中生学习管理系统

---

## 3.0 元数据

| 字段 | 值 |
|:---|:---|
| **Spec ID** | SPEC-LMS-001 |
| **项目名称** | 初中生学习管理系统（Junior Learning Management System） |
| **版本** | v1.0.0 Draft |
| **状态** | Draft |
| **创建日期** | 2026-05-02 |
| **负责人** | 待填写 |
| **目标用户** | 初中生（学生本人）+ 家长 |
| **使用场景** | 家庭自用，单一学生数据 |
| **关联需求** | 无（个人项目） |

---

## 3.1 背景与目标

### 1.1 业务背景

初中阶段科目多（9门）、知识点密集，学生普遍面临以下痛点：

- 错题分散在各科目练习册，无法系统化复习
- 复习缺乏科学计划，容易遗忘已学知识
- 家长无法直观了解孩子的学习薄弱点
- 学习效果缺乏可视化反馈，难以持续维持学习动力

### 1.2 核心价值

| 价值维度 | 描述 |
|:---|:---|
| 效率提升 | 通过艾宾浩斯遗忘曲线自动生成复习计划，避免低效重复 |
| 薄弱识别 | 自动统计错题模式，精准识别薄弱知识点 |
| 家校协同 | 家长可查看学习数据并协助制定复习计划 |
| 持续激励 | 可视化掌握度进度，给学生正向反馈 |

### 1.3 量化目标（供确认）

> ⚠️ 以下指标为草稿，请确认是否符合实际预期：

- 错题录入操作：从打开页面到完成一条录入 ≤ 3 分钟
- 复习提醒响应：每次打开首页，今日待复习任务显示延迟 ≤ 1 秒
- 系统可用性：本地部署，目标 99% 以上（排除硬件故障）

---

## 3.2 存量事实基准

> 本项目为**全新开发**，无存量代码库。

| 类型 | 说明 |
|:---|:---|
| 禁止变更清单 | 无（新项目） |
| 已有接口 | 无 |
| 已有数据库 | 无，需新建 SQLite 数据库文件 |
| 外部依赖 | 无已有对接，相似题推荐接口 MVP 阶段跳过 |

---

## 3.3 增量变更描述

### 3.3.1 新增模块列表

| 模块编号 | 模块名称 | 说明 |
|:---|:---|:---|
| MOD-01 | 角色切换模块 | 无需登录，顶部一键切换“学生模式/家长模式”，角色状态存于 Session |
| MOD-02 | 复习管理模块 | 艾宾浩斯计划生成、进度跟踪、网页内提醒 |
| MOD-03 | 错题管理模块 | 错题 CRUD、图片上传、富文本/公式、统计分析 |
| MOD-04 | 知识掌握追踪模块 | 掌握度自动计算、可视化图表、趋势分析 |
| MOD-05 | AI分析模块 | 规则引擎实现：错题模式分析、学习预测、周期报告 |
| MOD-06 | 家长视图模块 | 家长查看+辅助设置，权限隔离 |

### 3.3.2 科目与年级范围

系统预置以下9门科目（支持初一～初三全年级）：

`语文` `数学` `英语` `物理` `化学` `生物` `历史` `地理` `政治`

> 注：物理、化学、生物通常初二/初三才有，系统不做年级强制限制，学生自主管理。

### 3.3.3 极端场景处理策略

| 场景 | 处理策略 |
|:---|:---|
| 图片上传超大文件 | 限制单张图片 ≤ 5MB，前端提示压缩 |
| SQLite 文件损坏 | 提供数据库备份/导出功能，定期导出提醒 |
| 公式渲染失败 | 降级显示原始 LaTeX 文本，不影响其他功能 |
| 艾宾浩斯计划堆积（长期未打开） | 显示实际到期任务，超过14天未复习的任务标记为“已逾期”，不强制补做 |
| 并发访问 | 家庭自用场景，不考虑多设备并发，SQLite 单写足够 |

---

## 3.4 隐形边界声明

### 3.4.1 幂等性

| 操作 | 幂等要求 |
|:---|:---|
| 错题录入 | 无需幂等，允许重复录入（同题目可多次错） |
| 复习计划生成 | 幂等：同一知识点同一阶段只生成一条计划，重复调用不新增 |
| 复习完成标记 | 幂等：同一天同一知识点多次标记完成，只记录一次 |

### 3.4.2 并发安全

> 家庭自用，同一时间只有一个用户操作，SQLite 默认串行写入即可满足需求。无需分布式锁。

### 3.4.3 分布式事务

> 无分布式场景。所有数据操作在单一 SQLite 文件上，使用 Python 的数据库事务（`with conn:` 自动提交/回滚）。

### 3.4.4 错误分类

| 错误类型 | 处理方式 |
|:---|:---|
| 表单验证失败（空字段/格式错误） | 不可重试，返回表单级错误提示 |
| 图片上传失败（文件过大/格式不支持） | 不可重试，提示具体原因 |
| SQLite 写入失败 | 记录错误日志，页面提示“保存失败，请重试” |
| 公式渲染失败 | 静默降级，不影响主流程 |

### 3.4.5 时间语义

| 规则 | 说明 |
|:---|:---|
| 时间存储格式 | 统一使用 `TEXT` 类型存储 ISO 8601 格式（`YYYY-MM-DD HH:MM:SS`） |
| 时区策略 | 统一使用本机本地时区（家庭自用，无跨时区需求） |
| 艾宾浩斯日期计算 | 基于日期（`date`），不精确到时分秒，以“天”为单位 |
| “今日到期”判断 | `next_review_date <= 今日日期` |

### 3.4.6 数据安全

| 规则 | 说明 |
|:---|:---|
| 无认证设计 | 家庭自用，无密码登录，通过 Session 区分角色（student/parent）|
| Session | Flask 内置 Session，SECRET_KEY 随机生成，存储当前角色标识 |
| 图片文件 | 存储在服务端本地目录，通过应用路由访问，不直接暴露文件系统路径 |
| 缩略图 | 上传时 Pillow 生成缩略图（限宽 800px），原图与缩略图均落盘保存 |
| 日志中禁止输出 | Session 内容、文件系统绝对路径 |
| SQLite 文件 | 存储在应用目录下，不放在 Web 可访问的 static 目录内 |

---

## 3.5 CodeAnchor

> 本项目为新建项目，无存量代码库。以下为**待实现的核心接口定义**，作为实现阶段的锁点。

| 锁点编号 | 逻辑接口名 | 所在模块 | 说明 |
|:---|:---|:---|:---|
| ANC-01 | `RoleService.switch_role(role)` | MOD-01 | 切换当前角色写入 Session（student/parent）|
| ANC-02 | `ReviewService.generate_plan()` | MOD-02 | 基于艾宾浩斯曲线生成/更新复习计划 |
| ANC-03 | `ReviewService.get_today_tasks()` | MOD-02 | 查询今日待复习任务列表 |
| ANC-04 | `ReviewService.mark_complete()` | MOD-02 | 标记知识点复习完成，推进到下一阶段 |
| ANC-05 | `WrongQuestionService.create()` | MOD-03 | 录入错题（含图片上传处理） |
| ANC-06 | `WrongQuestionService.get_stats()` | MOD-03 | 统计错题数据（错误率、高频错题） |
| ANC-07 | `MasteryService.calculate_score()` | MOD-04 | 根据错题和复习数据计算知识点掌握度 |
| ANC-08 | `AIAnalysisService.analyze_weak_points()` | MOD-05 | 规则引擎分析薄弱知识点 |
| ANC-09 | `AIAnalysisService.generate_report()` | MOD-05 | 生成周/月学情报告 |
| ANC-10 | `AIAnalysisService.predict_forgetting_risk()` | MOD-05 | 预测近期遗忘风险知识点 |

---

## 3.6 第三方 API 契约

### 3.6.1 相似题推荐 API（MVP 跳过）

> ⚠️ **MVP 阶段此功能跳过，接口预留。** 第三方题库 API 尚未确定，以下为预留的扩展接口规范模板，待未来确定合作方后补全。

```python
# 预留扩展点（MOD-03 中注释占位）
class SimilarQuestionProvider:
    """
    相似题目推荐接口预留
    TODO: 对接第三方题库 API 后实现
    """
    def get_similar_questions(self, knowledge_point: str, subject: str) -> list:
        raise NotImplementedError("相似题推荐功能将在后续版本实现")
```

### 3.6.2 公式渲染库

| 库 | 版本（已确认）| 用途 |
|:---|:---|:---|
| KaTeX | 0.16.x（CDN） | 数学公式渲染（LaTeX 格式），轻量快速 |
| Quill.js | 2.x（CDN） | 富文本编辑器，支持自定义公式模块 |

---

## 3.7 数据模型

### 数据库文件：`lms.db`（SQLite）

---

#### 表 1：users（用户表）

```sql
CREATE TABLE users (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    role         TEXT NOT NULL CHECK(role IN ('student', 'parent')),
    display_name TEXT NOT NULL,
    created_at   TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- 初始数据（init_db.py 自动写入，无需密码）
-- INSERT INTO users(role, display_name) VALUES ('student', '同学');
-- INSERT INTO users(role, display_name) VALUES ('parent',  '家长');
```

---

#### 表 2：subjects（科目表）

```sql
CREATE TABLE subjects (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL UNIQUE,
    icon    TEXT,   -- emoji 图标，如 📐
    color   TEXT    -- 主题色，如 #4A90D9
);

-- 预置数据
-- 语文、数学、英语、物理、化学、生物、历史、地理、政治
```

---

#### 表 3：knowledge_points（知识点表）

```sql
CREATE TABLE knowledge_points (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id  INTEGER NOT NULL REFERENCES subjects(id),
    chapter     TEXT NOT NULL,   -- 章节名，如“第三章 方程与不等式”
    name        TEXT NOT NULL,   -- 知识点名，如“一元二次方程”
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
```

---

#### 表 4：wrong_questions（错题表）

```sql
CREATE TABLE wrong_questions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id          INTEGER NOT NULL REFERENCES users(id),
                        -- 单一学生系统，始终引用 id=1 的学生记录
    subject_id          INTEGER NOT NULL REFERENCES subjects(id),
    knowledge_point_id  INTEGER REFERENCES knowledge_points(id),
    question_content    TEXT NOT NULL,   -- 富文本 HTML 内容
    image_path          TEXT,            -- 图片相对路径，可为空
    answer_content      TEXT,            -- 正确答案/解析，富文本
    difficulty          INTEGER NOT NULL DEFAULT 2 CHECK(difficulty IN (1,2,3)),
                        -- 1=简单 2=中等 3=困难
    error_count         INTEGER NOT NULL DEFAULT 1,   -- 错误次数
    last_error_date     TEXT NOT NULL DEFAULT (date('now', 'localtime')),
    is_mastered         INTEGER NOT NULL DEFAULT 0,   -- 0=未掌握 1=已掌握
    created_at          TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at          TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
```

---

#### 表 5：review_plans（复习计划表）

```sql
CREATE TABLE review_plans (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id          INTEGER NOT NULL REFERENCES users(id),
    knowledge_point_id  INTEGER NOT NULL REFERENCES knowledge_points(id),
    review_stage        INTEGER NOT NULL DEFAULT 1,
                        -- 艾宾浩斯阶段：1/2/3/4/5/6（6=已掌握）
    next_review_date    TEXT NOT NULL,   -- 下次复习日期 YYYY-MM-DD
    created_at          TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE(student_id, knowledge_point_id)  -- 每个知识点只有一条计划
);
```

**艾宾浩斯阶段对照表：**

| 阶段 | 距上次复习天数 | 含义 |
|:---|:---|:---|
| Stage 1 | +1 天 | 第二天复习 |
| Stage 2 | +3 天 | 第4天复习 |
| Stage 3 | +7 天 | 第11天复习 |
| Stage 4 | +14 天 | 第25天复习 |
| Stage 5 | +30 天 | 第55天复习 |
| Stage 6 | 已掌握 | 不再提醒 |

---

#### 表 6：review_records（复习记录表）

```sql
CREATE TABLE review_records (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id          INTEGER NOT NULL REFERENCES users(id),
    knowledge_point_id  INTEGER NOT NULL REFERENCES knowledge_points(id),
    review_date         TEXT NOT NULL,   -- 实际复习日期 YYYY-MM-DD
    result              TEXT NOT NULL CHECK(result IN ('pass', 'fail')),
                        -- pass=掌握 fail=还需再复习
    stage_before        INTEGER NOT NULL,
    stage_after         INTEGER NOT NULL,
    created_at          TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
```

---

#### 表 7：mastery_scores（掌握度记录表）

```sql
CREATE TABLE mastery_scores (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id          INTEGER NOT NULL REFERENCES users(id),
    knowledge_point_id  INTEGER NOT NULL REFERENCES knowledge_points(id),
    score               REAL NOT NULL DEFAULT 0.0,   -- 0.0~1.0
    last_updated        TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE(student_id, knowledge_point_id)
);
```

**掌握度计算规则：**

```
score = base_score × review_bonus × recency_factor

base_score:
  - 从未有错题：0.5（中性起点）
  - 错误次数 = 1：0.4
  - 错误次数 2-3：0.3
  - 错误次数 > 3：0.2（薄弱点）
  - 已标记掌握（is_mastered=1）：1.0

review_bonus（复习加成）:
  - 复习通过次数 1 次：×1.2
  - 复习通过次数 2-3 次：×1.5
  - 复习通过次数 ≥ 4 次：×1.8

recency_factor（近期因子）:
  - 30天内有复习记录：×1.0
  - 30-90天无复习：×0.8
  - 90天以上无复习：×0.6

最终 score 上限为 1.0，下限为 0.0
```

---

## 3.8 验收标准与 TDD 规划

### 3.8.1 核心验收场景（Given-When-Then）

---

**场景 AC-01：切换到学生模式**

```
Given  用户打开系统（默认进入学生模式）
When   页面加载完成
Then   顶部角色标识显示“学生模式”
And    首页顶部显示“今日待复习任务” banner
And    “录入错题”等学生专属操作入口可见
```

**场景 AC-02：切换到家长模式后查看学习数据**

```
Given  用户在顶部点击“切换到家长模式”按鈕
When   角色切换完成（Session 中 role = parent）
Then   顶部角色标识更新为“家长模式”
And    可以看到学生各科目的掌握度进度条
And    可以看到本周错题新增数量
And    “录入错题”等学生专属操作入口不可见
```

**场景 AC-03：录入一道数学错题（含图片和公式）**

```
Given  学生已登录，进入错题管理页面
When   选择科目“数学”，选择知识点“一元二次方程”
And    在富文本编辑器中输入题目内容，插入公式 $x^2 - 5x + 6 = 0$
And    上传一张题目图片（≤5MB）
And    点击“保存”
Then   错题列表出现新录入的错题
And    公式正确渲染显示
And    图片正常展示
And    该知识点的掌握度分数自动降低
```

**场景 AC-04：复习计划自动生成**

```
Given  学生录入了一道“勾股定理”知识点的错题
When   系统生成复习计划
Then   数据库中出现一条 review_plans 记录
And    next_review_date = 录入日期 + 1天
And    review_stage = 1
```

**场景 AC-05：今日待复习提醒**

```
Given  某知识点的 next_review_date = 今天
When   学生打开系统首页
Then   首页顶部显示“今日待复习 N 项”提示
And    点击可展开查看具体知识点列表
```

**场景 AC-06：复习完成后推进阶段**

```
Given  学生查看今日复习任务，点击某条任务的“已复习-通过”
When   系统处理复习结果
Then   该知识点的 review_stage 从 1 推进到 2
And    next_review_date 更新为 今天 + 3天
And    生成一条 review_records 记录（result='pass'）
And    该知识点掌握度分数提升
```

**场景 AC-07：复习未通过**

```
Given  学生点击“已复习-未通过”
When   系统处理复习结果
Then   review_stage 不推进（保持当前阶段）
And    next_review_date 更新为 今天 + 当前阶段对应天数
And    生成一条 review_records（result='fail'）
And    该知识点掌握度分数不提升
```

**场景 AC-08：AI薄弱点分析**

```
Given  某知识点“分式方程”的 error_count = 4
When   进入 AI 分析页面
Then   该知识点在“薄弱点清单”中高亮显示
And    显示“建议重点复习”标签
```

**场景 AC-09：错题统计**

```
Given  学生在错题管理页面
When   查看统计分析
Then   显示各科目错题数量柱状图
And    显示错误率0的知识点列表
And    显示近30天错题新增趋势折线图
```

**场景 AC-10：图片上传超限**

```
Given  学生尝试上传一张 8MB 的图片
When   选择文件后
Then   系统拒绝上传
And    提示“图片大小不能超过 5MB，请压缩后重试”
And    不影响其他表单字段内容
```

---

## 3.9 实施计划

### 阶段划分（共 6 个迭代，每迭代可独立验证）

---

#### Task 1：项目初始化 + 角色切换模块（MOD-01）

**目标：** 可运行的基础框架 + 无需登录的角色切换

- [ ] 初始化 Flask 项目结构（含 routes/services/templates/static 目录）
- [ ] 配置 SQLite 连接，实现数据库初始化脚本（`init_db.py`）
- [ ] 实现首页（Dashboard）Jinja2 模板，默认学生模式
- [ ] 实现顶部角色切换按鈕（学生模式 ⇔ 家长模式）
- [ ] 实现 `RoleService.switch_role()`：切换角色写入 Flask Session
- [ ] 实现路由角色装饰器（家长路由只允许 parent Session 访问）
- [ ] 配置 waitress 作为 Windows 生产服务器

**验证：** 首页正常显示，角色切换后页面元素按权限显示/隐藏

**本 Task 必须注入的上下文：**
- Flask Session 配置方式（SECRET_KEY）
- waitress 在 Windows 下的安装和启动方式
- SQLite WAL 模式配置

---

#### Task 2：基础数据管理（科目/知识点）

**目标：** 科目、章节、知识点的基础 CRUD

- [ ] 创建 subjects、knowledge_points 表
- [ ] 预置9门科目数据
- [ ] 实现知识点管理页面（增删改查）
- [ ] 实现按科目/章节的树形展示

**验证：** 能完整管理知识点层级结构

---

#### Task 3：错题管理模块（MOD-03）

**目标：** 完整的错题录入、编辑、删除、分类

- [ ] 创建 wrong_questions 表
- [ ] 集成富文本编辑器 Quill.js 2.x
- [ ] 集成公式渲染 KaTeX 0.16.x
- [ ] 实现图片上传接口（限制 5MB，存储到本地目录）
- [ ] 上传时用 Pillow 生成缩略图（限宽 800px，保存为 `_thumb` 后缀文件）
- [ ] 实现图片访问路由（角色鉴权保护）
- [ ] 实现 `WrongQuestionService.create/update/delete()`
- [ ] 实现错题列表（按科目/知识点/难度筛选）
- [ ] 实现 `WrongQuestionService.get_stats()`
- [ ] 实现错题统计页面（Chart.js 图表）

**验证：** 覆盖 AC-03、AC-09、AC-10

**本 Task 必须注入的上下文：**
- Quill.js 2.x 集成文档（含自定义 toolbar 配置）
- KaTeX 0.16.x CDN 引入方式 + quill-better-table/公式模块配置
- Flask 文件上传最佳实践（Pillow 校验 MIME 类型）

---

#### Task 4：复习管理模块（MOD-02）

**目标：** 艾宾浩斯计划生成 + 今日提醒

- [ ] 创建 review_plans、review_records 表
- [ ] 实现 `ReviewService.generate_plan()`（录入错题时自动触发）
- [ ] 实现 `ReviewService.get_today_tasks()`
- [ ] 实现 `ReviewService.mark_complete()`（pass/fail 两种结果）
- [ ] 实现首页“今日待复习” banner 组件
- [ ] 实现复习任务列表页面
- [ ] 实现逾期任务标记逻辑（超过14天）

**验证：** 覆盖 AC-04、AC-05、AC-06、AC-07

---

#### Task 5：知识掌握追踪 + AI分析模块（MOD-04 + MOD-05）

**目标：** 掌握度可视化 + 规则引擎分析

- [ ] 创建 mastery_scores 表
- [ ] 实现 `MasteryService.calculate_score()`（按公式计算）
- [ ] 实现掌握度自动更新触发点（录入错题时、复习完成时）
- [ ] 实现各科目掌握度进度条页面（Chart.js）
- [ ] 实现知识点掌握度雷达图/热力图
- [ ] 实现学习趋势折线图（近30天/90天）
- [ ] 实现 `AIAnalysisService.analyze_weak_points()`
- [ ] 实现 `AIAnalysisService.predict_forgetting_risk()`
- [ ] 实现 `AIAnalysisService.generate_report()`（周/月报告模板）
- [ ] 实现 AI 分析页面
- [ ] 预留 `SimilarQuestionProvider` 扩展接口（注释占位）

**验证：** 覆盖 AC-08

---

#### Task 6：家长视图 + 系统完善（MOD-06）

**目标：** 家长权限视图 + 数据备份 + 最终打磨

- [ ] 实现家长专属路由组（只读 + 辅助设置）
- [ ] 家长可查看所有统计图表（只读）
- [ ] 家长可为学生设置复习提醒偏好（提醒展示时间等）
- [ ] 实现数据库备份导出功能（下载 lms.db）
- [ ] 实现响应式布局适配（手机/平板/PC）
- [ ] UI 最终视觉打磨（青少年配色主题）

**验证：** 覆盖 AC-02，完整系统端到端测试

---

## 3.10 环境配置

### 3.10.1 Runtime Profile

> ⚠️ 以下版本号为推荐版本，请根据实际安装情况确认：

| 组件 | 推荐版本 | 说明 |
|:---|:---|:---|
| Python | 3.11+ | 应用运行时 |
| Flask | 3.x | Web 框架 |
| Flask-Session | 0.8+ | 服务端 Session |
| Pillow | 10.x | 图片处理/缩略图生成（限宽 800px）|
| waitress | 3.x | Windows 生产 WSGI 服务器 |
| SQLite | 3.39+（内置） | 数据库 |
| Chart.js | 4.x（CDN） | 前端图表 |
| KaTeX | 0.16.x（CDN） | 公式渲染（已确认） |
| Quill.js | 2.x（CDN） | 富文本编辑器（已确认） |

### 3.10.2 目录结构（参考）

```
learn/
├── app.py                  # Flask 应用入口
├── config.py               # 配置文件
├── lms.db                  # SQLite 数据库（不放入 Web 静态目录）
├── init_db.py              # 数据库初始化脚本
├── requirements.txt
├── services/
│   ├── role_service.py
│   ├── review_service.py
│   ├── wrong_question_service.py
│   ├── mastery_service.py
│   └── ai_analysis_service.py
├── routes/
│   ├── role.py
│   ├── review.py
│   ├── wrong_question.py
│   ├── mastery.py
│   ├── ai_analysis.py
│   └── parent.py
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   └── ...
├── static/
│   ├── css/
│   ├── js/
│   └── uploads/
│       ├── *.jpg/png         # 原图
│       └── thumbs/           # 缩略图（Pillow 限宽 800px）
└── tests/
    └── ...
```

### 3.10.3 启动命令

```bash
# 初始化数据库（首次运行）
python init_db.py

# 开发模式启动
flask run --debug --port 5000

# 生产模式（Windows，使用 waitress）
waitress-serve --host=127.0.0.1 --port=5000 app:app
```

### 3.10.4 配置项清单

> ⚠️ 以下配置值请在 `config.py` 或 `.env` 文件中填写真实值，不要硬编码：

| 配置项 | 说明 | 示例占位 |
|:---|:---|:---|
| `SECRET_KEY` | Flask Session 加密密锐 | 随机生成 32 位字符串 |
| `DATABASE_PATH` | SQLite 文件路径 | `./lms.db` |
| `UPLOAD_FOLDER` | 图片上传目录 | `./static/uploads` |
| `THUMBNAIL_FOLDER` | 缩略图存储目录 | `./static/uploads/thumbs` |
| `THUMBNAIL_MAX_WIDTH` | 缩略图最大宽度（px）| `800` |
| `MAX_CONTENT_LENGTH` | 最大上传文件大小 | `5 * 1024 * 1024`（5MB）|

---

## 3.11 异常码定义

| 异常码 | 含义 | HTTP 状态码 |
|:---|:---|:---|
| `ROLE_001` | 角色不允许访问此资源（家长访问学生专属功能）| 403 |
| `UPLOAD_001` | 图片文件过大（>5MB）| 400 |
| `UPLOAD_002` | 不支持的图片格式 | 400 |
| `DB_001` | 数据库写入失败 | 500 |
| `VALID_001` | 表单必填字段为空 | 400 |
| `VALID_002` | 知识点不存在 | 400 |

---

## 3.12 审查清单

### AI 可自动检查项

- [ ] Python 代码通过 `flake8` / `pylint` 检查
- [ ] 无 `print()` 调试语句残留
- [ ] 无 `TODO` / `FIXME` 遗留（除已标注的 `SimilarQuestionProvider` 占位）
- [ ] 所有路由都有权限装饰器保护
- [ ] 图片路径未直接暴露到前端 URL 中

### 人工检查项（开发者确认）

- [ ] 实现逻辑与 3.3 增量变更描述一致
- [ ] 艾宾浩斯阶段推进逻辑与 3.7 表 5 对照表一致
- [ ] 掌握度计算公式与 3.7 表 7 规则一致
- [ ] 家长路由与学生路由角色隔离无遗漏
- [ ] 图片访问路由有角色鉴权，防止未授权访问
- [ ] 缩略图生成逻辑正确（限宽 800px，原图和缩略图均应存在）
- [ ] SQLite 文件不在 Web 可访问的 static 目录内
- [ ] 所有数据库写操作使用事务

---

## 3.13 部署契约

> 🚫 以下内容为本地部署场景，DevOps/开发者按实际环境填写：

| 项目 | 值 | 状态 |
|:---|:---|:---|
| 操作系统 | **Windows** | ✅ 已确认 |
| Python 版本 | 3.11+ | ✅ |
| 端口 | 5000（开发）/ 可自定义 | 待确认 |
| 数据库文件路径 | `./lms.db` | ✅ |
| 图片存储路径 | `./static/uploads/` | ✅ |
| 缩略图目录 | `./static/uploads/thumbs/` | ✅ |
| 备份策略 | 手动导出 lms.db 文件 | 🚫 待制定 |
| 进程管理 | **waitress 3.x**（Windows 原生支持）| ✅ 已确认 |

---

## 4.0 四道质量门禁

```
╔════════════════════════════════════════════╗
║     GATE 1: 事实基准审核（开发者确认）         ║
╠════════════════════════════════════════════╣
║ ☐ 数据模型（3.7）是否满足所有功能需求？        ║
║ ✅ 艾宾浩斯阶段：1/3/7/14/30天（已确认）         ║
║ ☐ 掌握度计算公式是否合理？                   ║
║ ✅ 无密码，角色切换器已确认               ║
╚════════════════════════════════════════════╝

╔════════════════════════════════════════════╗
║     GATE 2: 技术契约审核（开发者确认）         ║
╠════════════════════════════════════════════╣
║ ✅ 富文本编辑器：Quill.js 2.x（已确认）         ║
║ ✅ 公式渲染库：KaTeX 0.16.x（已确认）          ║
║ ☐ Runtime Profile 版本与实际安装一致？         ║
║ ☐ 图片存储目录权限配置正确？                  ║
╚════════════════════════════════════════════╝

╔════════════════════════════════════════════╗
║     GATE 3: 测试规划审核（开发者确认）         ║
╠════════════════════════════════════════════╣
║ ☐ AC-01 ~ AC-10 验收场景是否覆盖核心路径？     ║
║ ☐ 异常分支（AC-10 图片超限等）是否有测试？      ║
║ ☐ 艾宾浩斯边界値（Stage 6）是否有测试？        ║
╚════════════════════════════════════════════╝

╔════════════════════════════════════════════╗
║     GATE 4: 测试质量门禁（实现完成后执行）🆕   ║
╠════════════════════════════════════════════╣
║ ☐ 每个 GWT 场景有对应测试方法？               ║
║ ☐ 掌握度计算逻辑有边界値测试？                ║
║ ☐ 艾宾浩斯阶段推进逻辑有完整测试？            ║
║ ☐ 图片上传限制有测试覆盖？                   ║
╚════════════════════════════════════════════╝
```

---

## 5.0 待确认事项汇总

> 以下为 Spec 起草过程中标记的待确认项，请逐一确认后进入实现阶段：

| 编号 | 待确认内容 | 负责人 |
|:---|:---|:---|
| Q1 | 量化指标（3.1.3）是否符合预期？ | 产品确认 |
| Q2 | ✅ 富文本编辑器：**Quill.js 2.x** | 已确认 |
| Q3 | ✅ 公式渲染库：**KaTeX 0.16.x** | 已确认 |
| Q4 | 掌握度计算公式（3.7 表7）是否合理？ | 产品确认 |
| Q5 | ✅ 艾宾浩斯各阶段天数：**1/3/7/14/30天** | 已确认 |
| Q6 | ✅ **无需密码**，改为角色切换器（顶部一键切换学生/家长模式）| 已确认 |
| Q7 | ✅ **Windows** 环境，使用 waitress 作为 WSGI 服务器 | 已确认 |
| Q8 | ✅ **需要缩略图**，Pillow 限宽 800px 压缩，原图+缩略图均保存 | 已确认 |

---

*Spec 版本: v1.0.0 Draft | 生成日期: 2026-05-02*
*下一步：确认 Q1~Q8 后，经过四道 Quality Gates 审核，方可进入实现阶段*
