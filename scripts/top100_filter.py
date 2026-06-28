#!/usr/bin/env python3
"""
从 subs-check 生成的 output/all.yaml (Clash 格式) 与 output/base64.txt (V2Ray/base64 格式)
中，按节点名称里编码的测速结果（例如 "12.3MB/s"）排序，截取最优的 N 个节点，
分别输出精简后的 Clash 订阅与 V2Ray 订阅 —— 两份输出对应的是同一批节点。
"""

import argparse
import base64
import json
import re
import sys
from urllib.parse import unquote, urlparse

try:
    import yaml
except ImportError:
    print("缺少依赖，请先运行: pip install pyyaml --break-system-packages", file=sys.stderr)
    sys.exit(1)

SPEED_RE = re.compile(r'(\d+(?:\.\d+)?)\s*(KB|MB|GB)/s', re.IGNORECASE)
UNIT_TO_KB = {'KB': 1, 'MB': 1024, 'GB': 1024 * 1024}


def extract_speed_kb(name: str) -> float:
    if not name:
        return -1.0
    m = SPEED_RE.search(name)
    if not m:
        return -1.0
    value, unit = m.groups()
    return float(value) * UNIT_TO_KB[unit.upper()]


def load_clash_proxies(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    if not data or 'proxies' not in data:
        return []
    return data['proxies']


def vmess_remark(uri: str) -> str:
    raw = uri[len('vmess://'):].strip()
    raw += '=' * (-len(raw) % 4)
    try:
        obj = json.loads(base64.b64decode(raw).decode('utf-8', errors='ignore'))
        return obj.get('ps', '') or obj.get('remark', '')
    except Exception:
        return ''


def generic_remark(uri: str) -> str:
    try:
        frag = urlparse(uri).fragment
        return unquote(frag) if frag else ''
    except Exception:
        return ''


def uri_remark(uri: str) -> str:
    uri = uri.strip()
    if not uri:
        return ''
    if uri.startswith('vmess://'):
        return vmess_remark(uri)
    return generic_remark(uri)


def load_v2ray_uris(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    try:
        padded = content + '=' * (-len(content) % 4)
        decoded = base64.b64decode(padded).decode('utf-8', errors='ignore')
        if '://' in decoded:
            content = decoded
    except Exception:
        pass
    return [line for line in content.splitlines() if line.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--clash-in', required=True)
    ap.add_argument('--v2ray-in', required=True)
    ap.add_argument('--clash-out', required=True)
    ap.add_argument('--v2ray-out', required=True)
    ap.add_argument('--limit', type=int, default=100)
    args = ap.parse_args()

    proxies = load_clash_proxies(args.clash_in)
    if not proxies:
        print(f"警告：从 {args.clash_in} 没有读到任何 proxies", file=sys.stderr)

    ranked = sorted(proxies, key=lambda p: extract_speed_kb(p.get('name', '')), reverse=True)
    top = ranked[: args.limit]
    top_names = {p.get('name') for p in top}

    with open(args.clash_out, 'w', encoding='utf-8') as f:
        yaml.dump({'proxies': top}, f, allow_unicode=True, sort_keys=False)

    uris = load_v2ray_uris(args.v2ray_in)
    matched = [u for u in uris if uri_remark(u) in top_names]

    if len(top) > 0 and len(matched) < len(top) * 0.5:
        print("提示：按名称匹配数偏少，已降级为按数量直接截取", file=sys.stderr)
        matched = uris[: args.limit]

    out_content = '\n'.join(matched)
    out_b64 = base64.b64encode(out_content.encode('utf-8')).decode('utf-8')
    with open(args.v2ray_out, 'w', encoding='utf-8') as f:
        f.write(out_b64)

    print(f"完成：Clash 节点数 = {len(top)}, V2Ray 节点数 = {len(matched)}")


if __name__ == '__main__':
    main()
