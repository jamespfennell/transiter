
prepare-data:
	rm -f output/gtfsstaticdata.zip
	zip -jr output/gtfsstaticdata.zip data/gtfsstatic/*

test: prepare-data
	python -m unittest discover ./
