from __future__ import annotations

import time
from pathlib import Path

import httpx


BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api/v1"


def main() -> None:
    sample_file = Path(__file__).resolve().parents[1] / "examples" / "vulnerable_python_app" / "app.py"
    if not sample_file.exists():
        raise FileNotFoundError(f"未找到示例文件：{sample_file}")

    with httpx.Client(timeout=30.0) as client:
        with sample_file.open("rb") as handle:
            response = client.post(
                f"{API_BASE}/upload",
                files={"file": (sample_file.name, handle, "text/x-python")},
                data={"task_name": "demo-audit"},
            )
        response.raise_for_status()
        upload_data = response.json()
        task_id = upload_data["task_id"]
        print("上传成功：", upload_data)

        response = client.post(f"{API_BASE}/audit/start", json={"task_id": task_id})
        response.raise_for_status()
        print("任务已启动：", response.json())

        for _ in range(20):
            time.sleep(1)
            response = client.get(f"{API_BASE}/audit/{task_id}")
            response.raise_for_status()
            task = response.json()
            print("当前状态：", task["status"], "漏洞数：", len(task["findings"]))
            if task["status"] in {"completed", "failed"}:
                break

        report = client.get(f"{API_BASE}/report/{task_id}")
        report.raise_for_status()
        print("报告信息：", report.json())


if __name__ == "__main__":
    main()
