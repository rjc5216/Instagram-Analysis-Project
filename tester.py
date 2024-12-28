a = [1, 2]
b = [2, 3]

print(set(a)-set(b))

for element in a:
    if element not in b:
        print(element)
