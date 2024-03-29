import abc
import datetime
from datetime import date
import json 
from decision_making.buy_sell import buy_sell,buy_sell_reset,buy_sell_isavaliable
from decision_making.buy_sell_rlt import buy_sell_rlt,buy_sell_rlt_reset,buy_sell_rlt_isavaliable
from decision_making.buy_sell_stop import buy_sell_stop,buy_sell_stop_reset,buy_sell_stop_isavaliable
from decision_making.buy_sell_rlt_stop import buy_sell_rlt_stop,buy_sell_rlt_stop_reset,buy_sell_rlt_stop_isavaliable
from datetime import timedelta

from myapp.models.users import Strategy,Strategy_type,Strategies_Grades,Trades,Daily_metric,Total_metric,db
db.create_all()
from sqlalchemy import and_
# HERE IMPORT STRATEGY FEATURES TABLE FROM CELERY TASK
from celery_task import price_data,Strategy_features
# from background_jobs.celery_task import price_data,Strategy_features

from datetime import datetime
import time


class StrategyDAO():
    
    def saveStrategy(self,s,End_time,Start_time,strategy_id  ): 
    
        sc = {
            "buying_angle":s.startegy_values[0] ,
            "selling_angle":  s.startegy_values[1],
            "optimization":s.startegy_values[2],
            "relative_angle": s.startegy_values[3],
            "stop_order":  s.startegy_values[4],
            "less_than_buy": s.startegy_values[5]
        }
  
        print ('score',sc)
        
        data  = json.dumps(sc)
        score = json.loads(data)

       
        print ('SAVED STRATEY',score)
 
        Created_at = time.strftime("%a, %d %b %Y %H:%M:%S")

        '''if sc["optimization"]=="None":
            Opti = "No"
        elif sc["stop_order"]=="None":
            Opti = "No"'''
        
        if sc["optimization"]=="None" and  sc["stop_order"]=="None":
            Opti = "Not_applied"

        elif sc["optimization"]!="None":
            Opti = "relative_angle"

        elif sc["stop_order"]!="None":
            Opti = "stop_order"

        
        # if not stored that strategy than store it.

        # saving into the startegy table 

        db_get = Strategy.query.filter(and_(  Strategy.Symbol=='TVIX', Strategy.strategy_id == strategy_id)).first()
            
        if db_get != None:

            res = Strategy.query.filter_by(strategy_id=strategy_id).update(dict(Created_at = Created_at, Start_time= Start_time, End_time =  End_time))
            db.session.commit()


        else:
            db_data = Strategy(strategy_id = strategy_id ,Strategy_type_id = 'SMA', Symbol = 'TVIX',Created_at = Created_at, Params = score, Start_time= Start_time, End_time =  End_time,Optimization=Opti,isFavourite = False)
            db.session.add(db_data)
            db.session.commit()



    def updateStrategy(self,MStrategy,params):
       
        Symbol = 'TVIX'
        Applied  = True 
        Created_at = time.strftime("%a, %d %b %Y %H:%M:%S") 
        db_data = Strategies_Grades(Strategy_type_id = 'SMA' ,Created_at =  Created_at,isFavourite = True, Params = params)
        db.session.add(db_data)
        db.session.commit()


    def insertTrade(self,Trade):
        pass


class StrategyProcessor(object):

    def __init__(self):
        self.type = None
        self.price = None 
        self.generatedAt = None 

    __metaclass__ = abc.ABCMeta
    @abc.abstractmethod
    def applyStrategy(self,s,start,end):
        pass


class SMAStrategyProcessor(StrategyProcessor):

    start_date = None
    end_date = None
    St = None


    def applyStrategy(self,s,end,start,strategy_id):

        
        print ('ENETERED APPLY STRATEGY')

        def apply(s,end,start,strategy_id):

            # Get the data from Strategy_Features table
            db_data = Strategy_features.query.with_entities(Strategy_features.Feature).all()
        
            print ('length_of_angle',len(db_data))
    
            # fetched_data = db_data.count()
            fetched_data = len(db_data)
    
            # STOCK_DATA STORES THE MARKET DATA ALONG WITH THE ANGLE INFOMATION 
            stock_data = []

            # Adding 9 hours 30 minutes to the start
            '''market_start = start + 32400000 + (600000*3)
            # Adding 16 hours to the start
            market_end = start + 57600000
            # market end time
            end_trade = market_end - 600000'''

            market_start = start + 68400000
            # Adding 16 hours to the start
            market_end = start + 90000000
            # market end time
            end_trade = market_end - 600000


            print('=========== ACTUAL START AND END DATES ==========', start , end)
            
            print('========== NEW DATES =======',market_start,market_end ,end_trade )

            
            for i in range(0,fetched_data):

                a =  db_data[i].Feature

                Time_stamp = a["Time_stamp"]
                Opening = a["Open"]
                High = a["High"]
                Low = a["Low"]
                close = a["Close"]
                Volume = a["Volume"]
                Angle = a["Angle"]

                if Time_stamp >= market_start  and Time_stamp <= market_end:

                    stock_data.append([Time_stamp,Opening,High,Low,close,Volume,Angle])

            print('STOCK_DATA',stock_data)

            print (start,end)
       
            sc = {
                "buying_angle":s.startegy_values[0] ,
                "selling_angle":  s.startegy_values[1],
                "optimization":s.startegy_values[2],
                "relative_angle": s.startegy_values[3],
                "stop_order":  s.startegy_values[4],
                "less_than_buy": s.startegy_values[5]
            }
 
            print ('score',sc)
        
            data  = json.dumps(sc)
            stgy = json.loads(data)

            start_date = start
            end_date = end
            St = stgy
            current_strategy = stgy

            print(current_strategy)

            #GLOBAL VARIABLES
            buy_price = 0
            sell_price = 0
            buy_value = 0
            sell_value = 0
            profit_loss = 0
            profit_loss_percentage = 0
            buy_angle = 0
            Sell_angle = 0
            Symbol = 'TVIX'
            Type = 'SMA'
            buy_time = 0
            Sell_time = 0
            Opmz = 0
            Day_identifier = 0
            decision = 0


            # iterate over the lenth of candles
            for i in range(0,len(stock_data)):

                print ('=========== STOCK_DATA LENGTH============',len(stock_data) )

                market_data = stock_data[i]
                time = market_data[0]
                price = market_data[4]
                angle = market_data[6]
                low_price = market_data[3]
                
                if angle == 'angle calculation is not possible':
                    pass
                else: 

                    if time < end_trade :

                        if current_strategy["optimization"] == 'None' and current_strategy["stop_order"] == 'None':
                            decision = buy_sell(current_strategy["buying_angle"],current_strategy["selling_angle"],angle)
                            print('I AM CALLING 1')
                            Opti = "No"
            
                        elif current_strategy["stop_order"] == 'None':
                            decision = buy_sell_rlt(current_strategy["buying_angle"],current_strategy["selling_angle"],current_strategy["relative_angle"],angle)
                            Opti = "Yes"
                        elif current_strategy["optimization"] == 'None':
                            print('$$$$$BUY_SELL_STOP_ORDER CALLED')
                            decision = buy_sell_stop(current_strategy["buying_angle"],current_strategy["selling_angle"],angle,buy_price,low_price ,current_strategy["less_than_buy"])
                            Opti = "Yes"
                        else:
                            decision = buy_sell_rlt_stop(current_strategy["buying_angle"],current_strategy["selling_angle"],current_strategy["relative_angle"],angle,buy_price,low_price ,current_strategy["less_than_buy"])
                            Opti = "Yes"

                        print (time,angle,decision)


                        if decision == 1:
                            # update the global buy_price,buy_value,buying_angle,buy_time varaibles
                            buy_price = price 
                            buy_angle = angle
                            buy_value = buy_price * 1400
                            buy_time = time
                    
                        elif decision == 2:
                    
                            # update the global sell_price,sell_value,selling_angle,sell_time
                            # Give same day identifier if the trade happend in the same day 

                            sell_price = price 
                            print (price)
                            sell_value = sell_price * 1400
                            sell_angle = angle
                            sell_time = time
                            profit_loss = -(buy_value - sell_value)
                            profit_loss_percentage =((profit_loss/sell_value))*100

                            current_candle_time = time

                            print (sell_price,sell_value,sell_angle,sell_time,profit_loss,profit_loss_percentage)

            
                            date = datetime.fromtimestamp( start/1000.0)
                            Day_identifier = date.strftime('%Y-%m-%d')

                        
                            # ENTERING THE VALUES INTO THE TRADES TABLE
                            print('I AM ENTERING IT TO DATABASE')

                            data_into_db = Trades(strategy_id = strategy_id,buy_price = buy_price,sell_price = sell_price,buy_value = buy_value, sell_value = sell_value ,
                                    profit_loss = profit_loss  , profit_loss_percentage =  profit_loss_percentage ,buy_angle = buy_angle,Sell_angle = sell_angle ,Symbol = 'TVIX',
                                    Type = 'SMA',buy_time = buy_time, Sell_time = sell_time ,Optimization = Opti ,Day_identifier = Day_identifier,Strategy = current_strategy)
                    
                            db.session.add(data_into_db)
                            db.session.commit()
    
                        else:
                            pass 
                    
                    else:
                        
                        print ('========================= EXCUTING THE ELSE OF STRATEGY APPLY STRATEGY  ===========================')
                        
                        if current_strategy["optimization"] == 'None' and current_strategy["stop_order"] == 'None':
                            avaibility = buy_sell_isavaliable()
                            print('I AM CALLING 1 FOR AVAILABILTY')
                        elif current_strategy["stop_order"] == 'None':
                            avaibility = buy_sell_rlt_isavaliable()
                           
                        elif current_strategy["optimization"] == 'None':
                            avaibility = buy_sell_stop_isavaliable()     
                        else:
                            avaibility = buy_sell_rlt_stop_isavaliable()
                        
                        print('============= AVAIBILITY   ====================', avaibility )

                        if avaibility == 1:

                            buy_price = buy_price 
                            buy_angle =  buy_angle 
                            buy_value = buy_price * 1400
                            buy_time = buy_time
                            sell_price = price 
                            sell_value = sell_price * 1400
                            sell_angle = angle
                            sell_time = time
                            profit_loss = -(buy_value - sell_value)
                            profit_loss_percentage =((profit_loss/sell_value))*100
                            
                            current_candle_time = time

                            # date = datetime.fromtimestamp(current_candle_time/1000.0)
                            date = datetime.fromtimestamp(current_candle_time/1000.0)
                            Day_identifier = date.strftime('%Y-%m-%d')
                            
                            # for reseting decision making algorithms
                            print ('=============== CALLING RESET    =======================')
                        
                            if current_strategy["optimization"] == 'None' and current_strategy["stop_order"] == 'None':
                                buy_sell_reset()
                                print ('I AM CALLING 1 FOR RESET')
                                Opti = "No"
            
                            elif current_strategy["stop_order"] == 'None':
                                buy_sell_rlt_reset()
                                Opti = "Yes"
                            elif current_strategy["optimization"] == 'None':
                                buy_sell_stop_reset()
                                Opti = "Yes"
                            else:
                                buy_sell_rlt_stop_reset()
                                Opti = "Yes"


                            data_into_db = Trades(strategy_id = strategy_id,buy_price = buy_price,sell_price = sell_price,buy_value = buy_value, sell_value = sell_value ,
                                    profit_loss = profit_loss  , profit_loss_percentage =  profit_loss_percentage ,buy_angle = buy_angle,Sell_angle = sell_angle ,Symbol = 'TVIX',
                                    Type = 'SMA',buy_time = buy_time, Sell_time = sell_time ,Optimization = Opti ,Day_identifier = Day_identifier,Strategy = current_strategy)
                    
                            db.session.add(data_into_db)
                            db.session.commit()

                            print('============== INSERTED INTO DATABASE ==========================')
                        
                        
                        print ('========== avalibity not found i am restig it  ===========')
                    
                        if current_strategy["optimization"] == 'None' and current_strategy["stop_order"] == 'None':
                            buy_sell_reset()
                            print ('======== DECISION IS NOT EQUAL TO 1 I CALLED 1 FOR RESET ===== ')
                        elif current_strategy["stop_order"] == 'None':
                            buy_sell_rlt_reset()
                        elif current_strategy["optimization"] == 'None':
                            buy_sell_stop_reset()      
                        else:
                            buy_sell_rlt_stop_reset()
                            
                        
                        print('=========I AM BREAKING THE LOOP FOR THE DAY  ========')
                        break
                       


        print('Excuting apply strategy')
        global start_date,end_date,Strategy 

        print (' **********STRATEGY APPLYING BETWEEN**********', start,end)

        r_start = datetime.fromtimestamp(start/1000)
        r_start = r_start.replace(hour=0,minute=0,second=0)

        r_end = datetime.fromtimestamp(end/1000)
        r_end = r_end.replace(hour=0,minute=0,second=0)

        r_start_milliseconds = time.mktime(r_start.timetuple())*1000
        r_end_milliseconds = time.mktime(r_end.timetuple())*1000
        
        print('r_start_milliseconds',r_start_milliseconds)
        print('r_end_milliseconds',r_end_milliseconds)


        while (r_start_milliseconds <= r_end_milliseconds):

            print(r_start_milliseconds,r_end_milliseconds)

            r_eod = r_start_milliseconds + 24*60*60*1000

            print('r_eod',r_eod)
            print('r_start_milliseconds',r_start_milliseconds)

            date_str = str(r_start)

            db_get = Daily_metric.query.filter(and_( Daily_metric.Day_identifier == date_str , Daily_metric.Symbol=='TVIX',  Daily_metric.strategy_id == strategy_id)).first()
            
            print('db_get in the apply strategy', db_get)
            
            if db_get != None:

                print('skiping it fir ',r_start_milliseconds,r_eod )
   
            else:
                print('calling apply for the day', r_start_milliseconds,r_eod)
                
                apply(s,r_eod,r_start_milliseconds,strategy_id)
       
              
             
            r_start_milliseconds = r_start_milliseconds + 24*60*60*1000
            r_start = datetime.fromtimestamp(r_start_milliseconds/1000)
            r_start = r_start.replace(hour=0,minute=0,second=0)
        
        
        print ('existing applystrategy')
        

class Trade():

    def __init__(self,Type,price,at,post):
        self.type = Type
        self.price = price 
        self.at = at
        self.post = post
    
    def __new__(cls):
        return [Type,price,at,post]


class Signal():

    def __init__(self,Type,price,generatedAt):
        self.Type = Type
        self.price = price 
        self.generatedAt = generatedAt

    def __new__(cls):
        return [Type,price,generatedAt]



class Broker():

    def __init__(self,Type,price,generatedAt):
        self.Type = Type
        self.price = price 
        self.generatedAt = generatedAt

    def __new__(cls):
        return [Type,price,generatedAt]



# METRIC CALCULATION FOR EACH STRATEGY 
class Metric(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def forEachTrade(self,t):
        pass

    @abc.abstractmethod
    def getMetric():
        pass

    @abc.abstractmethod
    def getFormattedMetricLabel():
        pass



class MetricImpl(Metric):

    '''def __init__(self,name,date,strategy,metric):
        self.name = None
        self.date = None 
        self.strategy = None'''

    def forEachTrade(self,t):
        pass

    def getFormattedMetricLabel():
        pass



    def getMetric(self,endtime,starttime,s,strategy_id):

        def myFunction(milliseconds):

            date = datetime.fromtimestamp(milliseconds/1000.0)
            startday = date.strftime('%Y-%m-%d')
            datee = datetime.strptime(startday, "%Y-%m-%d")
            a = datee.year 
            b =  datee.month
            c =  datee.day
            return a,b,c 

        a,b,c = myFunction(starttime)
        start_date = date(a, b, c)
        a,b,c = myFunction(endtime)
        
        end_date = date(a, b, c + 1)
        
        print(start_date,end_date)

        def daterange(start_date, end_date):
            for n in range(int ((end_date - start_date).days)):
                yield start_date + timedelta(n)
        
        # get each day between starttime and endtime
        for single_date in daterange(start_date, end_date):
            
            required_day = single_date.strftime("%Y-%m-%d") 

            d = datetime.strptime(str(single_date), "%Y-%m-%d").strftime('%s')
            d_in_ms = int(d)*1000

            required_for = datetime.fromtimestamp(d_in_ms/1000)
            required_for = required_for.replace(hour=0,minute=0,second=0)

            print('required_day',required_day)
            print('required_for',required_for)
        

            # Filter the database based on Day_identifier 
            db_data = Trades.query.filter(and_(Trades.Day_identifier == required_day,Trades.Symbol=='TVIX',Trades.strategy_id == strategy_id))
          
            fetchdata_length = db_data.count()
           
            print (fetchdata_length)
        
            # a ARRAY HOLDS BOTH PORFITS/LOSSES 
            a = []

            for i in range(0,fetchdata_length):
                element = db_data[i].profit_loss
                a.append(element)

            Total_trades = len(a)

            # SEPEARTING WINING TRADES AND LOSING TRADES
            Winning_Trades = []
            losing_Trades = []
            for i in range(0,Total_trades):
                if a[i] > 0:
                    Winning_Trades.append(a[i])
                else:
                    losing_Trades.append(a[i])

            print ('Winning_Trades , losing_Trades',losing_Trades,Winning_Trades)

            Winning_Trades_sum = sum(Winning_Trades) 
            print ('Winning_Trades_sum', Winning_Trades_sum)
            losing_Trades_sum = sum(losing_Trades)
            print ('losing_Trades_sum',losing_Trades_sum)

            Profit = Winning_Trades_sum - (-losing_Trades_sum)
           
            print ('PROFIT',Profit )

            print ('length_winning_trades,total_trades',len(Winning_Trades),Total_trades)
            Winning_Trades_length = len(Winning_Trades)

            if Winning_Trades_sum !=0 and losing_Trades_sum !=0:
                Profit_Factor = (Winning_Trades_sum / losing_Trades_sum)*-1
                print ('length_winning_trades,total_trades',len(Winning_Trades),Total_trades)
                Profitable = float(Winning_Trades_length) / Total_trades
            else:
                Profit_Factor = 0
                Profitable = 0
            
            print ('PROFIT_FACTOR',Profit_Factor)

            print ('Profitable',Profitable)

            sc = {
                "buying_angle":s.startegy_values[0] ,
                "selling_angle":  s.startegy_values[1],
                "optimization":s.startegy_values[2],
                "relative_angle": s.startegy_values[3],
                "stop_order":  s.startegy_values[4],
                "less_than_buy": s.startegy_values[5]
            }
 
            print ('score',sc)
        
            data  = json.dumps(sc)
            stgy = json.loads(data)
        
            Strategy = stgy

            # check if it is already there 

            db_get = Daily_metric.query.filter(and_( Daily_metric.Symbol=='TVIX', Daily_metric.Day_identifier == required_for, Daily_metric.strategy_id == strategy_id)).first()
            
            if db_get != None:

                res = Daily_metric.query.filter(and_(Daily_metric.strategy_id==strategy_id,Daily_metric.Day_identifier==required_for)).update(dict(Total_Profit = Profit,Profit_Factor = Profit_Factor, Profitable = Profitable))
                db.session.commit()

            else:

                # Enter these values into the daily trade metrics 
                data_to_db = Daily_metric( strategy_id = strategy_id, Strategy =  Strategy,Symbol = 'TVIX',
                Total_Profit =  Profit ,Profit_Factor = Profit_Factor, Profitable = Profitable ,Max_Drawdown = None ,Type = 'SMA', Day_identifier = required_day )
            
                db.session.add(data_to_db)
                db.session.commit()
       



    def Tot_met(self,endtime,starttime,s,strategy_id):

        def myFunction(milliseconds):
            date = datetime.fromtimestamp(milliseconds/1000.0)
            startday = date.strftime('%Y-%m-%d')
            datee = datetime.strptime(startday, "%Y-%m-%d")
            a = datee.year 
            b =  datee.month
            c =  datee.day
            return a,b,c 

        a,b,c = myFunction(starttime)
        start_date = date(a, b, c)
        a,b,c = myFunction(endtime)
        end_date = date(a, b, c +1 )

       
        st_da= str(start_date) 
        e_da = str(end_date)



        Tweenty_days_trades = Trades.query.filter(and_(Trades.Day_identifier.between(st_da,e_da),Trades.Symbol=='TVIX',Trades.strategy_id == strategy_id))
        
        print (Tweenty_days_trades.count())

        print ('------------------------------------SUCCESS----------------------------------')

        print (Tweenty_days_trades.count())

        fetchdata_length =  Tweenty_days_trades.count()

        print (fetchdata_length)

        WIINING_TRADES = []
        LOOSING_TRADES = []
        Total_Trades = []
        
        for t in range(0,fetchdata_length):
            element =  Tweenty_days_trades[t].profit_loss
            Total_Trades.append(element)

        Total_Trades_len = len(Total_Trades)

        Profit = 0
        Profit_Factor = 0
        Profitable = 0

        for i in range(0,Total_Trades_len):
            if Total_Trades[i] > 0:
                WIINING_TRADES.append(Total_Trades[i])
            else:
                LOOSING_TRADES.append(Total_Trades[i])
            
            WIINING_TRADES_SUM = sum(WIINING_TRADES) 
            LOOSING_TRADES_SUM = sum(LOOSING_TRADES)

            # print WIINING_TRADES_SUM,LOOSING_TRADES_SUM

            Profit = WIINING_TRADES_SUM - (-LOOSING_TRADES_SUM)

            Profit_Factor = None
            Profitable = None

            WIINING_TRADES_LENGTH = len(WIINING_TRADES ) 

            if WIINING_TRADES_SUM != 0 and LOOSING_TRADES_SUM !=0:

                Profit_Factor = (WIINING_TRADES_SUM  / LOOSING_TRADES_SUM)*-1 
                Profitable =  float(WIINING_TRADES_LENGTH) / Total_Trades_len
                
            else:
                WIINING_TRADES_SUM == 0 or LOOSING_TRADES_SUM == 0 
                print ('CALCULATION OF PROFIT_FACTOR AND PROFITABLE IS NOT POSSIBLE')
                Profit_Factor = 0
                Profitable = 0
        

        sc = {
            "buying_angle":s.startegy_values[0] ,
            "selling_angle":  s.startegy_values[1],
            "optimization":s.startegy_values[2],
            "relative_angle": s.startegy_values[3],
            "stop_order":  s.startegy_values[4],
            "less_than_buy": s.startegy_values[5]
        }
 
        print ('score',sc)
        
        data  = json.dumps(sc)
        stgy = json.loads(data)
        
        Strategy = stgy
        # Enter these values into the total_metric table


        db_get = Total_metric.query.filter(and_(  Total_metric.Symbol=='TVIX',  Total_metric.strategy_id == strategy_id)).first()
            
        if db_get != None:

            res = Total_metric.query.filter_by(strategy_id=strategy_id).update(dict(Total_Profit = Profit,Profit_Factor = Profit_Factor, Profitable = Profitable,Start_Date = starttime,End_Date = endtime))
            db.session.commit()

        else:

            data_to_db = Total_metric( Strategy = Strategy,Symbol = 'TVIX',  strategy_id = strategy_id, Total_Profit =  Profit ,Profit_Factor =  Profit_Factor, Profitable = Profitable ,Max_Drawdown = None,Start_Date = starttime,End_Date = endtime )
            db.session.add(data_to_db)
            db.session.commit()

            print ('------------------------DONE --------------------------------------')