import pandas as pd
import numpy as np
from wse_extract import WSE_extract

class AEP_calc:
    """Class which handles finding the maximum WSE corresponding to given AEP values for each grid
    cell in a wse_extract object

    To Do: Update code to perform proper exponentiation of the data
    check to make sure the weight_file has the same number of storms as wse_extract
    check to make sure the weight_file is formated right
    """

    def __init__(
            self,
            wse_extract: WSE_extract,
            aep: list,
            weight_file: str
    ):
        """
        Constructor for the aep_calc object

        Args:
            wse_extract: a wse_extract object containing
            aep: a list containing AEP values to be extracted
            weight_file: a .csv file containing the weight for each storm object
        """
        self.__wse_data = wse_extract.extract()
        self.__aep = aep
        self.__weights = pd.read_csv(weight_file, header=0)
    

    
    def __get_AEP_value(self, data) -> list[np.float64]:
        """Helper method for process_location_aep
        takes data created by combining a grid cells max WSE values for each storm
        and cdf values and compares them to AEP values to caluclate the max WSE that correpsonds
        to each AEP

        Returns:
            A list of np.float64 of max WSE values the same length as the AEP value list
        """
        exceedance_values = []
        for p in self.__aep:
            if(p>max(data['cdf'])):
                exceedance_values.append(max(data['wse']))
            else:
                above = data[data.cdf>=p]
                exceedance_values.append(above['wse'].iloc[0])
        return exceedance_values
    
    def __exponentiate(self, data) -> list[np.float64]:
        """Currently does nothing, but should perform a transformation on the CDF values created in
        process_location_AEP in order to account for multiple storms
        """
        return data
    
    def __process_location_AEP(self, data) -> list[np.float64]:
        """Takes a row from a wse_extract object and joins it in a pd.Dataframe with
        the storm weight object, then sorts the pd.Dataframe by the maximum WSE values
        and creates a cumulative cdf for a single storm, this object is passed to the 
        exponentiate function to create a cdf column accounting for multiple storms
        finally this object is passed to the get_AEP value to return the maximum WSE values
        corresponding to AEPs

        Returns:
            A list of np.float64 of max WSE values the same length as the AEP value list
        """
        point_data = self.__weights
        point_data['wse'] = data.tolist()
        point_data.sort_values(by=['wse'], inplace=True)
        point_data['cdf_single_storm'] = np.cumsum(point_data['P'])
        point_data['cdf'] = self.__exponentiate(point_data['cdf_single_storm'].to_list())
        return self.__get_AEP_value(point_data)
    
    def return_AEP(self) -> list:
        """Applies the process location AEP function to each row of wse_extract data frame

        Returns:
            a pd.DataFrame with columns being AEP values and rows being geometry grid celss
        """
        print("Getting AEP")
        AEP_data = self.__wse_data.apply(self.__process_location_AEP, axis=1)
        
        return(pd.DataFrame(AEP_data.to_list()))