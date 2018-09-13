from .services import systemservice
import json

def jsonify(data):
    return json.dumps(data, indent=4, separators=(',', ': '))

systemservice.delete('nycsubway')
systemservice.install('nycsubway')

print(jsonify(systemservice.get('nycsubway')))
