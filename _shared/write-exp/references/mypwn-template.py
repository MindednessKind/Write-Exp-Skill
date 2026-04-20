# pyright: reportWildcardImportFromLibrary=false
# ruff: noqa: F403, F405
from Mypwn import *
from pwn import process
# from libcfind import *  # Uncomment only when you really resolve unknown libc from a leak


FILE_NAME = "./pwn"
LIBC_PATH = None
# REMOTE_TARGET = ("127.0.0.1", 9999)
REMOTE_TARGET = None

PACK_ARCH = None  # Set to "amd64" or "i386" when FILE_NAME is None.

IS_SSL = False
SNI_HOST = None
LOCAL_ARGV = None

src = """

"""

io = None
s = sl = sa = sla = rcv = rcu = shell = None

init(
    binary_path=FILE_NAME,
    libc_path=LIBC_PATH,
)


class _PackerArch:
    def __init__(self, arch):
        self.arch = arch


def resolve_packers():
    if elf is not None:
        return Tool.get_arch_packer(elf)
    if PACK_ARCH in ("amd64", "i386"):
        return Tool.get_arch_packer(_PackerArch(PACK_ARCH))
    raise ValueError("Set FILE_NAME or PACK_ARCH before using Tool.get_arch_packer().")


logHex, lg, info, debug = get_log_function()
unpk, dopk, word_size = resolve_packers()
itb, bti = Tool.get_byte_packer()


def dbg():
    if src.strip():
        GDB(io, scripts=src)
    else:
        GDB(io)
    pause()


def bind():
    global s, sl, sa, sla, rcv, rcu, shell
    s = lambda data: io.send(data)
    sl = lambda data: io.sendline(data)
    sa = lambda delim, data: io.sendafter(delim, data)
    sla = lambda delim, data: io.sendlineafter(delim, data)
    rcv = lambda num=4096: io.recv(num)
    rcu = lambda delim, drop=False: io.recvuntil(delim, drop)
    shell = lambda: io.interactive()

# ================= 壳准备 / 上传 =================
# def prep(expect=b"$ ", timeout=60, disable_echo=False):
#     prepare_shell(io, expect=expect, timeout=timeout, disable_echo=disable_echo)
#
# TERM_REPLY = make_terminal_reply()
#
# def upload_exp(local_path="./exp", remote_path="/tmp/exp", argv=""):
#     return upload_and_run(io, local_path, remote_path=remote_path, argv=argv, timeout=30.0)
#
# def run_exp_wait(remote_path="/tmp/exp", argv=""):
#     return execute_and_wait(io, remote_path, argv=argv, timeout=60, terminal_reply=TERM_REPLY)
#
# def run_exp_manual(remote_path="/tmp/exp"):
#     execute(io, remote_path)
#     data = io.recvrepeat(2)
#     return data


# ================= 协议函数 =================
# def cmd(ch):
#     sl(itb(ch))
#
# def add(idx, size, data=b"A"):
#     cmd(1)
#     sl(itb(idx))
#     sl(itb(size))
#     sa(b"data: ", data)
#
# def edit(idx, data):
#     cmd(2)
#     sl(itb(idx))
#     sa(b"data: ", data)
#
# def show(idx):
#     cmd(3)
#     sl(itb(idx))
#     return rcu(b"1. ", drop=True)
#
# def dele(idx):
#     cmd(4)
#     sl(itb(idx))


def exploit():
    global io

    if REMOTE_TARGET is None:
        if LOCAL_ARGV is None:
            io = iopen(binary=FILE_NAME, libc_path=LIBC_PATH)
        else:
            io = process(LOCAL_ARGV)
            bind()
    else:
        if SNI_HOST is None:
            io = iopen(
                target=REMOTE_TARGET,
                binary=FILE_NAME,
                libc_path=LIBC_PATH,
                ssl=IS_SSL,
            )
        else:
            io = iopen(
                target=REMOTE_TARGET,
                binary=FILE_NAME,
                libc_path=LIBC_PATH,
                ssl=IS_SSL,
                sni=SNI_HOST,
            )

    # leak = show(0)
    # libc.address = unpk(leak[:6]) - 0x123456
    # heap_base = unpk(leak[8:14]) - 0x260
    # logHex("libc", libc.address)
    # logHex("heap", heap_base)
    # puts_addr = unpk(leak[:6])
    # db = LibcSearcher("puts", puts_addr)
    # libc_base = puts_addr - db.symbols["puts"]
    # system_addr = libc_base + db.dump("system")
    # binsh_addr = libc_base + db.dump("str_bin_sh")

    shell()


if __name__ == "__main__":
    exploit()
