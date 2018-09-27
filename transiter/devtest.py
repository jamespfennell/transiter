from .services import routeservice
from .services import stopservice
from .services import systemservice
from .utils import jsonutil
from .data import dbexceptions


#print(jsonify(systemservice.get('nycsubway')))


#print(jsonify(stopservice.get('L03')))
#print(jsonify(routeservice.get('D')))
if(__name__=='__main__'):
    # print(jsonutil.convert_for_cli(routeservice.get_by_id(None, 'L')))
    #print(jsonutil.convert_for_cli(stopservice.get_by_id(None, 'L03')))

    try:
        systemservice.delete('nycsubway')
    except dbexceptions.IdNotFoundError:
        pass

    systemservice.install('nycsubway')




