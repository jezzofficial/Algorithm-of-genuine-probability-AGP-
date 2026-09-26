import random
import hashlib
import os
import colorama

def generate_seed():
    raw = os.urandom(32)
    return hashlib.sha256(raw).hexdigest()


def build_numbers(seed_str, count=10000):
    random.seed(seed_str)
    return [random.randint(1, 10**6) for _ in range(count)]


def split_by_option_biased(numbers, n):
    rng = random.Random()

    weights = [rng.random() + 0.1 for _ in range(n)]
    total = sum(weights)

    bounds = []
    acc = 0.0
    for w in weights:
        acc += w / total
        bounds.append(acc)

    buckets = [[] for _ in range(n)]
    for x in numbers:
        target = x / 10**6      
        for i, b in enumerate(bounds):
            if target <= b:
                buckets[i].append(x)
                break
    return buckets


def pick(elements, seed_str=None):
    n = len(elements)

    if seed_str is None:
        seed_str = generate_seed()

    numbers = build_numbers(seed_str)
    buckets = split_by_option_biased(numbers, n)

    pool = []
    for i, bucket in enumerate(buckets):
        if not bucket:
            continue
        take = random.randint(0, len(bucket))
        for x in random.sample(bucket, take):
            pool.append((x, i))

    if not pool:
        return random.choice(elements), seed_str, buckets

    chosen, idx = random.choice(pool)
    return elements[idx], seed_str, buckets


def main():
	try:
		n = int(input(f"Сколько элементов? {colorama.Fore.BLUE}(int):{colorama.Fore.RESET} "))
	except ValueError:
		print(f"{colorama.Fore.RED}Нужно ввести целое число. {colorama.Fore.WHITE}Попробуйте еще раз!")
		exit()
    
	elements = [input(f"Элемент {i+1}: ") for i in range(n)]
	winner, seed, buckets = pick(elements)

	print('-----------')
	print(f"{colorama.Fore.GREEN}Сгенерированный сид:{colorama.Fore.WHITE}", seed)
	print(f"{colorama.Fore.YELLOW}Размеры бакетов:{colorama.Fore.WHITE}", [len(b) for b in buckets])
	print('-----------')
	print("Победитель:", winner)


if __name__ == "__main__":
    main()