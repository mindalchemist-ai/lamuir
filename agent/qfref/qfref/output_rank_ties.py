import json, glob, os, sys


def walk(obj, path=''):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f'{path}.{k}')
    elif isinstance(obj, list):
        if len(obj) >= 3 and all(isinstance(r, dict) for r in obj):
            keys = [k for k in obj[0] if 'rank' in k.lower() and all(isinstance(r.get(k), int) for r in obj)]
            for i in range(len(keys)):
                for j in range(i + 1, len(keys)):
                    if all(r[keys[i]] == r[keys[j]] for r in obj):
                        yield path, keys[i], keys[j]
        for n, v in enumerate(obj):
            yield from walk(v, f'{path}[{n}]')
