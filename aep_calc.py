import pandas as pd
import numpy as np
from wse_extract import WSE_extract

class AEP_calc:

    def __init__(
            self,
            wse_extract: WSE_extract,
            aep: list,
            weight_file: str
    ):
        self.__wse_data = wse_extract.extract()
        self.__aep = aep
        self.__weights = pd.read_csv(weight_file, header=0)
    

    
    def __get_AEP_value(self, data) -> list[np.float64]:
        exceedance_values = []
        for p in self.__aep:
            if(p>max(data['cdf'])):
                exceedance_values.append(max(data['wse']))
            else:
                above = data[data.cdf>=p]
                exceedance_values.append(above['wse'].iloc[0])
        return exceedance_values
    
    def __exponentiate(self, data) -> list[np.float64]:
        return data
    
    def __process_location_AEP(self, data) -> list[np.float64]:
        point_data = self.__weights
        point_data['wse'] = data.tolist()
        point_data.sort_values(by=['wse'], inplace=True)
        point_data['cdf_single_storm'] = np.cumsum(point_data['P'])
        point_data['cdf'] = self.__exponentiate(point_data['cdf_single_storm'].to_list())
        return self.__get_AEP_value(point_data)
    
    def return_AEP(self) -> list:
        print("Getting AEP")
        AEP_data = self.__wse_data.apply(self.__process_location_AEP, axis=1)
        
        return(pd.DataFrame(AEP_data.to_list()))