import random

from turingarena import *

algorithm = submitted_algorithm()

all_passed = True
for _ in range(10):
    value_range = range(10 ** 3, 5 * 10 ** 3)
    a, b = random.choices(value_range, k=2)

    try:
        with algorithm.run() as process:
            c = process.call.sum(a, b)
    except AlgorithmError as e:
        print(f"{a} + {b} --> {e}")
        all_passed = False
    if c != a + b:
        print(f"{a} + {b} --> {c} (wrong!)")
        all_passed = False
    print(f"{a} + {b} --> {c} (correct)")

evaluation_result(goals=dict(correct=all_passed))
