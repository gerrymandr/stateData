out.csv: nc_sort_statewide.csv oe_2016_statewide.csv
	rm -f db.sqlite
	csvsql --db sqlite:///db.sqlite --table nc --insert nc_sort_statewide.csv
	csvsql --db sqlite:///db.sqlite --table oe --insert oe_2016_statewide.csv
	sqlite3 db.sqlite 'create index nc_precinct on nc (county_desc, precinct_code)'
	sqlite3 db.sqlite 'alter table nc add column row_matched integer default 0'
	python query.py oe_2016_statewide.csv > out.csv

oe_2016_statewide.csv: 20161108__nc__general__precinct__raw.csv
	cat 20161108__nc__general__precinct__raw.csv > $@

nc_sort_statewide.csv: results_sort_20161108.txt
	csvformat --tab results_sort_20161108.txt > $@

oe_2016_president.csv: 20161108__nc__general__precinct__raw.csv
	csvgrep -c office -m 'US PRESIDENT' 20161108__nc__general__precinct__raw.csv > $@

nc_sort_president.csv: results_sort_20161108.txt
	csvgrep --tab -c contest_name -m 'US PRESIDENT' results_sort_20161108.txt > $@

oe_2016_vance.csv: 20161108__nc__general__precinct__raw.csv
	csvgrep -c parent_jurisdiction -m 'VANCE' 20161108__nc__general__precinct__raw.csv > $@

nc_sort_vance.csv: results_sort_20161108.txt
	csvgrep --tab -c county_desc -m 'VANCE' results_sort_20161108.txt > $@

20161108__nc__general__precinct__raw.csv:
	curl --compress -o $@ -L 'https://github.com/migurski/openelections-results-nc/raw/714bcdfa798293f063879bd5881b9928d2c164fd/raw/20161108__nc__general__precinct__raw.csv'

results_sort_20161108.txt:
	curl -OL https://s3.amazonaws.com/dl.ncsbe.gov/ENRS/2016_11_08/results_sort_20161108.zip
	unzip -o results_sort_20161108.zip $@
