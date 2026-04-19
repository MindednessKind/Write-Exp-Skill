from Mypwn import *
from libcfind import *

# ================= 配置 =================
FILE_NAME = "./pwn"
LIBC_PATH = None  # 如果没有则设为 None
REMOTE_TARGET = "localhost:24753"
REMOTE_TARGET = None  # 本地调试时取消注释此行

# ================= 初始化 =================
# init 自动处理：
# 1. 有 Remote 则连远程，无 Remote 则启动本地进程
# 2. debug=True 时自动配置日志和 GDB 环境
io, elf, libc, GDB, shell = init(
    binary_path=FILE_NAME,
    target=REMOTE_TARGET,
    libc_path=LIBC_PATH,
    debug=True,
    IsBomb=False,
)

# 获取简写函数 (s, sl, sa, sla, rcv, rcu)
# 自动绑定了 io，直接用 sla(b">", b"1") 即可
# s, sl, sa, sla, rcv, rcu = get_dynamic_wrappers()
s, sl, sa, sla, rcv, rcu = get_static_wrappers(io)

# 获取架构相关打包函数 (unpk, dopk) 和字长
unpk, dopk, word_size = Tool.get_arch_packer(elf)
itb, bti = Tool.get_byte_packer()

# 获取 log 相关函数
logHex, log, info, debug = get_log_function()
hexlog = lambda data: logHex(data, eval(data))

# 获取 set log level 函数
set_info, set_debug = get_loglevel_function()


def dbg():
    GDB()
    pause()


# ================= 交互函数 =================
def cmd(chs):
    check_str = b"choice:"
    sla(check_str, itb(chs))


# def add(size, content=None):
#     if content is None:
#         content = b"A"
#     pass
def add(content, size=None):
    if size is None:
        size = len(content)
    # TODO: 填充题目的 add 逻辑
    raise NotImplementedError


def edit(idx, payload):
    # TODO: 填充题目的 edit 逻辑
    raise NotImplementedError


def dele(idx):
    # TODO: 填充题目的 dele 逻辑
    raise NotImplementedError


def show(idx):
    # TODO: 填充题目的 show 逻辑
    raise NotImplementedError


# ================= exploit =================
shell()
