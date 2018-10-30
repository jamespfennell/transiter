import csv


def read_csv(csv_file_path):
    with open(csv_file_path) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            yield row


with open('direction_name_rules_basic.csv', 'w') as f:

    f.write('stop_id,direction_id,direction_name\n')
    for row in read_csv('direction_names.csv'):
        f.write('{},{},"{}"\n'.format(
            row['stop_id'],
            '0',
            row['south_direction_name']
        ))
        f.write('{},{},"{}"\n'.format(
            row['stop_id'],
            '1',
            row['north_direction_name']
        ))

with open('direction_name_rules_with_track.csv', 'w') as f:

    f.write('stop_id,direction_id,track,direction_name\n')
    for row in read_csv('direction_name_exceptions.csv'):
        if row['direction'] == 'N':
            direction_id = '1'
        else:
            direction_id = '0'
        f.write('{},{},{},"{}"\n'.format(
            row['stop_id'],
            direction_id,
            row['track'],
            row['name']
        ))
