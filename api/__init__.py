from flask_restful import Api
from run import app

from .productionplan import ProductionPlan

api = Api(app)


api.add_resource(ProductionPlan,"/productionplan")