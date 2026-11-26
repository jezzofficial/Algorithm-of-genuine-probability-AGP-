import hashlib
import os
import random
import secrets

_rng = secrets.SystemRandom()


def generate_seed():
    raw = os.urandom(32)
    return hashlib.sha256(raw).hexdigest()


def build_numbers(seed_str, count=10000):
    if count < 1:
        raise ValueError("count должен быть положительным числом")
    random.seed(seed_str)
    return [random.randint(1, 10 ** 6) for _ in range(count)]


def split_by_option_biased(numbers, n):
    if n < 1:
        raise ValueError("нужно минимум одно значение (n >= 1)")

    weights = [_rng.random() + 0.1 for _ in range(n)]
    total = sum(weights)

    bounds = []
    acc = 0.0
    for w in weights:
        acc += w / total
        bounds.append(acc)

    buckets = [[] for _ in range(n)]
    for x in numbers:
        target = x / 10 ** 6
        for i, b in enumerate(bounds):
            if target <= b:
                buckets[i].append(x)
                break
    return buckets


def pick(elements, seed_str=None, count=10000):
    elements = list(elements)
    if not elements:
        raise ValueError("список элементов пуст")

    if seed_str is None:
        seed_str = generate_seed()

    numbers = build_numbers(seed_str, count)
    buckets = split_by_option_biased(numbers, len(elements))

    pool = []
    for i, bucket in enumerate(buckets):
        if not bucket:
            continue
        take = _rng.randint(0, len(bucket))
        for x in _rng.sample(bucket, take):
            pool.append((x, i))

    if not pool:
        return _rng.choice(elements), seed_str, buckets

    chosen, idx = _rng.choice(pool)
    return elements[idx], seed_str, buckets
