import collections
import glob
import math
import os

from huggingface_hub import snapshot_download
from safetensors import safe_open

root = snapshot_download("Hcompany/Holo-3.1-4B", local_files_only=True)
sizes = collections.Counter()
for path in glob.glob(os.path.join(root, "*.safetensors")):
    with safe_open(path, "pt") as f:
        for name in f.keys():
            key = []
            for part in name.split("."):
                if part.isdigit():
                    break
                key.append(part)
            sizes[".".join(key[:3])] += math.prod(f.get_slice(name).get_shape())

for key, params in sizes.most_common():
    print(f"{params * 2 / 2**30:6.2f} GiB  {params:>13,}  {key}")
print(f"{sum(sizes.values()) * 2 / 2**30:6.2f} GiB  {sum(sizes.values()):>13,}  total")
