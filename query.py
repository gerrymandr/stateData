import sqlite3, csv, datetime, sys

updated_at, _ = str(datetime.datetime.utcnow()).split('.', 1)

fieldnames = (
    'updated_at', 'id', 'start_date', 'end_date', 'election_type',
    'result_type', 'special', 'office', 'district', 'name_raw', 'last_name',
    'first_name', 'suffix', 'middle_name', 'party', 'parent_jurisdiction',
    'jurisdiction', 'division', 'votes', 'votes_type', 'total_votes', 'winner',
    'write_in', 'year', 'absentee_by_mail', 'election_day', 'one_stop',
    'provisional',
    )

(filename, ) = sys.argv[1:]
candidates, offices = dict(), set()

with open(filename) as file, sqlite3.connect('db.sqlite') as db:
    out = csv.DictWriter(sys.stdout, fieldnames)
    out.writeheader()
    
    db.execute('update nc set row_matched = 0')

    for oe_row in csv.DictReader(file):
        compare = (oe_row['parent_jurisdiction'], oe_row['jurisdiction'],
            '{}%'.format(oe_row['office']), oe_row['name_raw'])
        
        print(compare, file=sys.stderr)
        offices.add(oe_row['office'])
        candidates[oe_row['name_raw']] = {k: v for (k, v) in oe_row.items()
            if k in ('last_name', 'first_name', 'suffix', 'middle_name', 'party')}

        row = {k: v for (k, v) in oe_row.items() if k in out.fieldnames}
        row['updated_at'] = updated_at
        row['votes'] = None
        row['absentee_by_mail'] = None
        row['election_day'] = None
        row['one_stop'] = None
        row['provisional'] = None

        nc_rows = db.execute('''
            select rowid, votes
            from nc
            where county_desc = ? and precinct_code = ?
              and contest_name like ? and candidate_name = ?
            ''', compare)
        
        for (rowid, votes) in nc_rows:
            row['votes'] = votes
            db.execute('update nc set row_matched = 1 where rowid = ?', (rowid, ))
            break
        
        print('votes:', row['votes'], file=sys.stderr)
        out.writerow(row)
    
    for office in offices:
        nc_rows = db.execute('''
            select county_desc, contest_name, candidate_name, sum(votes)
            from nc where row_matched = 0 and contest_name like ?
            group by county_desc, contest_name, candidate_name
            ''', ('{}%'.format(office), ))
        
        for (county_desc, contest_name, candidate_name, votes) in nc_rows:
            if candidate_name not in candidates:
                continue

            print((county_desc, contest_name, candidate_name, votes), file=sys.stderr)
            
            missed_row = {field: None for field in out.fieldnames}
            missed_row.update(candidates[candidate_name])
            missed_row.update({k: v for (k, v) in oe_row.items()
                if k in ('id', 'updated_at', 'start_date', 'end_date',
                    'election_type', 'result_type', 'special', 'year')})

            missed_row.update(office=office, name_raw=candidate_name,
                parent_jurisdiction=county_desc, jurisdiction=None, votes=votes,
                division='ocd-division/country:us/state:nc/county:{}'.format(county_desc.lower()))
            
            out.writerow(missed_row)

print('offices:', offices, file=sys.stderr)
