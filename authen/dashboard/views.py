from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import (
    AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm,
)
from django.contrib.auth.decorators import login_required
from dashboard.forms import TestForm
from dashboard.forms import StockForm
from dashboard.models import TestBo
from datetime import datetime
from .waveline import authenticaiton
from .waveline import draw_line
import json
import pika

  

def authen_login(request):
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                try:
                    next = request.GET['next']
                except:
                    next = '/authen/stock/'
                return HttpResponseRedirect('%s' % next)
            else:
                form = AuthenticationForm(request.POST)
                return render(request, 'authen/login.html', {'forms':form, 'error':'User is not permit to login'})
        else:
            form = AuthenticationForm(request.POST)
            return render(request, 'authen/login.html', {'forms':form, 'error':'Invalid user of password'})

    form = AuthenticationForm()
    return render(request, 'authen/login.html', {'forms':form})

@login_required(login_url = '/authen/login/')
def index(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = StockForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            value = request.POST['stock_name']
            print(request.POST)
            dic = {'stock':value, 'days':int(request.POST['days']), 'choice':request.POST['choice']}
            dic_json = json.dumps(dic)
            send_message(dic_json)
            wait_message()
            global file_name
            print(' [*] back to view %s' % file_name)
            return render(request, 'authen/stock_index.html', {'form': form, 'image':file_name})
        else:
            print('This is not valid')
    # if a GET (or any other method) we'll create a blank form
    else:
        form = StockForm()
    #print('I am in handle stock')
    return render(request, 'authen/stock_index.html', {'form': form})


def handle_post(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = TestForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            
            bo = TestBo()
            bo.save()
            return HttpResponseRedirect('/admin/')
        else:
            print('This is not valid')
    # if a GET (or any other method) we'll create a blank form
    else:
        form = TestForm()

    return render(request, 'authen/test_form.html', {'form': form})


def send_message(message):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='client_server')

    channel.basic_publish(exchange='',
                        routing_key='client_server',
                        body=message)
    print(" [x] Sent Message:%s" % message)
    connection.close()

file_name = ''

def callback(ch, method, properties, body):
    print(' [*] Receive message %s' % body)
    ch.basic_ack(delivery_tag = method.delivery_tag)
    global file_name
    
    file_name = body.decode('utf-8')
    ch.basic_cancel(method.consumer_tag)
    print(' [*] Done')

def wait_message():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='server_client')
    channel.basic_consume(callback,
                          queue='server_client')
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/authen/login/')

@login_required(login_url = '/authen/login/')
def handle_stock(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = StockForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            value = request.POST['stock_name']
            print(request.POST)
            dic = {'stock':value, 'days':int(request.POST['days']), 'choice':request.POST['choice']}
            dic_json = json.dumps(dic)
            send_message(dic_json)
            wait_message()
            global file_name
            print(' [*] back to view %s' % file_name)
            return render(request, 'authen/stock.html', {'form': form, 'image':file_name})
        else:
            print('This is not valid')
    # if a GET (or any other method) we'll create a blank form
    else:
        form = StockForm()
    print('I am in handle stock')
    return render(request, 'authen/stock.html', {'form': form})


from pandas import Series, DataFrame
from sqlalchemy import create_engine
from sqlalchemy import DATETIME
import mysql.connector
import pandas as pd
from django.utils.safestring import mark_safe

class OutputData():
    def __init__(self, data):
        self.data = data

    def output(self):
        buff_list = []
        df = self.data
        for i in range(len(df)):
            index = df.index[i]
            buf_list = ["{",
                        'date:"%s",'%index.date(),
                        'open:"%s",'%df.open[index], 
                        'high:"%s",'%df.high[index],
                        'low:"%s",'%df.low[index],
                        'close:"%s",'%df.close[index],
                        "},"]
            buf = '\n'.join(buf_list)
            buff_list.append(buf)
        buf = '\n'.join(buff_list)
        # have to use mark_safe, otherwise \n will be translate. 
        return mark_safe(buf)


class EventFormat():
    def __init__(self, date, description):
        self.date = date
        self.description = description
    
    def date(self):
        date_list = self.date.split('-')
        output = ','.join(date_list)
        return mark_safe(output)

    def description(self):
        return mark_safe(self.description)

from .data_engine import read_price_data, read_finance_data


def verify_datetime(date):
    try:
        dt = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return None
    return dt

class OutputFinancialData():
    def __init__(self, data, target):
        self.target = target
        self.data = data

    def output(self):
        buff_list = []
        df = self.data
        for i in range(len(df)):
            index = df.index[i]

            if self.target == 'pe_ratio':
                buf_list = ["{",
                            'date:"%s",'%index.date(),
                            'value:"%s",'%df.pe_ratio[index], 
                            'volume:"%s",'% '0',
                            "},"]
            else:
                buf_list = ["{",
                            'date:"%s",'%index.date(),
                            'value:"%s",'%df.pb_ratio[index], 
                            'volume:"%s",'% '0',
                            "},"]

            buf = '\n'.join(buf_list)
            buff_list.append(buf)
        buf = '\n'.join(buff_list)
        # have to use mark_safe, otherwise \n will be translate. 
        return mark_safe(buf)

def financial_date(request):
    if request.method == "POST":
        stock_name = request.POST['stock_name']
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        print('debug start_date = %s end_date = %s'%(start_date, end_date))
        if request.POST['choice'] == 'PB':
            choice = 'pb_ratio'
        else:
            choice = 'pe_ratio'
    
        df = read_finance_data(stock_name, choice, start_date, end_date)
        
        if df is not None:
            df2 = df.sort_values(by=choice, ascending=True)
            try:
                end_date = str(df.index[-1].date())
                print('Debug ', end_date)
                position = df2.index.get_loc(end_date)
                print(position)
            except:
                print('Debug position has problem!')
                return render(request, 'authen/financial_data.html')

            his_pos = round(position/len(df2), 2)
            description = "History position rate at %s" % his_pos
            tool = OutputFinancialData(df, choice)
            event = EventFormat(end_date, description)
            return render(request, 'authen/financial_data.html', {'tool':tool, 'title_name': request.POST['choice'], 'event':event})
    
    return render(request, 'authen/financial_data.html')

def candle_stock(request):
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        stock_name = request.POST['stock_name']
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']

        start_date = verify_datetime(start_date)
        end_date = verify_datetime(end_date)

        error = ''
        # juduge whether date is correct
        if start_date is None or end_date is None:
            error = 'Please input correct start date and end date!'
            return render(request, 'authen/stock_data.html', {'error':error})

        if end_date < start_date:
            error = "End Date should be latest than Start Date!"
            return render(request, 'authen/stock_data.html', {'error':error})
        
        #judge stock name's format
        if len(stock_name) != 6:
            error = 'Stock code is not correct!'
        else:
            try:
                stock_name = int(stock_name)
            except:
                error = 'stock code must be number!'
        if len(error) > 0:
            return render(request, 'authen/stock_data.html', {'error':error})

        df = read_price_data(stock_name, str(start_date.date()), str(end_date.date()))
        
        if df is None:
            return render(request, 'authen/stock_data.html')

        tool = OutputData(df)
        return render(request, 'authen/stock_data.html', {'tool': tool, 'title':'601318'})
    
    return render(request, 'authen/stock_data.html', {'title':'None'})