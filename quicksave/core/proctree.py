import psutil

def get_process_tree(pid: int):
    """递归获取 pid 的所有子进程 PID（含自身）"""
    try:
        proc = psutil.Process(pid)
        children = proc.children(recursive=True)
        return [pid] + [c.pid for c in children]
    except Exception:
        return [pid]