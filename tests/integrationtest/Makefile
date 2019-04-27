
prepare-data:
	mkdir -p output
	rm -f output/gtfsstaticdata.zip
	zip -jr output/gtfsstaticdata.zip data/gtfsstatic/*

test: prepare-data
	transiterclt rebuild-db --yes
	python -m unittest discover ./
