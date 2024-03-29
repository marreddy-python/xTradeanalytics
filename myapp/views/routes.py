from flask import Blueprint, request,render_template,redirect, url_for,session,logging,flash,session,json,jsonify,flash
import sys
sys.dont_write_bytecode = True

from myapp.controllers.interface import StrategyController,Strategy,DataController
from myapp.controllers.decides_start_end import myFunction
from myapp.controllers.add_favourite import addFav,deletestrategy
from myapp.controllers.check_strategyapplied import applied_or_not,strategy_savedornot,get_strategy_id,get_lastsaved_strategy,get_strategyinfo
from myapp.controllers.check_strategyapplied import from_total_metric
from myapp.controllers.strategydao import MetricImpl

modulo1_blueprint = Blueprint(name='modulo1', import_name=__name__,template_folder='templates',
static_folder='static', static_url_path='/login,/trades.svg,/infile.json')

# from celery_task import generate_trades
# generate_trades()

from myapp.models.users import Post,db

import time

#LOGIN PAGE
@modulo1_blueprint.route('/', methods=['GET','POST'])
@modulo1_blueprint.route('/login', methods=['GET','POST'])
def login():
       
        if request.method == "POST":

                uname = request.form["uname"]
                passw = request.form["passw"]
        
                login = Post.query.filter_by(username=uname, password=passw).first()

                if login is not None:
                        print (uname)
                        session['username'] = uname
                        flash('Logged in successfully.')
                        return redirect(url_for("modulo1.strategyview"))
            
        
        return render_template("login.html")


#REGISTRATION PAGE
@modulo1_blueprint.route('/register', methods=['GET','POST'])
def register():

        if request.method == "POST":
                uname = request.form['uname']
                mail = request.form['mail']
                passw = request.form['passw']
                register = Post(username = uname, email = mail, password = passw)
                db.session.add(register)
                db.session.commit()
       
                return redirect(url_for("modulo1.login"))
                
        return render_template("register.html")



@modulo1_blueprint.route('/logout', methods=['GET','POST'])
def logout():
    return redirect(url_for('modulo1.login'))



start_time = None 
end_time = None
St = None
Trades_singleday = None
Metric_values_singleday = None
Performance = None
Buy_flags = None
Sell_flags = None
Stratey_values = None


@modulo1_blueprint.route('/strategyview', methods=['GET','POST'])
def strategyview():

        global start_time,end_time,St, Performance,Metric_values_singleday,Trades_singleday,Buy_flags,Sell_flags,Stratey_values

        Data_loader = DataController()
       
        # end_time = int(round(time.time() * 1000))
        
        #MYFUNCTION WILL DECIDE THE START TIME AND END TIME FOR THE CHART 
        start_time,end_time = myFunction()
       
        print (start_time,end_time)



        # daily_data = Data_loader.MarketData(start_time,end_time)
        tweenty_days = end_time - (86400000*10)
        print('@@@@@@',tweenty_days,end_time)
        # daily_data = Data_loader.MarketData(start_time,end_time)
        daily_data = Data_loader.MarketData(tweenty_days,end_time)
        # print daily_data


        if request.method == "POST":  

                Buying_angle = int(request.form.get('Buying_angle')) 
                selling_angle = int(request.form.get('selling_angle'))
                optimization = str(request.form.get('Optimization'))
                relative_angle = int(request.form.get('relative_angle'))
                stop_order = str(request.form.get('STPODVALUE'))
                less_than_buy = float(request.form.get('less_than_buy'))
                step_number  = int(request.form.get('step_number'))
                strategy_id  = int(request.form.get('strategy_id'))
                
                print(Buying_angle,selling_angle,optimization,relative_angle,stop_order,less_than_buy)
                
                Stratey_values = [Buying_angle,selling_angle,optimization,relative_angle,stop_order,less_than_buy] 
                
                if selling_angle == '' and Buying_angle == '':
                        print ('--------------------------------FAILED-----------------------------')
                        # FLASH MESSAGE NEEDS TO BE HERE 
                        return jsonify({'Trades_singleday':0,'Metric_values': 0 })
                
                else:
                        # INSTANCE OF STRATEGY CLASS
                        St = Strategy(1,Stratey_values,'NONE')
                        startegy_loader = StrategyController()

                        #After Clicking on save button
                        if request.form.get('main') == 'Save':

                
                                if step_number == 1:
                                        tweenty_days = end_time - (86400000*10)
                                        
                                        if strategy_id == -1:
                                                strategy_id = get_strategy_id(Stratey_values)

                                        b = startegy_loader.applyStrategy('TVIX',St ,end_time,tweenty_days , strategy_id)
                                        Trades_singleday,Buy_flags,Sell_flags = Data_loader.getTrades('TVIX',St,end_time,tweenty_days)
                                        print('step number1 excuting')
                                        return jsonify({'step':1 })       
                                else:   
                                        tweenty_days = end_time - (86400000*10)
                                        if strategy_id == -1:
                                                strategy_id = get_strategy_id(Stratey_values)

                                        startegy_loader.metricCalculation(end_time,tweenty_days,St,strategy_id)
                                        startegy_loader.Total_metricCalculation(end_time,tweenty_days,St,strategy_id)
            
                                        Metric_values_singleday = Data_loader.getPerformance('TVIX',St,start_time,end_time)
                                        b = startegy_loader.saveStrategy(St,end_time,tweenty_days,strategy_id)
                                        Performance = Data_loader.getPerformance('TVIX',St ,end_time,tweenty_days)
                                        print('step number2  excuting')
                                        from_total_metric_values = from_total_metric(strategy_id)
                                       
                                        return jsonify({'Trades_singleday':Trades_singleday,'Metric_values': Metric_values_singleday,'Performance':Performance,'Buy_flags':Buy_flags,'Sell_flags':Sell_flags,'step':2,'from_total_metric':from_total_metric_values })
                             
                                
                        else:
                                return json.dumps({'status':'Failed'})
  

        else:
                
                Data_loader = DataController()
                data,strategy_names = Data_loader.getStrategies()
                print ('data',data )
                print ('Stratey_values',Stratey_values)
                strategy_params = get_lastsaved_strategy()
                
                Stratey_values = strategy_params
              

                if len(strategy_params) == 0:
                        Trades_singleday = None
                        Metric_values_singleday = None
                        Performance = None
                        Buy_flags = None
                        Sell_flags = None


                return render_template("page1.html", Metric_values_singleday = Metric_values_singleday,Trades_singleday = Trades_singleday,Performance = Performance,daily_data = daily_data,Buy_flags = Buy_flags,Sell_flags = Sell_flags,
                strategy_names = strategy_names,Strategy_values = Stratey_values,page='strategyview',strategy_params = json.dumps(strategy_params))




@modulo1_blueprint.route('/Arena', methods=['GET','POST'])
def Arena():  
        Data_loader = DataController()
        data,strategy_names = Data_loader.getStrategies()
        return render_template("page2.html",strategy_names = strategy_names, page = 'Arena')     

         

@modulo1_blueprint.route('/Strategies1', methods=['GET','POST'])
def Strategies1():

        if request.method == "POST": 

                # GET THE ID OF A CLICKED STARTEGY AND ADD TO FAVOURITES
                print ('EXCELLENT ')
                print (request.get_data())
                # adding strategy to favouites
                addFav(request.get_data())
                
                # get the updated strategies 
                Data_loader = DataController()
                data123,strategy_names = Data_loader.getStrategies()
                print (data123)
                return data123
                
        else:
                #HERE LOAD ALL THE STRATEGIES FROM THE STRATEGIES TABLE

                Data_loader = DataController()
                data,strategy_names = Data_loader.getStrategies()
                print (strategy_names,data)

                return render_template("page3.html", data = data ,strategy_names = strategy_names,page = 'Strategies1' )



@modulo1_blueprint.route('/settings', methods=['GET','POST'])
def settings():
    
        if request.method == "POST":

                price_history = request.form.get('Price_history')
                data_grouping_Interval = request.form.get('data_grouping_Interval')
                userinput_dg = request.form.get('userinput_dg')
                userinput_sma = request.form.get('userinput_sma')
                position_size = request.form.get('Position_size')
                arena_size = request.form.get('max_size_arena')

                print (price_history,data_grouping_Interval,userinput_dg,userinput_sma,position_size,arena_size)

                #Save Button
                if request.form.get('main') == 'Save':
                        return json.dumps({'status':'Save'})

                #Cancel button
                if request.form.get('main') == 'Cancel':
                        return json.dumps({'status':'Cancel'})

        else:   
                # HERE LOAD THE SETTINGS FROM THE DATABASE AND PASS IT TO PAGE4 TEMPLATE
                Data_loader = DataController()
                data,strategy_names = Data_loader.getStrategies()
                
                return render_template("page4.html",strategy_names = strategy_names,page = 'settings')
         



@modulo1_blueprint.route('/delete_strategy', methods=['GET','POST'])
def delete_strategy():
        if request.method == "POST":

                print (request.form.get('clicked_strategy'))

                deletestrategy(request.form.get('clicked_strategy'))

                return json.dumps({'status':'Deleted ssuccesfully'})



@modulo1_blueprint.route('/view_strategy/<username>', methods=['GET','POST'])
def view_strategy(username):
        
        start_time,end_time = myFunction()
       
        print (start_time,end_time)

        # daily_data = Data_loader.MarketData(start_time,end_time)
        tweenty_days = end_time - (86400000*10)
        # daily_data = Data_loader.MarketData(start_time,end_time)
        Data_loader = DataController()
        daily_data = Data_loader.MarketData(tweenty_days,start_time)
        
        Data_loader = DataController()
        data,strategy_names = Data_loader.getStrategies()
        

        Trades_singleday = None
        Metric_values_singleday = None
        Performance = None
        Buy_flags = None
        Sell_flags = None
        # Stratey_values = None


        print (username.encode('ascii','ignore'))
        str_param = type(username.encode('ascii','ignore'))
        ab = int(username,10)

        print (ab)
        print (type(ab))

        strategy_params = get_strategyinfo(ab)
        Stratey_values = strategy_params
        

        return render_template("page1.html", Metric_values_singleday = Metric_values_singleday,Trades_singleday = Trades_singleday,Performance = Performance,daily_data = daily_data,Buy_flags = Buy_flags,Sell_flags = Sell_flags,
        strategy_names = strategy_names,Strategy_values =Stratey_values,page='strategyview', strategy_params = json.dumps(strategy_params) )



