from .services import systemservice
from .services import stopservice
from .services import routeservice
from .services import feedservice
import json

def jsonify(data):
    return json.dumps(data, indent=4, separators=(',', ': '))

#systemservice.delete('nycsubway')

#systemservice.install('nycsubway')

#print(jsonify(systemservice.get('nycsubway')))


#print(jsonify(stopservice.get('L03')))
#print(jsonify(routeservice.get('D')))
print(jsonify(feedservice.update('L')))
