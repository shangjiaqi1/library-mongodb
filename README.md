# 图书情报检索与统计平台（MongoDB 实训项目一）

《NoSQL 数据库技术与应用（第2版）》第3章 配套项目
班级：数科2班　学号：202414870230　姓名：尚佳琪

## 运行环境
- Python 3.9+、PyMongo 4.x
- 本机启动 MongoDB（mongod，端口 27017）；若未启动，程序会自动回退到内存版 mongomock 演示，仍可直接运行查看全部功能。
- 安装依赖：`pip install pymongo`（可选 `pip install mongomock`）

## 文件结构
```
books.txt / readers.txt / borrow_logs.txt   配套数据集（导入用）
mongodb_connect.py   数据库连接、建库建集合、特殊集合、索引、数据导入
book_manager.py      图书增删改查、条件检索、评分排行（Q1-Q16 / U1-U4）
reader_manager.py    读者信息、学院统计、等级分布（Q4 / D3）
borrow_manager.py    借阅登记、归还、逾期查询（D1/D2）
stat_manager.py      聚合统计报表（A1-A9：分类/趋势/畅销/活跃/$lookup/$merge）
main.py              菜单式交互主程序（--demo 自动演示）
screenshots/         覆盖六个任务的运行截图
docs/                实验报告 Word + 技术文档
```

## 运行方式
```bash
python3 mongodb_connect.py     # 验证连接与数据导入
python3 main.py                # 进入交互菜单
python3 main.py --demo         # 一次性自动演示全部功能（截图用）
```

## 六个任务对应
1. 环境部署：mongod 27017、自定义数据目录
2. 数据建模：library 库 + books/readers/borrow_logs/category_stats；固定集合 book_logs、时间序列 borrow_logs、视图 book_in_stock
3. 检索实现：16 条查询 + 更新删除
4. 统计与权限：9 条聚合管道 + 索引
5. 程序开发：上述 6 个 Python 文件
6. 验收交付：Compass 核对、导出 category_stats 与 books
