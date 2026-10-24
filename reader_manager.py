# -*- coding: utf-8 -*-
"""
reader_manager.py —— 读者信息管理模块（任务三 Q4/D3 + 任务五）
涉及方法：find、find_one、count_documents、distinct、update_one、replace_one。
"""
from collections import Counter


class ReaderManager:
    def __init__(self, db):
        self.col = db.readers

    def no_email(self):
        """Q4 查找 email 为空（未登记邮箱）的读者 ($eq:null)"""
        return list(self.col.find({"email": None}))

    def find_by_card(self, card_no):
        return self.col.find_one({"card_no": card_no})

    def college_stats(self):
        """按学院统计读者人数（find + 客户端聚合）"""
        rows = list(self.col.find({}, {"_id": 0, "college": 1, "level": 1}))
        return dict(Counter(r["college"] for r in rows))

    def level_distribution(self):
        """借阅等级分布（普通/高级/教师）"""
        rows = list(self.col.find({}, {"_id": 0, "level": 1}))
        return dict(Counter(r["level"] for r in rows))

    def college_list(self):
        """所有学院清单（distinct）"""
        return self.col.distinct("college")

    def replace_reader(self, card_no, new_info):
        """D3 整体替换某位读者信息，保留 _id (replace_one)"""
        new_info["card_no"] = card_no
        return self.col.replace_one({"card_no": card_no}, new_info)


def _fmt(r):
    return (f"  证号={r.get('card_no')} 姓名={r.get('name')} "
            f"学院={r.get('college')} 等级={r.get('level')} email={r.get('email')}")


def demo(db):
    rm = ReaderManager(db)
    print("【任务三·读者检索 Q4 / D3】")
    no_mail = rm.no_email()
    print("Q4 未登记邮箱的读者：", len(no_mail), "人")
    for r in no_mail:
        print(_fmt(r))
    print("读者总数 count_documents =", rm.col.count_documents({}))
    print("distinct 学院清单 =", rm.college_list())
    print("各学院人数统计：", rm.college_stats())
    print("借阅等级分布：", rm.level_distribution())
    # D3 演示：把 R20240015 冯雪的信息整体替换（保留 _id）
    res = rm.replace_reader(
        "R20240015",
        {"name": "冯雪", "college": "文学院", "phone": "15500155000",
         "level": "高级", "email": "xujing@example.edu"})
    print(f"D3 replace_one 整体替换 R20240015 matched={res.matched_count} "
          f"modified={res.modified_count}")


if __name__ == "__main__":
    from mongodb_connect import get_db
    demo(get_db())
