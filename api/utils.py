from flask_restful import abort

class MwH():
    def __init__(self,payload):
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
                    abort(f"{e} is not one of the powerplants type accepted.Please make sure your payload has the right formating.")
            
        except KeyError as e:
            logger.error(f"{e} was not one of the keys in the json file provided. The request has been abort.")
            abort(f"{e} was not one of the keys in the json file provided. This key is needed to have a response to your request. Please provide one and make sure your payload has the right formating.")


    # Updating the payload : pmax, cost according to efficiency or wind%
    def new_load(self):
        self.new_payload = self.payload.copy()
        for i,plant in enumerate(self.new_payload["powerplants"]):
            if plant["type"] != "windturbine":
                self.new_payload["powerplants"][i]["new_price"] = round((1/plant["efficiency"])*self.new_payload["fuels"][self.type_price[plant["type"]]],2)
            else:
                self.new_payload["powerplants"][i]["new_price"] = 0
                self.new_payload["powerplants"][i]["pmax"] = round(plant["pmax"]*(self.new_payload["fuels"]["wind(%)"]/100),3)    


    

    # Find all combinations of powerplants that can provid as much or more than the load needed
    def subset_sum(self,powerplants, target,otps=[], partial=[], partial_sum=0):
        if partial_sum >= target:
            otps.append((partial,sum([p[1] for p in partial]),sum([p[2] for p in partial])))
        for i, n in enumerate(powerplants):
            remaining = powerplants[i + 1:]
            self.subset_sum(remaining, target,otps, partial + [(n["name"],n["pmax"],n["new_price"],n["type"],n["pmin"])], partial_sum + n["pmax"])

    
    # Sorting and trying to redure powerplant power to reach the load or get close
    def sorter(self):
        result_out = []
        sorted_target = sorted(self.otps, key=lambda tup: tup[1], reverse= False)
        for itm in sorted_target:
            results = []
            p,total,price = itm
            far_from = total-self.payload["load"]
            drop_values = []
            to_far = []
            to_add = []
            for utm in p:
                if utm[3] != "windturbine":
                    name = utm[0]
                    room = utm[1]-utm[-1]
                    prc = utm[2]
                    if room> far_from:
                        drop_values.append((name,far_from,far_from*prc))

                    else:
                        to_far.append((name,room,room*prc,utm[1],prc))
                else:
                    to_add.append((utm[0],utm[1],utm[2]))
            if len(drop_values)>0:    
                sorted_drop = sorted(drop_values, key=lambda tup: tup[2], reverse= False)
                for utm2 in p:
                    if utm2[0] != sorted_drop[-1][0]:
                        results.append(utm2)
                    else:
                        results.append((sorted_drop[-1][0],utm2[1]-sorted_drop[-1][1],utm2[2]))
                        
                results = results+to_add
            
            elif len(to_far)>0:
                sorted_far = sorted(to_far, key=lambda tup: tup[2], reverse= True)
                left_over = far_from
                for j in sorted_far:
                    if left_over > 0:
                        to_take_out = j[1]-left_over
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
            
            result_out.append((results,sum(kk[1] for kk in results),sum(kk[1]*kk[2] for kk in results),sum(kk[1] for kk in results) == self.payload["load"]))
            
        self.sorted_by_load =  sorted(result_out, key=lambda tup: tup[1], reverse= False)
            

    # variable to json to send
    def to_send(self):
        plant_names = [plant["name"] for plant in [i for i in self.new_payload["powerplants"]]]
        chosen_ones = [i for i in self.sorted_by_load if i[3] == True]
        if len(chosen_ones)>0:
            selected = sorted(chosen_ones, key=lambda tup: tup[2], reverse= False)[0]
        else:
            selected = sorted(self.sorted_by_load, key=lambda tup: tup[1], reverse= False)[0]

        to_send_list = [{"name": itm[0],"p":itm[1]*0.1} for itm in [name for name in selected[0]]]
        s_names = [s["name"] for s in to_send_list]
        for n in plant_names:
            if n not in s_names:
                to_send_list.append({"name":n,"p":0})

        return to_send_list