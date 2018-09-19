# Mapbox [`robosat`](https://github.com/mapbox/robosat/) + Planet Workflow

1. Convert Planet image extent into shapefile using `gdaltindex [image]`
2. Threshold SWE mask with `gdalcalc.py` 

	gdal_calc.py -A [SWE_MASK].tif --outfile [SWE_MASK]_thresh.tif --calc="0*(A<[THRESHOLD])" --calc="1*(A>[THRESHOLD])"

3. Crop resulting thresholded mask with image extent using `gdalwarp -cutline [sat_image_extent] -crop_to_cutline [thresh_swe_mask] output...etc`. **Carefully consider CRS here**. 
4. Convert cropped mask to polygons using `gdal_polygonize.py`. 
5. Convert image to tiles USING NEW SCRIPT [HERE](https://gist.github.com/jeffaudi/9da77abf254301652baa) (the stock `gdal2tiles.py` switches north and south in an infuriating way)
6. Rasterize GeoJSON Polygons from ASO created above using `./rs rasterize`. You'll likely want to use the Dockerized version of Robosat. 
7. Compute tile cover over GeoJSON polygons using `./rs cover`.
8. Use `./rs download` to "download" proper tiles from the tiled Planet image from step 5. The best way to do this is to enter into your image tile folder and run a simple Python http server (`python -m http.server`) then point `./rs download` to `http://localhost`/
9. Divide tiles into train and test set (best way to do this is to find list of tile names, divide into 2 groups, and copy the corresponding files and folders (see Python function `os.makedirs` to copy the directory structure as you do this).
10. Follow instructions on robosat github page to create a `model.toml` file and a `dataset.toml`. 
11. Run u-net training `./rs train` using documentation. 
12. Use `./rs predict` and `./rs mask` to see results using your test data. 
