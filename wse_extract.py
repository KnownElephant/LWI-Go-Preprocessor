import pandas as pd
import h5py
import numpy as np
import os
from hecras.hecgeometry import HecGeometry
from hecras.flowarea2d import FlowArea2D

class WSE_extract:

    def __init__(
            self,
            flow_area: FlowArea2D,
            directory: str
    ):
        self.__flow_area = flow_area
        self.__directory = directory
        self.__files_list = os.listdir(directory)
    
    
    def extract(self)-> pd.DataFrame:
        print("Extracting for "+self.__flow_area.name())
        wse_data=pd.DataFrame()
        for file in self.__files_list:
            with h5py.File(self.__directory+"/"+file, "r") as f:
                wse = f['Results/Unsteady/Output/Output Blocks/Base Output/Unsteady Time Series/2D Flow Areas/'+self.__flow_area.name()+'/Max Values/Water Surface'][:]
                wse_data[file] = wse
        return wse_data
            

    