check:
	pytest tests
	@echo ""
	@echo "==="
	black -l 125 --diff robosat_pink/*py robosat_pink/*/*.py
	@echo "==="
	@echo ""
	flake8 --max-line-length 125 --ignore=E203,E241,E226,E272,E261,E221,W503,E722


black:
	black -l 125 robosat_pink/*py robosat_pink/*/*.py


it: clean
	rsp cover --zoom 18 --type bbox 4.8,45.7,4.83,45.73  it/cover

	rsp download --rate 20 --type WMS 'https://download.data.grandlyon.com/wms/grandlyon?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=Ortho2015_vue_ensemble_16cm_CC46&WIDTH=512&HEIGHT=512&CRS=EPSG:3857&BBOX={xmin},{ymin},{xmax},{ymax}&FORMAT=image/jpeg' --web_ui it/cover it/images
	rsp download --rate 20 --type WMS 'https://download.data.grandlyon.com/wms/grandlyon?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=Ortho2015_vue_ensemble_16cm_CC46&WIDTH=512&HEIGHT=512&CRS=EPSG:3857&BBOX={xmin},{ymin},{xmax},{ymax}&FORMAT=image/jpeg' --web_ui it/cover it/images

	wget -nc -O it/lyon_roofprint.json 'https://download.data.grandlyon.com/wfs/grandlyon?SERVICE=WFS&REQUEST=GetFeature&TYPENAME=ms:fpc_fond_plan_communaut.fpctoit&VERSION=1.1.0&srsName=EPSG:4326&BBOX=4.79,45.69,4.84,45.74&outputFormat=application/json; subtype=geojson' | true

	rsp rasterize --config config.toml --zoom 18 --web_ui it/lyon_roofprint.json it/cover it/labels

	rm -rf it/training it/validation
	mkdir it/training it/validation

	cat it/cover | sort -R > it/cover.shuffled
	head -n 500 it/cover.shuffled > it/training/cover
	tail -n 236 it/cover.shuffled > it/validation/cover

	rsp subset --web_ui --dir it/images --cover it/training/cover --out it/training/images
	rsp subset --web_ui --dir it/labels --cover it/training/cover --out it/training/labels
	rsp subset --web_ui --dir it/images --cover it/validation/cover --out it/validation/images
	rsp subset --web_ui --dir it/labels --cover it/validation/cover --out it/validation/labels

	rsp train --config config.toml --workers 0 --epochs 5 --dataset it it/pth
	rsp train --config config.toml --workers 0 --resume --checkpoint it/pth/checkpoint-00005-of-00005.pth --epochs 10 --dataset it it/pth
	rsp predict --config config.toml --workers 0 --batch_size 16 --checkpoint it/pth/checkpoint-00010-of-00010.pth --web_ui it/images it/masks

	rsp compare --images it/images it/labels it/masks --mode stack --labels it/labels --masks it/masks --config config.toml --web_ui it/compare

	rsp compare --mode list --labels it/labels --maximum_qod 70 --minimum_fg 5 --masks it/masks --config config.toml --geojson it/tiles.json



clean:
	rm -rf it
