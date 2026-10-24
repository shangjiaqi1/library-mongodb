# -*- coding: utf-8 -*-
"""
mongodb_connect.py
《NoSQL 数据库技术与应用（第2版）》第3章 实训项目一 —— 图书情报检索与统计平台
数据库连接与初始化模块（任务一 / 任务二）

职责：
  1. 封装获取 MongoDB 数据库连接的逻辑（MongoClient，统一连接参数）；
  2. 建库 library，创建 books / readers / borrow_logs / category_stats 四个集合；
  3. 创建三种特殊集合：固定集合 book_logs、时间序列集合 borrow_logs、视图 book_in_stock；
  4. 从 books.txt / readers.txt / borrow_logs.txt 导入配套数据集；
  5. 建立高频查询索引（I1—I5）。

说明：本模块默认连接本机 mongod（mongodb://localhost:27017/）。
若本机未启动 MongoDB，程序会自动回退到内存版 mongomock，
保证“6 个文件能够直接运行”并可演示全部功能；在真实 MongoDB 环境下
会自动创建时间序列集合、固定集合与视图等全部高级对象。
"""

import os
import json
from datetime import datetime

from pymongo import MongoClient, ASCENDING, DESCENDING

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILES = {
    "books": os.path.join(BASE_DIR, "books.txt"),
    "readers": os.path.join(BASE_DIR, "readers.txt"),
    "borrow_logs": os.path.join(BASE_DIR, "borrow_logs.txt"),
}

DB_NAME = "library"
DEFAULT_URI = "mongodb://localhost:27017/"

# 运行环境标记，供其它模块与报告区分“真实 MongoDB / 内存演示”
ENV = {"using_mock": False}


def _convert_dates(obj):
    """把数据文件里的 {"$date": "..."} 递归转换为 Python datetime 对象。"""
    if isinstance(obj, dict):
        if "$date" in obj and len(obj) == 1:
            return datetime.fromisoformat(obj["$date"].replace("Z", "+00:00"))
        return {k: _convert_dates(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_dates(v) for v in obj]
    return obj


def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return _convert_dates(json.load(f))


def get_client():
    """建立并返回 MongoClient。真实连接失败时回退到 mongomock 内存库。"""
    try:
        client = MongoClient(DEFAULT_URI, serverSelectionTimeoutMS=1500)
        client.admin.command("ping")           # 探测真实 mongod 是否在线
        ENV["using_mock"] = False
        return client
    except Exception:
        try:
            import mongomock
            ENV["using_mock"] = True
            return mongomock.MongoClient()
        except Exception:
            raise RuntimeError(
                "既无法连接本机 MongoDB（localhost:27017），也未安装 mongomock，"
                "请先启动 mongod 或执行 pip install mongomock。"
            )


def _ensure_special_collections(db):
    """任务二 ST-2.2：创建三种特殊集合（真实 MongoDB 生效，内存环境自动降级为普通集合）。"""
    existing = set(db.list_collection_names())

    # ① 固定集合 book_logs：容量上限 1MB，最多 1000 条文档
    if "book_logs" not in existing:
        try:
            db.create_collection(
                "book_logs", capped=True, size=1048576, max=1000
            )
        except Exception:
            db.create_collection("book_logs")

    # ② 时间序列集合 borrow_logs：时间字段 borrow_date，粒度 hours，文档过期 2 年
    if "borrow_logs" not in existing:
        try:
            db.create_collection(
                "borrow_logs",
                timeseries={
                    "timeField": "borrow_date",
                    "granularity": "hours",
                    "expireAfterSeconds": 63072000,   # 2 年
                },
            )
        except Exception:
            db.create_collection("borrow_logs")

    # ③ 视图 book_in_stock：基于 books 过滤出 stock > 0 的图书
    if "book_in_stock" not in existing:
        try:
            db.command(
                "create", "book_in_stock",
                viewOn="books",
                pipeline=[{"$match": {"stock": {"$gt": 0}}}],
            )
        except Exception:
            pass  # 内存环境不支持视图，跳过


def _import_data(db):
    """任务二 ST-2.3：用 insert_one 录入一条样例，再用 insert_many 批量录入其余数据。"""
    if db.books.count_documents({}) > 0:
        return  # 已导入，避免重复

    books = _load_json(DATA_FILES["books"])
    readers = _load_json(DATA_FILES["readers"])
    logs = _load_json(DATA_FILES["borrow_logs"])

    # insert_one：单独录入第一条图书，观察返回的 inserted_id
    first, rest = books[0], books[1:]
    res = db.books.insert_one(first)
    db.books.insert_many(rest)

    db.readers.insert_many(readers)
    db.borrow_logs.insert_many(logs)

    # 建一个空的统计结果集合，供任务四 A9 $merge 写入
    if "category_stats" not in db.list_collection_names():
        db.create_collection("category_stats")

    return res.inserted_id


def _create_indexes(db):
    """任务四 I1—I5：为高频查询字段建立索引。"""
    db.books.create_index([("isbn", ASCENDING)], unique=True, name="uniq_isbn")   # I1 唯一索引
    db.books.create_index([("title", ASCENDING)], name="idx_title")                # I2 单键
    db.books.create_index([("category", ASCENDING)], name="idx_category")          # I3 单键
    db.books.create_index([("tags", ASCENDING)], name="idx_tags")                  # I4 多键
    db.books.create_index([("category", ASCENDING), ("price", ASCENDING)],
                          name="idx_cat_price")                                    # I5 复合
    db.readers.create_index([("card_no", ASCENDING)], unique=True)
    db.borrow_logs.create_index([("reader_card", ASCENDING)])
    db.borrow_logs.create_index([("book_isbn", ASCENDING)])


def get_db():
    """获取 library 数据库，并在首次调用时完成建库、建集合、导入与建索引。"""
    client = get_client()
    db = client[DB_NAME]
    _ensure_special_collections(db)
    _import_data(db)
    _create_indexes(db)
    return db


def collection_counts(db):
    """返回各集合文档数量，供启动时打印核对。"""
    names = ["books", "readers", "borrow_logs", "category_stats",
             "book_logs", "book_in_stock"]
    info = {}
    for n in names:
        try:
            info[n] = db[n].count_documents({})
        except Exception:
            info[n] = "视图/不可计数"
    return info


if __name__ == "__main__":
    db = get_db()
    print("已连接数据库：", DB_NAME,
          "（真实 MongoDB）" if not ENV["using_mock"] else "（内存演示 mongomock）")
    for k, v in collection_counts(db).items():
        print(f"  集合 {k:14s} 文档数 = {v}")
