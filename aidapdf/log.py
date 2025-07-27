import sys


def _log(prefix: str, msg: str):
    n = 8
    print(prefix.ljust(n) + ' ' + msg.replace("\n", "\n" + ' '*(n+1)), file=sys.stderr)

def log(msg: str):
    _log("", msg)

def log_action(msg: str):
    _log("!!>", msg)

def log_cmd(cmd: str, args: dict):
    a = []
    for k, v in args.items():
        a.append(str(k) + '=' + repr(v))
    _log("$$>", cmd + ' ' + ', '.join(a))

def log_hint(msg: str):
    _log("[hint]", msg)

def log_err(msg: str):
    _log("[!!]", msg)
