#!/usr/bin/env python3
"""
从环境变量 SUB_URLS（来自 GitHub Actions Secret）读取订阅链接列表，
注入到 config/config.template.yaml 里，生成 config/config.yaml。
"""

import os
import sys

try:
    import yaml
except ImportError:
    print("缺少依赖，请先运行: pip install pyyaml --break-system-packages", file=sys.stderr)
    sys.exit(1)

TEMPLATE_PATH = "config/config.template.yaml"
OUTPUT_PATH = "config/config.yaml"


def main():
    raw = os.environ.get("SUB_URLS", "")
    urls = [line.strip() for line in raw.splitlines() if line.strip()]

    if not urls:
        print(
            "错误：没有从 SUB_URLS 这个 secret 读到任何链接。\n"
            "请确认仓库 Settings -> Secrets and variables -> Actions 里已经配置了 SUB_URLS。",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    config["sub-urls"] = urls

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    print(f"已生成 {OUTPUT_PATH}，注入了 {len(urls)} 条订阅链接（内容不打印）")


if __name__ == "__main__":
    main()
