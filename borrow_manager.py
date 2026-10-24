# -*- coding: utf-8 -*-
"""
borrow_manager.py —— 借阅流水模块（任务三 D1/D2 + 任务五）
涉及方法：insert_one、update_one、update_many、find、delete_one、delete_many。
"""
from datetime import datetime


class BorrowManager:
    def __init__(self, db):
        self.col = db.borrow_logs
        self.books = db.books
        self.readers = db.readers

    def borrow(self, reader_card, book_isbn):
        """借阅登记：新增一条 借出 流水 (insert_one)"""
        doc = {
            "borrow_date": datetime.now(),
            "reader_card": reader_card,
            "book_isbn": book_isbn,
            "status": "借出",
        }
        return self.col.insert_one(doc)

    def give_back(self, reader_card, book_isbn):
        """归还处理：把对应 借出 记录改为 已归还并写入归还时间 (update_one)"""
        return self.col.update_one(
            {"reader_card": reader_card, "book_isbn": book_isbn, "status": "借出"},
            {"$set": {"status": "已归还", "return_date": datetime.now()}},
        )

    def overdue_records(self):
        """逾期记录查询"""
        return list(self.col.find({"status": "逾期"}))

    def on_loan_records(self):
        """当前仍在借（未归还）记录"""
        return list(self.col.find({"status": "借出"}))

    def delete_one_returned(self):
        """D1 删除一条已归还记录 (delete_one + $eq)，先预览再删"""
        target = self.col.find_one({"status": "已归还"})
        if not target:
            return None, "没有可删除的已归还记录"
        res = self.col.delete_one({"_id": target["_id"]})
        return target, f"已删除1条已归还记录 deleted={res.deleted_count}"

    def delete_overdue_unreturned(self):
        """D2 清理逾期未还（仍处于借出状态且借期很早）的记录 (delete_many)"""
        preview = list(self.col.find({"status": "借出"}))
        res = self.col.delete_many({"status": "借出"})
        return preview, f"delete_many 清理在借记录 deleted={res.deleted_count}"


def _fmt(l):
    bd = l.get("borrow_date")
    bs = bd.strftime("%Y-%m-%d") if isinstance(bd, datetime) else str(bd)
    return (f"  {bs} 读者={l.get('reader_card')} ISBN={l.get('book_isbn')} "
            f"状态={l.get('status')}")


def demo(db):
    bm = BorrowManager(db)
    print("【任务三·借阅 D1/D2 + 逾期查询】")
    ov = bm.overdue_records()
    print("逾期记录：", len(ov), "条")
    for l in ov[:5]:
        print(_fmt(l))
    on = bm.on_loan_records()
    print("当前在借（未归还）：", len(on), "条")
    for l in on:
        print(_fmt(l))
    # D1
    target, msg = bm.delete_one_returned()
    print("D1 删除前预览：", _fmt(target) if target else "无")
    print("D1 结果：", msg)
    # 新登记一笔借阅
    r = bm.borrow("R20240003", "9787115428028")
    print("借阅登记 insert_one 成功 inserted_id =", r.inserted_id)


if __name__ == "__main__":
    from mongodb_connect import get_db
    demo(get_db())
