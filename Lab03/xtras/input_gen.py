import random
import sys

N = int(sys.argv[1])
random.seed(int(sys.argv[2]))

ranges = [random.randint(10, 14) for _ in range(4)]
bitstrings = ["".join([str(random.choice([0, 1])) for _ in range(ranges[i])]) for i in range(4)]

if N == 3:
    two_m = random.choice([_ for _ in range(1, N+1)])
    new_list = list(range(1, N+1))
    new_list.remove(two_m)
    broadcast = random.choice([_ for _ in new_list])

    for i in range(1, 4):
        print(f"========= Node {i} ===========")
        if two_m == i:
            new_list_1 = list(range(1, N+1))
            new_list_1.remove(i)
            print(bitstrings.pop(), random.choice(new_list_1))
            print(bitstrings.pop(), random.choice(new_list_1))

        elif broadcast == i:
            print(bitstrings.pop(), 0)
            print(0, -1)
        
        else:
            new_list_2 = list(range(1, N+1))
            new_list_2.remove(i)
            print(bitstrings.pop(), random.choice(new_list_2))
            print(0, -1)

if N == 2:
    for i in range(1, 3):
        adj_node = 3 - i
        print(f"========= Node {i} ===========")

        print(bitstrings.pop(), adj_node)
        print(bitstrings.pop(), adj_node)
        