#!/usr/bin/env python3
"""有界、只读地分析存档样本并另存证据报告；不自动解压或写回。"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import uuid

MIB = 1024 * 1024
MAX_TOTAL = 64 * MIB


def number(text):
    return int(text, 16 if text.lower().startswith('0x') else 10)


def entropy(data):
    if not data:
        return 0.0
    return -sum((n / len(data)) * math.log2(n / len(data)) for n in Counter(data).values())


def signatures(data):
    found = []
    for magic, label in [(b'\x1f\x8b', 'gzip 头部候选'), (b'PK\x03\x04', 'ZIP 本地头候选'),
                         (b'SQLite format 3\x00', 'SQLite 文件头候选')]:
        if data.startswith(magic):
            found.append(label)
    if len(data) >= 2 and data[0] & 15 == 8 and data[0] >> 4 <= 7 and int.from_bytes(data[:2], 'big') % 31 == 0:
        found.append('zlib 头部候选')
    if data.lstrip().startswith((b'{', b'[')):
        found.append('JSON 文本起始候选')
    return found


def read_sample(path, limit):
    path = Path(path).resolve(strict=True)
    with path.open('rb') as handle:
        stat_before = path.stat()
        data = handle.read(limit + 1)
        stat_after = path.stat()
    if len(data) > limit:
        raise ValueError(f'样本超过每文件读取上限：{path}')
    if stat_before.st_size != len(data) or stat_after.st_size != len(data) or stat_before.st_mtime_ns != stat_after.st_mtime_ns:
        raise ValueError(f'读取期间样本变化：{path}')
    return data, {'path': str(path), 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                  'entropy_bits_per_byte': round(entropy(data), 6), 'header_hex': data[:64].hex(' '),
                  'signature_candidates': signatures(data)}


def probe_value(data, offset, size):
    if offset < 0 or size not in (1, 2, 4, 8):
        raise ValueError('probe 需要非负偏移和 1/2/4/8 字节长度')
    if offset + size > len(data):
        return {'offset': hex(offset), 'size': size, 'status': '超出样本，未读取'}
    raw = data[offset:offset + size]
    result = {'offset': hex(offset), 'size': size, 'hex': raw.hex(' '), 'status': '仅机械解释，类型和语义待验证'}
    for endian in ('little', 'big'):
        result[endian] = {'unsigned': int.from_bytes(raw, endian), 'signed': int.from_bytes(raw, endian, signed=True)}
        if size in (4, 8):
            value = struct.unpack(('<' if endian == 'little' else '>') + ('f' if size == 4 else 'd'), raw)[0]
            result[endian]['float'] = value if math.isfinite(value) else str(value)
    return result


def fixed_offset_diff(a, b):
    length, index, changed, blocks, shown = min(len(a), len(b)), 0, 0, 0, []
    while index < length:
        if a[index] == b[index]:
            index += 1
            continue
        start = index
        while index < length and a[index] != b[index]:
            index += 1
        changed += index - start
        blocks += 1
        if len(shown) < 128:
            end = min(index, start + 64)
            shown.append({'start': start, 'end': index, 'before_hex': a[start:end].hex(' '),
                          'after_hex': b[start:end].hex(' '), 'preview_truncated': end < index})
    return {'alignment': '固定文件偏移；未做插入/删除或结构对齐', 'common_length': length,
            'changed_bytes_in_common': changed, 'total_blocks': blocks, 'blocks': shown,
            'blocks_truncated': blocks > len(shown),
            'before_tail': {'start': length, 'length': len(a) - length},
            'after_tail': {'start': length, 'length': len(b) - length}}


def analyze(paths, limit, probes):
    if not 1 <= len(paths) <= 16 or not 0 < limit <= MAX_TOTAL:
        raise ValueError('要求 1–16 个样本，每文件上限不超过 64 MiB')
    files, buffers, total, resolved = [], [], 0, set()
    for path in paths:
        location = Path(path).resolve(strict=True)
        if location in resolved:
            raise ValueError('同一路径重复输入，不能充当独立样本')
        resolved.add(location)
        # 先用大小预算限制读取，避免多文件读取后才发现总量超限。
        remaining = MAX_TOTAL - total
        if location.stat().st_size > min(limit, remaining):
            raise ValueError('样本超过每文件或 64 MiB 累计预算')
        data, info = read_sample(location, min(limit, remaining))
        total += len(data)
        info['source_id'] = f'S{len(files) + 1:02d}'
        info['probes'] = [probe_value(data, offset, size) for offset, size in probes]
        files.append(info)
        buffers.append(data)
    comparisons = []
    for index in range(1, len(buffers)):
        comparisons.append({'before': files[0]['source_id'], 'after': files[index]['source_id'],
                            **fixed_offset_diff(buffers[0], buffers[index])})
    return {'format': 'xp-save-analysis-v1', 'sources': files, 'comparisons': comparisons,
            'warnings': ['只读观察；高熵不是加密证明，签名不是完整格式验证。',
                         '数值 probe 只是大小端/类型解释，字段边界、含义和算法均待验证。',
                         '长度变化可能造成固定偏移错位；差异不证明字段对应关系。',
                         '未自动解压、解密、计算校验覆盖范围或验证游戏可加载性。']}


def write_report(report, out_dir):
    root = Path(out_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    folder = root / ('xp-save-analysis-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:12])
    folder.mkdir(exist_ok=False)
    with (folder / 'report.json').open('x', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, allow_nan=False)
    lines = ['# XP · 存档格式观察', '', '状态：机器观察已记录，字段语义和格式假设尚待验证。', '', '## 来源', '']
    for source in report['sources']:
        lines += [f"- {source['source_id']}: `{source['path']}`；{source['size']} 字节；SHA-256 `{source['sha256']}`",
                  f"  - 头部线索：{', '.join(source['signature_candidates']) or '没有已识别的签名'}；熵 {source['entropy_bits_per_byte']}"]
    lines += ['', '## 固定偏移差异', '', '| 前后样本 | 公共长度 | 公共区域变化字节 | 原/新尾部长度 |', '|---|---|---|---|']
    for item in report['comparisons']:
        lines.append(f"| {item['before']} → {item['after']} | {item['common_length']} | {item['changed_bytes_in_common']} | {item['before_tail']['length']} / {item['after_tail']['length']} |")
    lines += ['', '具体半开偏移范围、原始片段、probe 数值与截断标记见同目录 report.json。', '', '## 不确定项与下一步', '']
    lines += ['- ' + warning for warning in report['warnings']]
    lines += ['- 提供版本/操作标签并重复单变量样本实验，随后核对读写函数或完整解析结果。']
    with (folder / 'report.md').open('x', encoding='utf-8') as handle:
        handle.write('\n'.join(lines) + '\n')
    return folder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs', nargs='+', type=Path)
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--max-bytes', type=number, default=16 * MIB, help='单文件上限，默认 16 MiB，硬上限 64 MiB')
    parser.add_argument('--probe', action='append', default=[], help='偏移:长度，例如 0x10:4，可重复')
    args = parser.parse_args()
    try:
        probes = []
        for spec in args.probe:
            offset, size = spec.split(':')
            offset, size = number(offset), number(size)
            if offset < 0 or size not in (1, 2, 4, 8):
                raise ValueError('probe 需要非负偏移和 1/2/4/8 字节长度')
            probes.append((offset, size))
        print(write_report(analyze(args.inputs, args.max_bytes, probes), args.out_dir))
    except (OSError, ValueError, TypeError) as error:
        print(f'失败：{error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
