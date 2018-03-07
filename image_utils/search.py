import pandas as pd
import geopandas as gpd
from tqdm import tqdm
from planet import api
from shapely.geometry import mapping
import json


class Search(object):
    """Locates image IDs for geometries and
        corresponding dates.
        One -> Many relationship between geometry 
        and dates. 'id' field is key between them. 
    """

    def __init__(self, geometries, dates, dry=False, key="id",
                 start_col="start_date", end_col="end_date", item_type = "PSScene4Band"):
        super(Search, self).__init__()
        # initialize api
        self._client = api.ClientV1()
        self.dry = dry
        self.key = key
        self.start_col = start_col
        self.end_col = end_col
        self.item_type = item_type

        # type-check and save members
        if(isinstance(geometries, gpd.GeoDataFrame)):
            self.geometries = geometries
        else:
            raise ValueError("'geometries' must be a GeoDataFrame")
        if(isinstance(dates, pd.DataFrame) or
           isinstance(dates, gpd.GeoDataFrame)):
            self.dates = dates

    def query(self):
        _joined = self.dates.join(self.geometries.set_index(self.key),
                                  on=self.key, how='left',
                                  lsuffix='Left')
        result = []
        for _, row in tqdm(_joined.iterrows(),
                           desc="Querying Planet API",
                           unit="searches", total=len(_joined)):
            if(self.dry):
                print("Dry run, not executing search"
                      ". {id}:{start} - {end}".format(id=row[self.key],
                                                      start=row[self.start_col],
                                                      end=row[self.end_col]))
                continue
            _r = self._exec(row['geometry'],
                            row[self.start_col],
                            row[self.end_col])
            _r['loc_id'] = row.name
            result.append(_r)
        return(pd.concat(result))

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
        item_types = [self.item_type]
        request = api.filters.build_search_request(query, item_types)
        # this will cause an exception if there are any API related errors
        results = self._client.quick_search(request)
        return(pd.read_json(json.dumps(json.loads(results.get_raw())['features'])))
