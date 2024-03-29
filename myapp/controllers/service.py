import sys
sys.dont_write_bytecode=True
import abc

from factory import get_dd,get_sd,get_smastprsr,get_metric

class iDataService(object):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def getTrades(symbol,Strategy,start,end):
        pass

    @abc.abstractmethod
    def getPerformance(symbol,Strategy,start,end):
        pass
     
    @abc.abstractmethod
    def MarketData(start,end):
        pass

    
    @abc.abstractmethod
    def getStrategies():
        pass


class DataService(iDataService): 
    
    DD = get_dd() 

    def getTrades(self,symbol,Strategy,start,end):
        d = self.DD.getTrades(symbol,Strategy,start,end)
        return d
        
    def getPerformance(self,symbol,Strategy,start,end):
        d = self.DD.getPerformance(symbol,Strategy,start,end)
        return d
        
    def MarketData(self,start,end):
        d = self.DD.MarketData(start,end)
        return d

    def getStrategies(self):
        d = self.DD.getStrategies()
        return d



class iStrategyService(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def saveStrategy(Strategy, Start_time,End_time):
        pass

    @abc.abstractmethod
    def getNewStrategy(list):
        pass
    
    @abc.abstractmethod
    def updateStrategy(Strategy,params):
        pass
    
    @abc.abstractmethod
    def applyStrategy(symbol,Strategy,start,end):
        pass

    @abc.abstractmethod 
    def getProgress():
        pass


class StrategyService(iStrategyService):

    SD = get_sd()
    SMA_SPP = get_smastprsr()
    get_metr = get_metric()

    def saveStrategy(self,Strategy,Start_time,End_time,strategy_id):
        b = self.SD.saveStrategy(Strategy,Start_time,End_time,strategy_id)
        return b 

    def getNewStrategy(list):
        pass

    def updateStrategy(self,Strategy,params):
        b = self.SD.updateStrategy(Strategy,params)
        return b 

    def applyStrategy(self,symbol,Strategy,start,end,strategy_id):
        b = self.SMA_SPP.applyStrategy(Strategy,start,end,strategy_id)
        return b

    def metric_calcgetMetric(self,start_time,tweenty_days,St,strategy_id):
        b = self.get_metr.getMetric(start_time,tweenty_days,St,strategy_id)
        return b 

    def metric_calcTot_met(self,start_time,tweenty_days,St,strategy_id):
        b = self.get_metr.Tot_met(start_time,tweenty_days,St,strategy_id)
        return b
    
    
    def getProgress():
        pass



