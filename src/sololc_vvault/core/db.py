import sqlite3
from sqlite3 import Error


# 推荐在连接时开启 WAL 模式（预写日志），这能让 SQLite 的读写并发性能大幅提升
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        # 性能优化：开启 WAL 模式，减少主密码认证和高频读写时的锁表概率
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn
    except Error as e:
        print(f"Database connection error: {e}")
    return conn


# from pathlib import Path

# # 获取用户家目录，把数据库安全地存在隐藏文件夹下
# DB_DIR = Path.home() / ".config" / "sololc-vvault"
# DB_DIR.mkdir(parents=True, exist_ok=True)
# DB_PATH = DB_DIR / "vault.db"

# def query_alias(alias_name: str):
#     # 使用 with 自动管理连接和关闭
#     with sqlite3.connect(DB_PATH) as conn:
#         cursor = conn.cursor()

#         # 还记得我们建的唯一索引吗？这里会走 idx_totp_alias 索引，速度极快
#         cursor.execute(
#             "SELECT service, account, secret FROM totp_vault WHERE alias = ?;",
#             (alias_name,)
#         )
#         return cursor.fetchone()
