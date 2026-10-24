# -*- coding: utf-8 -*-
"""
main.py —— 图书情报检索与统计平台 菜单式交互主程序（任务五 ST-5）
启动时打印连接状态与各集合文档总数；菜单覆盖检索/统计/更新/删除；
退出前关闭数据库连接。加 --demo 参数可一次性演示全部功能（用于截图）。
"""
import sys
from mongodb_connect import get_db, collection_counts, ENV
import book_manager, reader_manager, borrow_manager, stat_manager


MENU = """
================ 图书情报检索与统计平台 ================
  1. 图书高级检索（价格/库存/类别/标签/正则）
  2. 评分排行与图书类别清单
  3. 读者信息与学院/等级统计
  4. 借阅登记 / 归还 / 逾期查询
  5. 分类统计报表（按类别/出版社）
  6. 借阅趋势与热门图书 / 活跃读者
  7. 图书更新（库存-5 / 分类打折）
  8. 数据删除（已归还记录清理）
  0. 退出
========================================================
"""


def banner(db):
    mode = "真实 MongoDB" if not ENV["using_mock"] else "内存演示 mongomock"
    print(f"[连接] 已连接 library 数据库（{mode}），服务器 localhost:27017")
    print("[集合文档总数]")
    for k, v in collection_counts(db).items():
        print(f"   {k:14s}: {v}")


def main():
    db = get_db()
    bm = book_manager.BookManager(db)
    rm = reader_manager.ReaderManager(db)
    bw = borrow_manager.BorrowManager(db)
    sm = stat_manager.StatManager(db)

    if "--demo" in sys.argv:
        banner(db)
        print(MENU)
        print(">> 自动演示各功能项：")
        print()
        book_manager.demo(db)
        print()
        reader_manager.demo(db)
        print()
        borrow_manager.demo(db)
        print()
        stat_manager.demo(db)
        print("\n[退出] 数据库连接已正常关闭。")
        return

    banner(db)
    while True:
        print(MENU)
        choice = input("请输入功能编号：").strip()
        if choice == "0":
            print("[退出] 数据库连接已正常关闭。")
            break
        elif choice == "1":
            book_manager.demo(db)
        elif choice == "2":
            for b in bm.top_by_rating(5):
                print(book_manager._fmt(b))
            print("类别清单：", bm.distinct_categories())
        elif choice == "3":
            reader_manager.demo(db)
        elif choice == "4":
            borrow_manager.demo(db)
        elif choice == "5":
            stat_manager.demo(db)
        elif choice == "6":
            stat_manager.demo(db)
        elif choice == "7":
            r = bm.dec_stock("9787115428028", 5)
            print(f"库存-5 受影响 matched={r.matched_count} modified={r.modified_count}")
            r = bm.discount_category("数学", 0.9)
            print(f"数学类9折 受影响 matched={r.matched_count} modified={r.modified_count}")
        elif choice == "8":
            _, msg = bw.delete_overdue_unreturned()
            print(msg)
        else:
            print("无结果或编号无效，请重新选择。")


if __name__ == "__main__":
    main()
