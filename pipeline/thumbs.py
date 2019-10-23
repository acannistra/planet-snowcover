import pandas as pd
from sys import argv, exit
import matplotlib.pyplot as plt
from json import loads
import requests
from io import BytesIO
from PIL import Image
from os.path import expanduser
from math import ceil, floor
from tqdm import tqdm


API_URL = "https://tiles.planet.com/data/v1/item-types/{asset}/items/{id}/thumb?api_key={key}&width=2048"

ids = []
asset = ""
try:
    ids = pd.read_csv(argv[1], header = None, names = ['id'])
    asset = argv[2]
except Exception as e:
    print("usage: thumbs.py idlist.csv asset")
    exit(1)

API_KEY = ""
try:
    API_KEY = loads(open(expanduser('~/.planet.json'), 'r').read())['key']
except Exception as e:
    print(e)
    print("run planet init")
    exit(1)


n_thumbs = len(ids)
fig, ax = plt.subplots(ceil(n_thumbs / 3), 3, figsize=(15,30))


for i, thumb in tqdm(ids.iterrows(), unit='img', total=n_thumbs):
    url = API_URL.format(id=thumb.id, asset = asset, key= API_KEY)
    img = requests.get(url)
    img = Image.open(BytesIO(img.content))
    ax[floor(i/3), i%3].imshow(img)
    ax[floor(i/3), i%3].set_title(thumb.id)

plt.tight_layout()
plt.savefig("{}_thumbs.pdf".format(argv[1]))
fig.show()
