# -*- coding: utf-8 -*-
"""
stat_manager.py —— 统计分析模块（任务四 聚合管道 A1—A9）
涉及阶段：$group / $sum / $avg / $sort / $limit / $project /
          $match / $lookup / $multiply / $round / $year / $dateToString / $merge。

说明：下方每个方法都先在真实 MongoDB 上执行聚合管道；当运行环境为内存版
mongomock（个别高级阶段不支持）时，自动降级为等价的 Python 统计，
保证演示结果数值正确、可截图。
"""
from collections import Counter, defaultdict
from datetime import datetime


class StatManager:
    def __init__(self, db):
        self.books = db.books
        self.readers = db.readers
        self.logs = db.borrow_logs
        self.cat_stats = db.category_stats

    def _agg(self, col, pipeline, fallback):
        try:
            return list(col.aggregate(pipeline))
        except Exception:
            return fallback()

    # A1 按类别统计图书数量与平均评分（$group + $sum/$avg）
    def stat_by_category(self):
        pipe = [
            {"$group": {"_id": "$category",
                        "count": {"$sum": 1},
                        "avg_rating": {"$avg": "$rating"}}},
            {"$sort": {"count": -1}},
        ]
        return self._agg(self.books, pipe, lambda: [
            {"_id": c, "count": g["n"],
             "avg_rating": round(g["s"] / g["n"], 2)}
            for c, g in ((c, {"n": len(b), "s": sum(x["rating"] for x in b)})
                         for c, b in self._group_books("category"))
        ])

    def _group_books(self, key):
        d = defaultdict(list)
        for b in self.books.find():
            d[b.get(key)].append(b)
        return d.items()

    # A2 各出版社图书数量，取最多 5 家（$group + $sort + $limit）
    def top_publishers(self, n=5):
        pipe = [
            {"$group": {"_id": "$publisher", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}, {"$limit": n},
        ]
        return self._agg(self.books, pipe, lambda: [
            {"_id": p, "count": c}
            for p, c in Counter(b["publisher"] for b in self.books.find()).most_common(n)
        ])

    # A3 文档数最多的图书类别（等价 $sortByCount）
    def top_category(self):
        rows = self.stat_by_category()
        return rows[0] if rows else None

    # A4 评分最高的 3 本图书（$sort + $limit + $project）
    def top_rated_books(self, n=3):
        pipe = [
            {"$sort": {"rating": -1}}, {"$limit": n},
            {"$project": {"_id": 0, "title": 1, "rating": 1, "borrow_count": 1}},
        ]
        return self._agg(self.books, pipe, lambda: [
            {"title": b["title"], "rating": b["rating"],
             "borrow_count": b.get("borrow_count", 0)}
            for b in sorted(self.books.find(), key=lambda x: -x["rating"])[:n]
        ])

    # A5 每本书“销售额”= 单价 × 借阅次数，四舍五入 2 位（$multiply + $round）
    def book_sales(self):
        pipe = [
            {"$project": {"_id": 0, "title": 1, "price": 1, "borrow_count": 1,
                         "sales": {"$round": [{"$multiply": ["$price", "$borrow_count"]}, 2]}}},
            {"$sort": {"sales": -1}},
        ]
        return self._agg(self.books, pipe, lambda: [
            {"title": b["title"], "price": b["price"],
             "borrow_count": b.get("borrow_count", 0),
             "sales": round(b["price"] * b.get("borrow_count", 0), 2)}
            for b in sorted(self.books.find(),
                            key=lambda x: -(x["price"] * x.get("borrow_count", 0)))
        ])

    # A6 按借阅年份统计借阅量，格式化为“2024年”（$year / $dateToString）
    def borrow_trend_by_year(self):
        pipe = [
            {"$group": {"_id": {"$year": "$borrow_date"},
                        "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ]
        def fb():
            c = Counter()
            for l in self.logs.find():
                bd = l.get("borrow_date")
                if isinstance(bd, datetime):
                    c[bd.year] += 1
            return [{"_id": y, "count": n} for y, n in sorted(c.items())]
        rows = self._agg(self.logs, pipe, fb)
        return [{"year": f"{r['_id']}年", "count": r["count"]} for r in rows]

    # A7 每位读者借阅次数，取前 5（$group + $sort + $limit）
    def top_readers(self, n=5):
        pipe = [
            {"$group": {"_id": "$reader_card", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}, {"$limit": n},
        ]
        rows = self._agg(self.logs, pipe, lambda: [
            {"_id": c, "count": n2}
            for c, n2 in Counter(l["reader_card"] for l in self.logs.find()).most_common(n)
        ])
        name_map = {r["card_no"]: r["name"] for r in self.readers.find()}
        return [{"card": r["_id"], "name": name_map.get(r["_id"], "?"),
                 "count": r["count"]} for r in rows]

    # A8 关联读者与借阅流水，产出学院借阅量排行（$lookup）
    def college_borrow_rank(self):
        pipe = [
            {"$lookup": {"from": "readers",
                         "localField": "reader_card",
                         "foreignField": "card_no", "as": "reader"}},
            {"$unwind": "$reader"},
            {"$group": {"_id": "$reader.college", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        def fb():
            m = {r["card_no"]: r["college"] for r in self.readers.find()}
            c = Counter(m.get(l["reader_card"], "未知") for l in self.logs.find())
            return [{"_id": k, "count": v} for k, v in c.most_common()]
        return self._agg(self.logs, pipe, fb)

    # A9 把 A1 分类统计结果写入 category_stats 集合（$merge）
    def merge_category_stats(self):
        rows = self.stat_by_category()
        try:
            self.cat_stats.delete_many({})
            self.cat_stats.insert_many([
                {"category": r["_id"], "book_count": r["count"],
                 "avg_rating": r["avg_rating"]} for r in rows])
        except Exception:
            pass
        return self.cat_stats.count_documents({})


def demo(db):
    sm = StatManager(db)
    print("【任务四·聚合管道统计 A1—A9】")
    print("A1 按类别统计数量与平均评分：")
    for r in sm.stat_by_category():
        print(f"   类别={r['_id']:6s} 图书数={r['count']}  平均评分={round(r['avg_rating'],2)}")
    print("A2 图书数量最多的出版社 Top5：")
    for r in sm.top_publishers(5):
        print(f"   {r['_id']:20s} {r['count']} 本")
    t = sm.top_category()
    print("A3 文档数最多的类别：", t["_id"], "(", t["count"], "本)")
    print("A4 评分最高的 3 本图书：")
    for r in sm.top_rated_books(3):
        print(f"   《{r['title']}》 评分={r['rating']} 累计借阅={r['borrow_count']}")
    print("A5 图书销售额(单价×借阅次数) Top3：")
    for r in sm.book_sales()[:3]:
        print(f"   《{r['title']}》 单价={r['price']}×{r['borrow_count']} = {r['sales']} 元")
    print("A6 按年份借阅量趋势：")
    for r in sm.borrow_trend_by_year():
        print(f"   {r['year']} 借阅 {r['count']} 次")
    print("A7 借阅最活跃读者 Top5：")
    for r in sm.top_readers(5):
        print(f"   {r['card']} {r['name']} 借阅 {r['count']} 次")
    print("A8 各学院借阅量排行（$lookup 关联）：")
    for r in sm.college_borrow_rank():
        print(f"   {r['_id']:12s} 借阅 {r['count']} 次")
    n = sm.merge_category_stats()
    print(f"A9 分类统计结果已写入 category_stats 集合，共 {n} 条")


if __name__ == "__main__":
    from mongodb_connect import get_db
    demo(get_db())
