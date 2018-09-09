from .services import systemservice
import json

def jsonify(data):
    return json.dumps(data, indent=4, separators=(',', ': '))

systemservice.install('nycsubway')

print(jsonify(systemservice.get('nycsubway')))

systemservice.delete('nycsubway')
