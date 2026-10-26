#!/usr/bin/env python3
"""解析子智能体模型设置；不启动子智能体，不修改配置或主模型。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / 'references' / 'config.json'
FIELDS = ('model', 'reasoning_effort')


def resolve(config, model=None, effort=None):
    if not isinstance(config, dict) or set(config) != set(FIELDS):
        raise ValueError('配置必须且仅包含 model 和 reasoning_effort')
    for key in FIELDS:
        if not isinstance(config[key], str) or not config[key].strip():
            raise ValueError(f'{key} 必须为非空字符串')
    overrides = {'model': model, 'reasoning_effort': effort}
    result = {}
    for key in FIELDS:
        value = overrides[key] if overrides[key] is not None else config[key]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'本次 {key} 覆盖必须为非空字符串')
        value = value.strip()
        result[key] = {'value': value, 'mode': 'inherit' if value == 'inherit' else 'specific',
                       'source': 'invocation' if overrides[key] is not None else 'config'}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--model', help='本次覆盖的模型 ID，或 inherit')
    parser.add_argument('--effort', help='本次覆盖的推理档位，或 inherit')
    args = parser.parse_args()
    try:
        with args.config.open(encoding='utf-8-sig') as handle:
            result = resolve(json.load(handle), args.model, args.effort)
        print(json.dumps({'requested': result, 'runtime_validation_required': True}, ensure_ascii=False, indent=2))
    except (OSError, ValueError, TypeError) as error:
        print(f'配置错误：{error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
