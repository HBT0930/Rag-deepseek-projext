from typing import Callable, Dict, Any, Optional, List
import subprocess
import os
import json
import glob as py_glob
import re


class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.blocked_commands = [
            "rm -rf",
            "git push --force",
            "DROP TABLE",
            "DROP DATABASE",
            "chmod 777",
            "format",
            "del /f /s /q",
        ]

    def register(self, name: str, func: Callable):
        self.tools[name] = func

    def execute(self, name: str, **kwargs) -> Any:
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found. Available: {list(self.tools.keys())}")
        return self.tools[name](**kwargs)

    def is_blocked(self, command: str) -> bool:
        return any(blocked in command.lower() for blocked in self.blocked_commands)
    
    def get_blocked_checker(self):
        blocked = self.blocked_commands
        return lambda cmd: any(b in cmd.lower() for b in blocked)


def create_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    
    is_blocked = registry.get_blocked_checker()

    registry.register("run_bash", lambda cmd: _run_bash(cmd, is_blocked))
    registry.register("read_file", lambda path: _read_file(path))
    registry.register("write_file", lambda path, content: _write_file(path, content))
    registry.register("list_dir", lambda path=".": _list_dir(path))
    registry.register("search_files", lambda pattern: _search_files(pattern))
    registry.register("find_text", lambda pattern, path=".", include="*.py": _find_text(pattern, path, include))
    registry.register("get_file_info", lambda path: _get_file_info(path))
    registry.register("count_lines", lambda path: _count_lines(path))
    registry.register("execute_python", lambda code: _execute_python(code))

    return registry


def _run_bash(cmd: str, is_blocked) -> dict:
    if is_blocked(cmd):
        return {"success": False, "error_type": "blocked", "output": "命令被阻止"}

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=120
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
            "error_type": "execution_error" if result.returncode != 0 else None,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error_type": "timeout", "output": "命令超时"}
    except Exception as e:
        return {"success": False, "error_type": "exception", "output": str(e)}


def _read_file(path: str) -> dict:
    import os
    
    # 检查是否为图片/二进制文件
    binary_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.ico', '.exe', '.dll', '.so', '.dylib')
    ext = os.path.splitext(path)[1].lower()
    if ext in binary_extensions:
        return {
            "success": False,
            "error_type": "unsupported_file_type",
            "output": f"不支持读取二进制文件: {path}。请使用文本文件。"
        }
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"success": True, "content": content}
    except Exception as e:
        return {"success": False, "error_type": "file_error", "output": str(e)}


def _write_file(path: str, content: str) -> dict:
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "output": f"文件已写入: {path}"}
    except Exception as e:
        return {"success": False, "error_type": "file_error", "output": str(e)}


def _list_dir(path: str = ".") -> dict:
    try:
        entries = os.listdir(path)
        return {"success": True, "entries": entries}
    except Exception as e:
        return {"success": False, "error_type": "file_error", "output": str(e)}


def _search_files(pattern: str) -> dict:
    try:
        files = list(py_glob.glob(pattern, recursive=True))
        return {"success": True, "files": files, "count": len(files)}
    except Exception as e:
        return {"success": False, "error_type": "glob_error", "output": str(e)}


def _find_text(pattern: str, path: str = ".", include: str = "*.py") -> dict:
    try:
        results = []
        for file_path in py_glob.glob(os.path.join(path, "**", include), recursive=True):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if re.search(pattern, content, re.IGNORECASE):
                        results.append({
                            "file": file_path,
                            "matches": len(re.findall(pattern, content, re.IGNORECASE))
                        })
            except Exception:
                continue
        
        return {"success": True, "results": results, "count": len(results)}
    except Exception as e:
        return {"success": False, "error_type": "search_error", "output": str(e)}


def _get_file_info(path: str) -> dict:
    try:
        if not os.path.exists(path):
            return {"success": False, "error_type": "not_found", "output": f"文件不存在: {path}"}
        
        stat = os.stat(path)
        return {
            "success": True,
            "path": path,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "is_dir": os.path.isdir(path),
            "is_file": os.path.isfile(path),
        }
    except Exception as e:
        return {"success": False, "error_type": "file_error", "output": str(e)}


def _count_lines(path: str) -> dict:
    try:
        if not os.path.exists(path):
            return {"success": False, "error_type": "not_found", "output": f"文件不存在: {path}"}
        
        if os.path.isdir(path):
            return {"success": False, "error_type": "is_directory", "output": f"路径是目录: {path}"}
        
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        return {"success": True, "lines": len(lines), "path": path}
    except Exception as e:
        return {"success": False, "error_type": "file_error", "output": str(e)}


def _execute_python(code: str) -> dict:
    try:
        import io
        import sys
        
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        
        try:
            exec(code, {})
            output = buffer.getvalue()
            return {"success": True, "output": output}
        except Exception as e:
            return {"success": False, "error_type": "execution_error", "output": str(e)}
        finally:
            sys.stdout = old_stdout
    except Exception as e:
        return {"success": False, "error_type": "system_error", "output": str(e)}
