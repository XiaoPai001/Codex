#!/usr/bin/env python3
"""只读校验/比较 DHS MCP 导出的有界快照，不连接调试器。"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import uuid

MAX_JSON = 40 * 1024 * 1024
MAX_REGION = 1024 * 1024
MAX_TOTAL = 16 * MAX_REGION


def integer(value):
    if isinstance(value, bool):
        raise ValueError('布尔值不是地址或大小')
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 16 if value.lower().startswith('0x') else 10)
    raise ValueError('地址/数值必须是整数或明确的数字字符串')


def load_snapshot(path):
    path = Path(path).resolve(strict=True)
    with path.open('rb') as handle:
        raw = handle.read(MAX_JSON + 1)
    if len(raw) > MAX_JSON:
        raise ValueError('快照 JSON 超过 40 MiB 上限')
    obj = json.loads(raw.decode('utf-8-sig'))
    if not isinstance(obj, dict) or obj.get('format') != 'xp-debug-snapshot-v1':
        raise ValueError('不是 xp-debug-snapshot-v1')
    for key in ('session_id', 'target_id', 'captured_at'):
        if not isinstance(obj.get(key), str) or not obj[key].strip():
            raise ValueError(f'缺少身份/时间字段：{key}')
    captured = datetime.fromisoformat(obj['captured_at'].replace('Z', '+00:00'))
    if captured.tzinfo is None:
        raise ValueError('captured_at 必须为带时区的 ISO 8601 时间')
    if type(obj.get('pointer_size')) is not int or obj['pointer_size'] not in (4, 8):
        raise ValueError('pointer_size 必须为 4 或 8')
    if obj.get('consistency') != 'paused':
        raise ValueError('不是经核对的暂停快照，拒绝可靠对比')
    if not isinstance(obj.get('registers'), dict) or not isinstance(obj.get('regions'), list):
        raise ValueError('缺少 registers 或 regions')
    regions, total, spans = {}, 0, []
    for region in obj['regions']:
        if not isinstance(region, dict):
            raise ValueError('范围记录不是对象')
        key = region.get('id')
        if not isinstance(key, str) or not key.strip() or key in regions:
            raise ValueError('范围 ID 缺失或重复')
        base, size = integer(region.get('address')), integer(region.get('size'))
        if not (0 < size <= MAX_REGION) or base < 0 or base + size > 1 << (8 * obj['pointer_size']):
            raise ValueError('范围长度、地址或位宽无效')
        total += size
        if total > MAX_TOTAL:
            raise ValueError('累计范围超过 16 MiB')
        spans.append((base, base + size))
        if region.get('read_ok') is True:
            if not isinstance(region.get('hex'), str):
                raise ValueError('成功范围缺少 hex 字符串')
            data = bytes.fromhex(region['hex'])
            if len(data) != size:
                raise ValueError('短读/长度不符，禁止补零')
        elif region.get('read_ok') is False:
            if not region.get('error') or region.get('hex') not in (None, ''):
                raise ValueError('失败范围必须记录 error 且不能带伪造字节')
            data = None
        else:
            raise ValueError('read_ok 必须为布尔值')
        regions[key] = {'address': base, 'size': size, 'data': data, 'error': region.get('error')}
    spans.sort()
    if any(left[1] > right[0] for left, right in zip(spans, spans[1:])):
        raise ValueError('范围重叠，无法保证变化统计不重复')
    return obj, regions, {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()}


def byte_changes(before, after, max_blocks=128, preview=64):
    if len(before) != len(after):
        raise ValueError('字节比较要求相同长度')
    changed = blocks = index = 0
    shown = []
    while index < len(before):
        if before[index] == after[index]:
            index += 1
            continue
        start = index
        while index < len(before) and before[index] != after[index]:
            index += 1
        changed += index - start
        blocks += 1
        if len(shown) < max_blocks:
            end = min(index, start + preview)
            shown.append({'start': start, 'end': index, 'before_hex': before[start:end].hex(' '),
                          'after_hex': after[start:end].hex(' '), 'preview_truncated': end < index})
    return {'changed_bytes': changed, 'total_blocks': blocks, 'blocks': shown,
            'blocks_truncated': blocks > len(shown)}


def comparable_register(value):
    try:
        return integer(value)
    except (ValueError, TypeError):
        return value


def compare(before_path, after_path):
    before, br, bi = load_snapshot(before_path)
    after, ar, ai = load_snapshot(after_path)
    for key in ('session_id', 'target_id', 'pointer_size'):
        if before[key] != after[key]:
            raise ValueError(f'{key} 不同，拒绝自动跨会话/目标对齐')
    if before.get('process_id') is not None and after.get('process_id') is not None:
        if str(before['process_id']) != str(after['process_id']):
            raise ValueError('已知 PID 不同，拒绝对比')
    warnings = ['仅覆盖采集范围；变化不证明字段含义，暂停检查不等于原子快照。']
    bt = datetime.fromisoformat(before['captured_at'].replace('Z', '+00:00'))
    at = datetime.fromisoformat(after['captured_at'].replace('Z', '+00:00'))
    if at <= bt:
        warnings.append('时间戳相同或 after 早于 before：只按入参顺序比较，无法证明操作时序或因果。')
    if before.get('process_id') is None or after.get('process_id') is None:
        warnings.append('PID 未完整记录；同一进程依赖采集者提供的会话身份核验。')
    same_thread = before.get('thread_id') is not None and before.get('thread_id') == after.get('thread_id')
    register_changes = []
    if same_thread:
        for key in sorted(before['registers'].keys() | after['registers'].keys()):
            a, b = before['registers'].get(key), after['registers'].get(key)
            if comparable_register(a) != comparable_register(b):
                register_changes.append({'name': key, 'before': a, 'after': b})
    else:
        warnings.append('线程不同或未确认：不作寄存器逐值比较；内存变化可能涉及其他线程。')
    compared, incomparable = [], []
    for key in sorted(br.keys() | ar.keys()):
        a, b = br.get(key), ar.get(key)
        reason = None
        if a is None or b is None:
            reason = '范围只存在于一份快照'
        elif a['address'] != b['address'] or a['size'] != b['size']:
            reason = '基址/长度改变，需要新的对象对齐证据'
        elif a['data'] is None or b['data'] is None:
            reason = '至少一次读取失败'
        if reason:
            def context(region):
                if region is None:
                    return None
                return {'address': hex(region['address']), 'size': region['size'], 'error': region['error']}
            incomparable.append({'id': key, 'reason': reason, 'before': context(a), 'after': context(b)})
        else:
            changes = byte_changes(a['data'], b['data'])
            for block in changes['blocks']:
                block['address'] = hex(a['address'] + block['start'])
            compared.append({'id': key, 'address': hex(a['address']), 'size': a['size'], **changes})
    if not compared:
        warnings.append('没有可比较的内存范围，不能宣称内存未变化。')
    bi.update({key: before.get(key) for key in ('captured_at', 'thread_id', 'process_id', 'consistency')})
    ai.update({key: after.get(key) for key in ('captured_at', 'thread_id', 'process_id', 'consistency')})
    return {'format': 'xp-debug-diff-v1', 'sources': {'before': bi, 'after': ai},
            'session_id': before['session_id'], 'target_id': before['target_id'],
            'register_changes': register_changes, 'registers_compared': same_thread,
            'regions': compared, 'incomparable': incomparable, 'warnings': warnings}


def write_report(report, out_dir):
    root = Path(out_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    folder = root / ('xp-debug-diff-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:12])
    folder.mkdir(exist_ok=False)
    with (folder / 'report.json').open('x', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    lines = ['# XP · 调试状态差异', '', '状态：以下为字节/寄存器观察，字段语义待验证。', '', '## 来源', '']
    for label, source in report['sources'].items():
        lines.append(f"- {label}: `{source['path']}`；SHA-256 `{source['sha256']}`")
    lines += ['', '## 内存范围', '', '| 范围 | 基址 | 长度 | 精确变化字节 | 连续变化块 |', '|---|---|---|---|---|']
    for item in report['regions']:
        lines.append(f"| {item['id']} | {item['address']} | {item['size']} | {item['changed_bytes']} | {item['total_blocks']} |")
    lines += ['', '原始变化块、寄存器差异和截断标记见同目录 report.json。', '', '## 不可比较范围', '']
    lines += [f"- {item['id']}: {item['reason']}" for item in report['incomparable']] or ['- 无。']
    lines += ['', '## 限制与待验证', ''] + ['- ' + item for item in report['warnings']]
    with (folder / 'report.md').open('x', encoding='utf-8') as handle:
        handle.write('\n'.join(lines) + '\n')
    return folder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('validate').add_argument('snapshot', type=Path)
    diff = sub.add_parser('diff')
    diff.add_argument('before', type=Path)
    diff.add_argument('after', type=Path)
    diff.add_argument('--out-dir', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'validate':
            obj, regions, source = load_snapshot(args.snapshot)
            print(json.dumps({'valid': True, 'source': source, 'regions': len(regions)}, ensure_ascii=False))
        else:
            print(write_report(compare(args.before, args.after), args.out_dir))
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f'失败：{error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
