from flask import request,jsonify
from flask_restful import Resource,abort
import logging 
from .utils import MwH
import os

# logger_tracker
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s —""%(funcName)s:%(lineno)d — %(message)s")
file_handler = logging.FileHandler(os.path.join(os.getcwd(),"api","logs","productionplan.log"))
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
# RuntimeError logger
logger_rte = logging.getLogger("api.productionplan_rte")
logger_rte.setLevel(logging.ERROR)
formatter = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s —""%(funcName)s:%(lineno)d — %(message)s")
file_handler = logging.FileHandler(os.path.join(os.getcwd(),"api","logs","productionplanRuntimeError.log"))
file_handler.setFormatter(formatter)
logger_rte.addHandler(file_handler)

class ProductionPlan(Resource):

    def post(self):
        json_data = request.get_json()
        if json_data == None:
            logger.error("The data provided is not a json file. The post request has been abort")
            abort(406,message="The data provided is not a json file. Please provide one.")

        logger.info("json_data : Ok")


        # Instantiate the unit commitement class algorithm
        try:
            power_commitment = MwH(json_data)
        except Exception as e:
            if type(e) == RuntimeError:
                logger_rte.exception("RuntimeError during the initialisation of the unit commitment algorithm class")
                logger.exception("RuntimeError during the initialisation of the unit commitment algorithm class")
                abort(500,message="RuntimeError during the initialisation of the unit commitment algorithm class. Check log file for more information.")
            else:
                logger.exception(f"{type(e)} during the initialisation of the unit commitment algorithm class")
                abort(500,message=f"{type(e)} during the initialisation of the unit commitment algorithm class during the initialisation of the unit commitment algorithm class. Check log file for more information.")                
        
        logger.info("MwH : Ok")

        # Checking the payload format
        try:
            power_commitment.check_payload(json_data,logger)
        except Exception as e:
            if type(e) == RuntimeError:
                logger_rte.exception("RuntimeError during the payload format checking")
                logger.exception("RuntimeError during the payload format checking")
                abort(500,message="RuntimeError during the payload format checking. Check log file for more information.")
            else:
                logger.exception(f"{type(e)} during the payload format checking")
                abort(500,message=f"{type(e)} during the payload format checking. Check log file for more information.")

        logger.info("check_payload : Ok")

        
        # Updating the pmax, price according to the efficiency data and wind%
        try:
            power_commitment.new_load()
        except Exception as e:
            if type(e) == RuntimeError:
                logger_rte.exception("RuntimeError while updating the pmax, price according to the efficiency data and wind%")
                logger.exception("RuntimeError while updating the pmax, price according to the efficiency data and wind%")
                abort(500,message="RuntimeError while updating the pmax, price according to the efficiency data and wind%. Check log file for more information.")
            else:
                logger.exception(f"{type(e)} while updating the pmax, price according to the efficiency data and wind%")
                abort(500,message=f"{type(e)} while updating the pmax, price according to the efficiency data and wind%. Check log file for more information.")                
            

        logger.info("new_load : Ok")

        # Finding all the combinasions of powerplants that can provide the needed load or more
        try:
            power_commitment.subset_sum(powerplants=power_commitment.new_payload["powerplants"],target=power_commitment.new_payload["load"],otps= power_commitment.otps)
        except Exception as e:
            if type(e) == RuntimeError:
                logger_rte.exception("RuntimeError while looking for all the combinasions of powerplants that can provide the needed load or more")
                logger.exception("RuntimeError while looking for all the combinasions of powerplants that can provide the needed load or more")
                abort(500,message="RuntimeError while looking for all the combinasions of powerplants that can provide the needed load or more. Check log file for more information.")
            else:
                logger.exception(f"{type(e)} while looking for all the combinasions of powerplants that can provide the needed load or more")
                abort(500,message=f"{type(e)} while looking for all the combinasions of powerplants that can provide the needed load or more. Check log file for more information.")

        logger.info("subset_sum : Ok")

        # Finding all the powerplants that can have their power output reduce to have the combinasion be equal to the targeted load or more close if none can and sorting the output by power provided
        try:
            power_commitment.sorter()
        except Exception as e:
            if type(e) == RuntimeError:
                logger_rte.exception("RuntimeError while looking for  all the powerplants that can have their power output reduce to have the combinasion be equal to the targeted load or more close if none can and sorting the output by power provided")
                logger.exception("RuntimeError while looking for  all the powerplants that can have their power output reduce to have the combinasion be equal to the targeted load or more close if none can and sorting the output by power provided")
                abort(500,message="RuntimeError while looking for  all the powerplants that can have their power output reduce to have the combinasion be equal to the targeted load or more close if none can and sorting the output by power provided. Check log file for more information.")
            else:
                logger.exception(f"{type(e)} while looking for  all the powerplants that can have their power output reduce to have the combinasion be equal to the targeted load or more close if none can and sorting the output by power provided")
                abort(500,message=f"{type(e)} while looking for  all the powerplants that can have their power output reduce to have the combinasion be equal to the targeted load or more close if none can and sorting the output by power provided. Check log file for more information.")                      
        logger.info("sorter : Ok")
        
        # Selecting the combinasion of powerplant that is equal to the targeted load and the cheapest our the one closest to the targeted load.
        # As requiered, for the exemple payload provided, the selected payload have their power sum equal to the targeted payload
        try:
            response_data = power_commitment.to_send()
        except Exception as e:
            if type(e) == RuntimeError:
                logger_rte.exception("RuntimeError while selecting the combinasion of powerplant that is equal to the targeted load and the cheapest our the one closest to the targeted load.")
                logger.exception("RuntimeError while selecting the combinasion of powerplant that is equal to the targeted load and the cheapest our the one closest to the targeted load.")
                abort(500,message="RuntimeError while selecting the combinasion of powerplant that is equal to the targeted load and the cheapest our the one closest to the targeted load.. Check log file for more information.")
            else:
                logger.exception(f"{type(e)} while selecting the combinasion of powerplant that is equal to the targeted load and the cheapest our the one closest to the targeted load.")
                abort(500,message=f"{type(e)} while selecting the combinasion of powerplant that is equal to the targeted load and the cheapest our the one closest to the targeted load.. Check log file for more information.")

        logger.info("to_send : Ok")

        logger.info(f"Everything went smoothly. The output was : {response_data}")
        return response_data,200

