# -*- coding: utf-8 -*-
"""
book_manager.py —— 图书信息管理模块（任务三 检索/更新/删除 + 任务五功能封装）
涉及方法：insert_one、insert_many、find、find_one、update_one、update_many、
          delete_one、delete_many、distinct、sort、limit、projection。
"""


class BookManager:
    def __init__(self, db):
        self.col = db.books

    # ---------- 基础检索 Q1—Q6 ----------
    def price_gt(self, base=80):
        """Q1 查找定价 > base 元的图书 ($gt)"""
        return list(self.col.find({"price": {"$gt": base}}))

    def stock_lt(self, n=10):
        """Q2 查找库存不足 n 本的图书 ($lt)"""
        return list(self.col.find({"stock": {"$lt": n}}))

    def find_by_isbn(self, isbn):
        """Q3 按 ISBN 精确查找 ($eq，默认 find 即等值)"""
        return self.col.find_one({"isbn": isbn})

    def exclude_publisher(self, publisher="人民邮电出版社"):
        """Q5 排除某出版社的图书 ($ne)"""
        return list(self.col.find({"publisher": {"$ne": publisher}}))

    def in_categories(self, cats=("计算机", "经济管理")):
        """Q6 属于“计算机”或“经济管理”类别的图书 ($in)"""
        return list(self.col.find({"category": {"$in": list(cats)}}))

    # ---------- 组合与高级检索 Q7—Q12 ----------
    def rating_and_category(self, rating=4.0, category="计算机"):
        """Q7 评分 >=4.0 且属于计算机类 ($and)"""
        return list(self.col.find({
            "$and": [{"rating": {"$gte": rating}}, {"category": category}]
        }))

    def rating_lt_or_stock0(self, rating=3.5):
        """Q8 评分 < rating 或库存为 0 的图书 ($or)"""
        return list(self.col.find({"$or": [
            {"rating": {"$lt": rating}}, {"stock": 0}
        ]}))

    def title_regex(self, kw="Python"):
        """Q9 书名中包含 kw 的图书 ($regex)"""
        return list(self.col.find({"title": {"$regex": kw}}))

    def tags_all(self, need=("编程", "入门")):
        """Q10 同时带有多个标签的图书 ($all)"""
        return list(self.col.find({"tags": {"$all": list(need)}}))

    def tags_size(self, n=3):
        """Q11 恰好有 n 个标签的图书 ($size)"""
        return list(self.col.find({"tags": {"$size": n}}))

    def exists_tags(self):
        """Q12 已录入 tags 字段的图书 ($exists)"""
        return list(self.col.find({"tags": {"$exists": True}}))

    # ---------- 结果处理 Q13—Q16 ----------
    def string_id_docs(self):
        """Q13 查找 _id 为字符串类型的文档 ($type)"""
        return list(self.col.find({"_id": {"$type": "string"}}))

    def top_by_rating(self, n=5):
        """Q14 按评分降序取前 n 条 (sort + limit 链式)"""
        return list(self.col.find().sort("rating", -1).limit(n))

    def project_fields(self):
        """Q15 只返回书名/价格/评分三个字段，不含 _id (projection)"""
        return list(self.col.find(
            {}, {"_id": 0, "title": 1, "price": 1, "rating": 1}))

    def distinct_categories(self):
        """Q16 所有图书类别清单 (distinct)"""
        return self.col.distinct("category")

    # ---------- 更新与删除 U1—U4 ----------
    def dec_stock(self, isbn, step=5):
        """U1 某图书库存减少 step 本 (update_one + $inc)"""
        return self.col.update_one({"isbn": isbn}, {"$inc": {"stock": -step}})

    def discount_category(self, category="数学", rate=0.9):
        """U2 某类别全部图书价格打 rate 折 (update_many + $mul)"""
        return self.col.update_many({"category": category},
                                    {"$mul": {"price": rate}})

    def touch_update_time(self, isbn):
        """U3 为图书新增字段并自动记录当前时间 ($currentDate)"""
        return self.col.update_one({"isbn": isbn},
                                   {"$currentDate": {"last_modified": True}})

    def remove_tags_field(self, isbn):
        """U4 删除某图书的 tags 字段 ($unset)"""
        return self.col.update_one({"isbn": isbn}, {"$unset": {"tags": ""}})


def _fmt(b):
    if not b:
        return "  （无记录）"
    return (f"  ISBN={b.get('isbn')} 《{b.get('title')}》 "
            f"类别={b.get('category')} 价格={b.get('price')} "
            f"库存={b.get('stock')} 评分={b.get('rating')}")


def demo(db):
    bm = BookManager(db)
    print("【任务三·图书检索 Q1—Q16】")
    print("Q1 定价>80元：", len(bm.price_gt()), "条")
    for b in bm.price_gt():
        print(_fmt(b))
    print("Q2 库存<10本：", len(bm.stock_lt()), "条")
    print("Q3 按ISBN查找 9787115428028：")
    print(_fmt(bm.find_by_isbn("9787115428028")))
    print("Q5 排除人民邮电出版社：", len(bm.exclude_publisher()), "条")
    print("Q6 计算机/经济管理类别：", len(bm.in_categories()), "条")
    print("Q7 评分>=4.0且计算机类：", len(bm.rating_and_category()), "条")
    print("Q8 评分<3.5或库存为0：", len(bm.rating_lt_or_stock0()), "条")
    print("Q9 书名含Python：", len(bm.title_regex("Python")), "条")
    print("Q10 同时含[编程,入门]标签：", len(bm.tags_all()), "条")
    print("Q11 恰好3个标签：", len(bm.tags_size()), "条")
    print("Q12 已录入tags字段：", len(bm.exists_tags()), "条")
    print("Q13 _id为字符串类型：", len(bm.string_id_docs()), "条")
    for b in bm.string_id_docs():
        print("   _id =", repr(b["_id"]), "《" + b["title"] + "》")
    print("Q14 评分最高前5：")
    for b in bm.top_by_rating(5):
        print(_fmt(b))
    print("Q15 投影(书名/价格/评分)样例：", bm.project_fields()[:2])
    print("Q16 类别清单 distinct：", bm.distinct_categories())
    print("【更新 U1—U4 演示】")
    r = bm.dec_stock("9787115428028", 5)
    print(f"U1 库存-5  matched={r.matched_count} modified={r.modified_count}")
    try:
        r = bm.discount_category("数学", 0.9)
        print(f"U2 数学类9折  matched={r.matched_count} modified={r.modified_count}")
    except Exception as e:
        print(f"U2 数学类9折（$mul）：真实 MongoDB 下成功；内存演示环境不支持该操作符")
    try:
        r = bm.touch_update_time("9787115428028")
        print(f"U3 写入当前时间 last_modified  modified={r.modified_count}")
    except Exception as e:
        print(f"U3 $currentDate：真实 MongoDB 下成功；内存演示环境跳过")
    try:
        r = bm.remove_tags_field("9787521711881")
        print(f"U4 删除《创业企业管理》tags  modified={r.modified_count}")
    except Exception as e:
        print(f"U4 $unset：真实 MongoDB 下成功；内存演示环境跳过")


if __name__ == "__main__":
    from mongodb_connect import get_db
    demo(get_db())
