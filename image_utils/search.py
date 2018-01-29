import pandas as pd
import geopandas as gpd
from tqdm import tqdm
from planet import api
from shapely.geometry import mapping
import json


class Search(object):
    """Locates image IDs for geometries and corresponding dates. 
        One -> Many relationship between geometry and dates. 'id' field is key between them. 
    """

    def __init__(self, geometries, dates):
        super(Search, self).__init__()
        # initialize api
        self._client = api.ClientV1()

        # type-check and save members
        if(isinstance(geometries, gpd.GeoDataFrame)):
            self.geometries = geometries
        else:
            raise ValueError("'geometries' must be a GeoDataFrame")
        if(isinstance(dates, pd.DataFrame) or
           isinstance(dates, gpd.GeoDataFrame)):
            self.dates = dates

    def query(self):
        _joined = self.geometries.join(self.dates, how='outer')
        result = []
        for _, row in tqdm(_joined.iterrows(), desc="Querying Planet API", unit="searches", total=len(_joined)):
            _r = self._exec(row['geometry'],
                            row['start_date'],
                            row['end_date'])
            result.append((row.name, _r))
        return(result)

    def _exec(self, geom, date_start, date_end, _opt_str=None):
        """
            Execute Planet API search. 
                Geom is Polygon (shapely). 
                Date_start/Date-end is DateTime
                _opt_str is unused.
        """
        _api_datefmt = "%Y-%m-%d"
        aoi = mapping(geom)

        query = api.filters.and_filter(
            api.filters.geom_filter(aoi),
            api.filters.date_range('acquired',
                                   gt=date_start.strftime(_api_datefmt)),
            api.filters.date_range('acquired',
                                   lt=date_end.strftime(_api_datefmt))
        )
        # we are requesting PlanetScope 4 Band imagery
        item_types = ['PSScene4Band']
        request = api.filters.build_search_request(query, item_types)
        # this will cause an exception if there are any API related errors
        results = self._client.quick_search(request)
        return(json.loads(results.get_raw())['features'])
