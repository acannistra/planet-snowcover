import requests
import pandas as pd
from shapely.geometry import mapping
from retrying import retry
from multiprocessing import Pool as ThreadPool
import os

CLIP_API_URL = "https://api.planet.com/compute/ops/clips/v1/"
ACTIVATE_API_URL = "https://api.planet.com/data/v1/item-types/{atype}/items/{id}/assets/"
PL_API_KEY = os.environ["PL_API_KEY"]

class WholeDownload(object):
    """Downloads a set of entire images."""
    @retry(wait_fixed=5000, stop_max_delay = 600000) # try for 10 minutes, 5 second delay
    def _check_active(self, id):
        r = requests.get(ACTIVATE_API_URL.format(atype=self.assettype, id=id),
                         auth=(PL_API_KEY, ""))
        print("Checking url {url}".format(url=ACTIVATE_API_URL.format(atype=self.assettype, id=id)))
        if r.json()[self.itemtype]['status'] != "active":
            print("state: {!s}".format(r.json()[self.itemtype]['status']))
            raise Exception("Not Yet")
        else:
            print("response found.")
            return(r.json())

    def __init__(self, loc_id, image_ids, dest_dir, assettype = "PSScene4Band", itemtype="analytic", _threads=5):
        super(WholeDownload, self).__init__()
        self.loc_id = loc_id
        self.image_ids = image_ids
        self.dest_dir = dest_dir
        self.assettype = assettype
        self.itemtype = itemtype
        self._threads = _threads

    def _request_and_download_image(self, id):
        print("Starting activation for image {img}".format(img=id))
        

        @retry(wait_fixed=5000,stop_max_delay=600000)
        def _start_op():
            print("querying assets at {}".format(ACTIVATE_API_URL.format(atype=self.assettype, id=id)))
            r = requests.get(ACTIVATE_API_URL.format(atype=self.assettype, id=id),
                             auth=(PL_API_KEY, ""))
            print("fetching assets...status:{}".format(r.status_code))
            
            r.raise_for_status()
            return(r)
        
        try:            
            r = _start_op()
        except Exception as e:
            print(e)
            print("error starting asset activation operation")
            return("{loc} - error starting clip operation".format(loc=self.loc_id))
        
        item_activation_url = r.json()[self.itemtype]["_links"]["activate"]
        requests.post(item_activation_url, auth = (PL_API_KEY, ""))
       
        try:
            response = self._check_active(id)
        except Exception as e:
            print(e)
            print("error retrieving clipped raster")
            return("{loc} - error retrieving clipped raster".format(loc=self.loc_id))

        image_url = response[self.itemtype]['location']

        local_filename_base = os.path.join(self.dest_dir,
                                           "{loc}_{img}".format(loc=self.loc_id, img=id))
        local_xml_filename = local_filename_base + ".xml"
        local_tif_filename = local_filename_base + ".tif"

        if(not os.path.isfile(local_tif_filename)):
            r = requests.get(image_url, stream=True, auth=(PL_API_KEY, ""))
            with open(local_tif_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
        # also get XML
        r = requests.get(response[self.itemtype+"_xml"]['location'], auth=(PL_API_KEY, ""))
        with open(local_xml_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
        
        
        return (local_tif_filename, local_xml_filename)
    
        
    
    
    def run(self):
        pool = ThreadPool(self._threads)
        filenames = pool.map(self._request_and_download_image, self.image_ids)
        return(filenames)

class CroppedDownload(object):
    """Downloads a set of cropped images for a given geometry."""
    @retry(wait_fixed=5000, stop_max_delay = 600000) # try for 10 minutes, 5 second delay
    def _check_clip_op(self, id):
        r = requests.get(
            "{_base}/{id}".format(_base=CLIP_API_URL, id=id),
            auth=(PL_API_KEY, ""))
        print("Checking url {_base}/{id}".format(_base=CLIP_API_URL, id=id))
        if r.json()['state'] != "succeeded":
            print("state: {!s}, HTTP status: {!s}".format(r.json()['state'], r.status_code))
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

        @retry(wait_fixed=5000,stop_max_delay=600000)
        def _start_op(payload):
            r = requests.post(CLIP_API_URL, auth=(PL_API_KEY, ""), json=payload)
            print("starting...{!s}".format(r.json()))
            r.raise_for_status()
            return(r)
        
        try:            
            r = _start_op(payload)
        except Exception as e:
            print(e)
            print("error starting clip operation")
            return("{loc} - error starting clip operation".format(loc=self.loc_id))
        
        try:
            response = self._check_clip_op(r.json()['id'])
        except Exception as e:
            print(e)
            print("error retrieving clipped raster")
            return("{loc} - error retrieving clipped raster".format(loc=self.loc_id))

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



