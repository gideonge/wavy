import time
import matplotlib.pyplot as plt
from datetime import datetime
import json
import jqdatasdk
#from mpl_finance import candlestick_ohlc
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import numpy as np
import  matplotlib.font_manager as fm
import pika
# -*- coding: UTF-8 -*-
# 画K线图

# def draw_candle_line(stock_name, username, password):
#     stock_name = '000001.XSHE'
#     jqdatasdk.auth(username, password)
#     price = jqdatasdk.get_price(security=stock_name, frequency='1d')
#     # 获取时间序列，并且转化为可以使用的格式
#     time_index = price.index
#     timelist = [mdates.date2num(i.to_pydatetime()) for i in time_index]  # Convert to date struct
#     # 生成candlestick能用的数据格式。这种数据的格式是六元组，time, open, high, low, close, volume。这六元组又由一个tuple组成。
#     data = tuple((timelist[i], price.open[i], price.high[i], price.low[i], price.close[i]) for i in range(len(price)))
#     fig = plt.figure()
#     fig.set_dpi(120)
#     ax1 = plt.subplot2grid((1,1),(0,0))
#     plt.xlabel('Date')
#     plt.ylabel('Price')
#     plt.title('Instrument: 000001.XSHE')
#     candlestick_ohlc(ax1, data, width=0.65, colorup='#77d879', colordown='#db3f3f')
#     ax1.xaxis.set_major_locator(mticker.MaxNLocator(15))
#     ax1.xaxis.set_major_formatter(mdates.DateFormatter('%y-%m-%d'))
#     plt.xticks(rotation=45)
#     plt.savefig('{}.png'.format(stock_name), dpi=120)
#     plt.show()

# 获取百分比
def generate_pct(max_value, min_value, pct):
    return round((max_value - min_value) * pct + min_value, 2)

def draw_diagram(total_fac, name, stock, full_name):
    '''
    total_fac: Data
    name: PE-TTM, PB, etc. 
    stock: Stock Code
    full_name: Stock display name
    '''
    # 解决中文乱码问题
    myfont=fm.FontProperties(fname="C:\Windows\Fonts\STXIHEI.TTF")
    #total_fac
    total_fac.fillna(method="ffill") #remove nan
    fig = plt.figure()
    ax1 = plt.subplot2grid((1,1),(0,0))
    fig.set_dpi(120)
    #fg.set_size_inches(8,6)
    #ax.set_xticks([total_fac.index[0], s1, total_fac.index[-1]])

    # 设置刻度字体大小
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    
    ax1.set_xlabel('Time', fontsize=8)
    ax1.set_ylabel(name, fontsize=8)
        
    line=0.5
    # 处理数据， remote pike
    total_fac[np.abs(total_fac - total_fac.mean())<= (3*total_fac.std())]
    # total_fac.fillna(method="ffill") #remove nan
    # 画PB
    ax1.plot_date(total_fac.index, total_fac.values, '-', color='k', linewidth=line)
    # 画网格
    ax1.grid(True, color='g', linestyle=':', linewidth=0.2)
    # 生成比例值
    max_value = total_fac.max().values[0]
    min_value = total_fac.min().values[0]
    
    min_s_value = min_value
    max_s_value = max_value
      
    ax1.tick_params(which='major', width=1.00)
    ax1.tick_params(which='major', length=5)
    ax1.tick_params(which='minor', width=0.75)
    ax1.tick_params(which='minor', length=2.5)

    ax1.yaxis.set_major_locator(mticker.MaxNLocator(10))
                 
    if max_s_value - min_s_value >= 300:
      ax1.yaxis.set_minor_locator(mticker.MultipleLocator(20))
    elif max_s_value - min_s_value >= 200:
      ax1.yaxis.set_minor_locator(mticker.MultipleLocator(10))
    elif max_s_value - min_s_value > 20:
      ax1.yaxis.set_minor_locator(mticker.MultipleLocator(1))  
    elif max_s_value - min_s_value <= 20:
      ax1.yaxis.set_minor_locator(mticker.MultipleLocator(0.2))  
      
    pct_10 = generate_pct(max_value, min_value, 0.1)
    pct_30 = generate_pct(max_value, min_value, 0.3)
    pct_50 = generate_pct(max_value, min_value, 0.5)
    pct_70 = generate_pct(max_value, min_value, 0.7)
    pct_90 = generate_pct(max_value, min_value, 0.9)
    
    latest_pb = total_fac.values[-1][0]
      
    peak_index = np.argmax(total_fac.values)
    peak_time = total_fac.index[peak_index]
    max_value = total_fac.values[peak_index]

    # 画等比例线
    ax1.axhline(pct_10, color='k', linewidth=0.8, linestyle=':')
    ax1.axhline(pct_30, color='b', linewidth=0.8, linestyle=':')
    ax1.axhline(pct_50, color='c', linewidth=0.8, linestyle=':')
    ax1.axhline(pct_70, color='c', linewidth=0.8, linestyle=':')
    ax1.axhline(pct_90, color='r', linewidth=0.8, linestyle=':')
    
    try:
      ax1.annotate('Peak {}'.format(str(round(max_value[0],2))), (total_fac.index[peak_index], max_value), 
                 (total_fac.index[peak_index+10], max_value), fontsize=7)
    except:
      ax1.annotate('Peak {}'.format(str(round(max_value,2))), (total_fac.index[peak_index], max_value), 
                 (total_fac.index[peak_index - 10], max_value), fontsize=5)
    
    ax1.plot([], [], color='purple', linestyle='-', label='%s'% latest_pb)
    

    # 时间旋转45度
    for label in ax1.xaxis.get_ticklabels():
        label.set_rotation(45)
       
    if type(total_fac).__name__ == 'DataFrame':
      values = np.array([i[0] for i in total_fac.values])
    else:
      values = total_fac
      
    rate_up = len(values[values <= latest_pb]) / len(values)
    ax1.plot([], [], color='purple', label='history rate:{0:.2f}%'.format(rate_up*100))
    
    ax1.fill_between(total_fac.index, values, latest_pb, where=(values > latest_pb), alpha=0.3, facecolors='r')
    ax1.fill_between(total_fac.index, values, latest_pb, where=(values < latest_pb), alpha=0.3, facecolors='g')
    
    ax1.xaxis.set_major_locator(mticker.MaxNLocator(20))
    # 设置背景颜色
    ax1.set_facecolor('w')    
    ax1.legend(loc='best')
    ax1.set_title('{} {} {} - {}'.format(full_name, name, total_fac.index[0], total_fac.index[-1]), fontname='华文细黑',fontproperties=myfont)
    plt.tight_layout()
    #stock_name = instruments(stock, country='cn').symbol
    file_name = '{}_{}({}).png'.format(full_name, name, total_fac.index[-1].date())
    plt.savefig('./static/'+file_name, dpi=240)
    return file_name
    #plt.show()
    #plt.subplots_adjust(wspace=0.05, hspace=0.05)

from datetime import datetime

# 获取连续的PE曲线
def draw_line(stock_name, type, days=600):
    info = jqdatasdk.get_security_info(stock_name)

    if info is None:
      return 'error'
    q = jqdatasdk.query(jqdatasdk.valuation).filter(jqdatasdk.valuation.code == stock_name) 
    now = datetime.now()
    date = '%d-%d-%d' % (now.year, now.month, now.day)
    df = jqdatasdk.get_fundamentals_continuously(q, end_date=date, count=days)

    print(df['pe_ratio'].index)

    if type == 'PE':
      return draw_diagram(df['pe_ratio'], 'PE-TTM', stock_name, info.display_name)
    elif type == 'PB':
      return draw_diagram(df['pb_ratio'], 'PB', stock_name, info.display_name)

def authenticaiton(username, password):
    jqdatasdk.auth(username, password)


config_file = './pass.conf'

def read_account(file_name):
    rf = open(file_name, 'r')
    account = rf.readlines()[0]
    account = account.split()
    name = account[0]
    password = account[1]
    return name,password

def wrap_draw_line(stock, day, choice):
    name,password = read_account(config_file)
    authenticaiton(name, password)
    stock_name = jqdatasdk.normalize_code(stock)
    print(stock_name)
    file_name = draw_line(stock_name, choice, days=day)
    return file_name
 
# receive message and draw picture
def callback(ch, method, properties, body):
    ch.basic_ack(delivery_tag = method.delivery_tag)
    dic = json.loads(body)
    print(' [*] Receive message %s' % body)
    file_name = wrap_draw_line(dic['stock'], dic['days'], dic['choice'])
    send_message(file_name)

# send back ack message
def send_message(message):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='server_client')

    channel.basic_publish(exchange='',
                        routing_key='server_client',
                        body=message)
    print(" [x] Sent Message:%s" % message)
    connection.close()

# start rabbitmq
def kickoff():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='client_server')
    channel.basic_consume(callback,
                          queue='client_server')
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    kickoff()
    #wrap_draw_line('000002', 600, 'PE')


# draw_line('601877.XSHG', 'PE')
# draw_line('601877.XSHG', 'PB')
