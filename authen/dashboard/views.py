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
    return HttpResponse('Hello World!')


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