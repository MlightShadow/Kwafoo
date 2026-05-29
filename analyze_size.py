import os

dist_path = 'd:/private_project/Kwafoo/dist'
files = []

for root, dirs, filenames in os.walk(dist_path):
    for f in filenames:
        fp = os.path.join(root, f)
        size = os.path.getsize(fp)
        files.append((fp, size))

files.sort(key=lambda x: x[1], reverse=True)

print('Top 20 largest files:')
for fp, size in files[:20]:
    print(f'{size/1024/1024:.2f} MB - {fp}')

print('\nTotal size by extension:')
ext_sizes = {}
for fp, size in files:
    ext = os.path.splitext(fp)[1].lower()
    if ext not in ext_sizes:
        ext_sizes[ext] = 0
    ext_sizes[ext] += size

for ext, size in sorted(ext_sizes.items(), key=lambda x: x[1], reverse=True):
    print(f'{ext}: {size/1024/1024:.2f} MB')