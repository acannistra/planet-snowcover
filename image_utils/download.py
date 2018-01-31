import requests
import pandas as pd
from shapely.geometry import mapping
from retrying import retry
from multiprocessing.dummy import Pool as ThreadPool
import os

CLIP_API_URL = "https://api.planet.com/compute/ops/clips/v1/"
PL_API_KEY = os.environ["PL_API_KEY"]


class CroppedDownload(object):
    """Downloads a set of cropped images for a given geometry."""
    @retry(wait_fixed=5000, stop_max_delay = 600000) # try for 10 minutes, 5 second delay
    def _check_clip_op(self, id):
        r = requests.get(
            "{_base}/{id}".format(_base=CLIP_API_URL, id=id),
            auth=(PL_API_KEY, ""))
        if r.json()['state'] != "succeeded":
            print("\t...waiting")
            raise Exception("Not Yet")
        else:
            print("response found.")
            return(r.json())

    def __init__(self, loc_id, geometry, image_ids, dest_dir, _threads=5):
        super(CroppedDownload, self).__init__()
        self.loc_id = loc_id
        self.geometry = geometry
        self.image_ids = image_ids
        self.dest_dir = dest_dir
        self._threads = _threads

    def _request_and_download_image(self, id):
        print("Starting download for image {img}".format(img=id))
        payload = {
            "aoi": mapping(self.geometry),
            "targets": [{
                "item_id": id,
                "item_type": "PSScene4Band",
                "asset_type": 'analytic'
            }]
        }

        try: 
            r = requests.post(CLIP_API_URL, auth=(PL_API_KEY, ""), json=payload)
            r.raise_for_status()
        except Exception as e:
            print(e)
            return("error: {id}".format(id=id))
        
        response = self._check_clip_op(r.json()['id'])

        image_url = response['_links']['results'][0]

        local_filename = os.path.join(
            self.dest_dir, "{loc}_{img}.zip".format(loc=self.loc_id, img=id))

        r = requests.get(image_url, stream=True, auth=(PL_API_KEY, ""))
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
        return local_filename

    def run(self):
        pool = ThreadPool(self._threads)
        filenames = pool.map(self._request_and_download_image, self.image_ids)
        return(filenames)



