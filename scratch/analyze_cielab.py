import os
import sys
import json
import numpy as np
sys.path.insert(0, os.path.abspath('.'))
from ml.preprocessing.cielab_extractor import extract_mango_features

with open('ml/data/mango/splits/train_manifest.json') as f:
    train_manifest = json.load(f)

stats = {}
for item in train_manifest:
    c = item['unified_class']
    p = item['image_path']
    if not os.path.exists(p):
        p = os.path.join('ml', p)
    if os.path.exists(p):
        if c not in stats:
            stats[c] = {'mean_a': [], 'mean_b': [], 'mean_L': []}
        if len(stats[c]['mean_a']) < 80:
            feat = extract_mango_features(p, use_l=True)
            stats[c]['mean_a'].append(feat[0])
            stats[c]['mean_b'].append(feat[7])
            stats[c]['mean_L'].append(feat[19])

for c, vals in stats.items():
    ma = np.mean(vals['mean_a'])
    mb = np.mean(vals['mean_b'])
    mL = np.mean(vals['mean_L'])
    n = len(vals['mean_a'])
    print(f"{c:18s} -> N={n:2d} | a*: {ma:6.2f} | b*: {mb:6.2f} | L*: {mL:6.2f}")
