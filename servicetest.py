
from realtimerail.services import routeservice
from realtimerail.services import stopservice
from realtimerail.auxiliary import jsonify

#print(jsonify.jsonify(routeservice.get('GS')))
print(jsonify.jsonify(stopservice.list()))
#print(jsonify.jsonify(stopservice.get('L14')))
#print(jsonify.jsonify(stopservice.get('B08')))



#Hekko
