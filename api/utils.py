from flask_restful import abort

class MwH():
    """
    This class implement the algorithm to find the combinations of power plants that will allow us to provid the needed load at the cheapest price.
    :param:payload: a json file with the formating and the value type like the one requested. Example can be find at : https://github.com/gem-spaas/powerplant-coding-challenge/tree/master/example_payloads
    :type payload: json
    """

    def __init__(self,payload):
        # A dict use to get the cost of the powerplant for a specific power plant type 
        self.type_price =  {"gasfired": "gas(euro/MWh)",
                            "turbojet" : "kerosine(euro/MWh)",
                            "windturbine" : "wind_price"}
        
        self.payload = payload

        # Output of subset_sum function
        self.otps = []
        
        # sorted_by_load
        self.sorted_by_load = []

    # Checking the payload format
    def check_payload(self,alleged_json,logger):

        # Checks KeyError                                  
        try:
            load = alleged_json["load"]
            fuelsf = alleged_json["fuels"]["gas(euro/MWh)"]
            fuelsf = alleged_json["fuels"]["kerosine(euro/MWh)"]
            fuelsf = alleged_json["fuels"]["co2(euro/ton)"]
            fuelsf = alleged_json["fuels"]["wind(%)"]
            
            pws = alleged_json["powerplants"]
            
            if isinstance(pws,list):
                v = [i["name"] for i in pws]
                typs = [i["type"] for i in pws]
                v = [i["efficiency"] for i in pws]
                v = [i["pmin"] for i in pws]
                v = [i["pmax"] for i in pws]
                
                try:
                    v2 = [self.type_price[t] for t in typs]
                except KeyError as e:
                    logger.error(f"{e} is not one of the powerplants type accepted. The request has been abort.")
                    abort(406,message=f"{e} is not one of the powerplants type accepted.Please make sure your payload has the right formating.")
            
        except KeyError as e:
            logger.error(f"{e} was not one of the keys in the json file provided. The request has been abort.")
            abort(406,message=f"{e} was not one of the keys in the json file provided. This key is needed to have a response to your request. Please provide one and make sure your payload has the right formating.")


    # Updating the payload : pmax, cost according to efficiency or wind%
    # Output : self.new_payload, type : dict
    def new_load(self):
        self.new_payload = self.payload.copy()
        # Calculating the actual cost of a power plant base on it efficiency. Windmills cost of use is considered equal to 0
        for i,plant in enumerate(self.new_payload["powerplants"]):
            if plant["type"] != "windturbine":
                self.new_payload["powerplants"][i]["new_price"] = round((1/plant["efficiency"])*self.new_payload["fuels"][self.type_price[plant["type"]]],2)
            else:
                # The efficiency of windmills depend on the wind(%) value
                self.new_payload["powerplants"][i]["new_price"] = 0
                self.new_payload["powerplants"][i]["pmax"] = round(plant["pmax"]*(self.new_payload["fuels"]["wind(%)"]/100),3)    


    

    # Find all combinations of powerplants that can provid as much or more than the load needed
    # This function update self.otps, type : list
    # The format is : ([(<powerplant name>,<powerplant pmax>,<powerplant updated price>,<powerplant type>,<powerplant pmin>),..,(<powerplant name>,<powerplant pmax>,<powerplant updated price>,<powerplant type>,<powerplant pmin>),<The sum of the pmax>,<The total cost>])
    def subset_sum(self,powerplants, target,otps=[], partial=[], partial_sum=0):
        if partial_sum >= target:
            # We append to the output list (otps) a list of tuples which the sum of the pmax of each item is equal to the targeted load or greater
            otps.append((partial,sum([p[1] for p in partial]),sum([p[2] for p in partial])))
        for i, n in enumerate(powerplants):
            remaining = powerplants[i + 1:]
            # As our approach is recursive, we run the subset_sum again to find suitable power plants combinations on the remaining powerplants
            self.subset_sum(remaining, target,otps, partial + [(n["name"],n["pmax"],n["new_price"],n["type"],n["pmin"])], partial_sum + n["pmax"])

    
    # This function use self.otps and try to reduce the produce power to reduce the price if the total power is greater that the targeted load, all that according to the pmin
    # The result is then sorted by the sum of updated pmax
    # The total cost is then also updated
    # The function will also reduce the most it can the power produce if he can't find a way to have the power produced equal to the target load. The power produced will then be greater than the target load
    # For the example payload, as requested, we do reach the targeted load
    # Update self.sorted_by_load, type : list
    def sorter(self):
        # initializing a list to contain the outputs before sorting by the total updated load
        result_out = []
        # sorting each powerplant combinasion by total pmax
        sorted_target = sorted(self.otps, key=lambda tup: tup[1], reverse= False)
        # Iterating through all powerplants combinasions
        for itm in sorted_target:
            results = []
            p,total,price = itm
            far_from = total-self.payload["load"] # total power produced - target power
            drop_values = [] # Will be use to store powerplants combinasions were all the extra power produce can be dropped
            to_far = [] # Will be use to store powerplants combinasions were were the pmin do not allow us to reduce enough the extra power to reach the targeted power level
            to_add = []
            # Iterating through each powerplant in a combinasion
            for utm in p:
                #  Check if the powerplant is a Windmill. Willmill can either be on or off. We cannot turn them of during their rent time.
                # Therefore if a windmill is already part of our combinasion, we cannot produce less than the pmax
                if utm[3] != "windturbine":
                    name = utm[0]
                    room = utm[1]-utm[-1] # pmax - pmin
                    prc = utm[2] # powerplant cost
                    if room> far_from:
                        drop_values.append((name,far_from,far_from*prc))

                    else:
                        to_far.append((name,room,room*prc,utm[1],prc))
                else:
                    to_add.append((utm[0],utm[1],utm[2]))
            if len(drop_values)>0: 
                # Sorting by power reduction cost. Cheapest to expensive   
                sorted_drop = sorted(drop_values, key=lambda tup: tup[2], reverse= False)
                for utm2 in p:
                    # if the name of the powerplant do not match the most expensive powerplant, we keep it
                    if utm2[0] != sorted_drop[-1][0]:
                        results.append(utm2)
                    else:
                        # As the name match the most expensive powerplant, we reduce the power there
                        results.append((sorted_drop[-1][0],utm2[1]-sorted_drop[-1][1],utm2[2]))
                        
                results = results+to_add
            
            elif len(to_far)>0:
                # Sorting by power reduction cost from most expensive to cheapest
                sorted_far = sorted(to_far, key=lambda tup: tup[2], reverse= True)
                left_over = far_from
                for j in sorted_far:
                    if left_over > 0:
                        to_take_out = j[1]-left_over # room-left_over to reduce
                        if to_take_out<0:
                            results.append((j[0],j[3]-j[1],j[4]))
                            left_over = left_over-j[1]
                        else:
                            results.append((j[0],j[3]-left_over,j[4]))
                            left_over = 0
                    else:
                        results.append((j[0],j[3],j[4]))
                        
                results = results+to_add
            else:
                results = p
            
            # append the powerplants combinasions with the updated total cost and total power produced by 
            result_out.append((results,sum(kk[1] for kk in results),sum(kk[1]*kk[2] for kk in results),sum(kk[1] for kk in results) == self.payload["load"]))

        # Update self.sorted_by_load with the list of combinasion sorted by their total power produced    
        self.sorted_by_load =  sorted(result_out, key=lambda tup: tup[1], reverse= False)
            

    # Select the combinasion of powerplant that is equal to the load key value in the payload and set it to the json format requiered as a response
    def to_send(self):
        # get all powerplants names
        plant_names = [plant["name"] for plant in [i for i in self.new_payload["powerplants"]]]
        # Select the powerplants combinasions were the total power produced is equal to the targeted load
        chosen_ones = [i for i in self.sorted_by_load if i[3] == True]
        if len(chosen_ones)>0:
            # Get the cheapest form the chosen_ones
            selected = sorted(chosen_ones, key=lambda tup: tup[2], reverse= False)[0]
        else:
            # get the combinasion of powerplants closest to the target load if there is no chosen_ones
            selected = sorted(self.sorted_by_load, key=lambda tup: tup[1], reverse= False)[0]

        # Set selected to the requiered format as a json respone
        to_send_list = [{"name": itm[0],"p":itm[1]*0.1} for itm in [name for name in selected[0]]]
        s_names = [s["name"] for s in to_send_list]
        for n in plant_names:
            if n not in s_names:
                to_send_list.append({"name":n,"p":0})

        return to_send_list