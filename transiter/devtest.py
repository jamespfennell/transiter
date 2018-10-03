from .services import routeservice
from .services import stopservice
from .services import systemservice
from .utils import jsonutil
from .services import exceptions


#print(jsonify(systemservice.get('nycsubway')))


#print(jsonify(stopservice.get('L03')))
#print(jsonify(routeservice.get('D')))
if(__name__=='__main__'):
    # print(jsonutil.convert_for_cli(routeservice.get_by_id(None, 'L')))
    #print(jsonutil.convert_for_cli(stopservice.get_by_id(None, 'L03')))

    try:
        systemservice.delete_by_id('nycsubway')
    except exceptions.IdNotFoundError:
        pass

    systemservice.install('nycsubway')




