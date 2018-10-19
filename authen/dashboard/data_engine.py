from pandas import Series, DataFrame
from sqlalchemy import create_engine
from sqlalchemy import DATETIME
import mysql.connector
import jqdatasdk as jdk
from datetime import datetime
#from datetime import timedelta
import pandas as pd
from . import waveline

'''
A article for python database operation including delete, insert, create, etc. 
https://www.tutorialspoint.com/python/python_database_access.htm
'''

def search_data(database, table, target, start_date, end_date):
    '''
    This routine is used to get a DataFrame from database.
    target is the parameter you want to get back. 
    start_date and end_date is the time span you specify as a criteria 
    '''
    if if_table_exists(database, table) == False:
        return 
    engine = create_engine("mysql+mysqldb://root:"+"@localhost/%s" % database)
    df = pd.read_sql('select day, %s from %s where day > "%s" and day < "%s"' % (target, table, start_date, end_date), 
                    con=engine, index_col='day')
    return df


def if_table_exists(database, table):
    '''
    This routine is used to judge whether specific table exsiting in a database. 
    database: database name
    table: the table name
    '''
    mydb = mysql.connector.connect(host='localhost', user='root', database=database)
    mycursor = mydb.cursor()
    mycursor.execute('show tables')
    tables = mycursor.fetchall()
    tables = [i[0] for i in tables]
    if table in tables:
        return True
    else:
        return False

STOCK_DATABASE = 'stockdata'
STOCK_ID_MAPPING = 'stock_mapping'
STOCK_PRICE_MAPPING = 'stock_price_mapping'

class StockMonitor(object):
    '''
    This class is used to get data from remove jqdata quant source. After get data, it will push to a database.
    '''

    def __init__(self, stock, username, password):
        self.stock = stock
        self.username = username
        self.password = password
        return

    def to_mysql_price(self, engine):
        self.engine = engine
        
        try:
            self.price_data.to_sql(con=engine, index=True, if_exists='replace', name=self.price_table)
        except:
            print("Error: please initialize the database first!")
        # creat mapping table
        self.creat_price_mapping_table()
        # insert mapping entry
        self.insert_price_mapping()

    def to_sync_price(self, engine):
        # read from database
        df = pd.read_sql('select * from %s;' % self.price_table, con=engine, index_col='date')
        # concat data, sort, remove duplicated rows
        self.price_data = pd.concat((df, self.price_data))
        self.price_data.drop_duplicates(inplace=True)
        self.price_data.sort_index(inplace=True)
        # write back to database
        self.price_data.to_sql(con=engine, index=True, if_exists='replace', name=self.price_table)


    def __generate_table_name(self):
        name = self.stock_info.code.split('.')
        name.sort(reverse=True)
        name = '_'.join(name)
        return name.lower()

    def to_mysql_finance(self, engine):
        self.engine = engine
        
        try:
            self.finance_data.to_sql(con=engine, if_exists='replace', name=self.finance_table, dtype={'day':DATETIME()})
        except:
            print("Error: please initialize the database first!")
        # create the mapping table firstly
        self.create_mapping_entry()
        # insert row into mappting table
        self.insert_mapping_entry()   

    def to_sync_finance(self, engine):
        '''
        Below example is used to get the row information which time is the datest. 
        mycursor.execute('select * from xshe_000425_finance where day = (select max(day) from xshe_000425_finance);')
        mycursor.fetchall()
        Out[71]: 
        [(datetime.datetime(2018, 9, 28, 0, 0),
        19.6546,
        0.4041,
        1.2581,
        0.8009,
        35.4762,
        783366.8125,
        309.4299,
        699356.3125,
        276.2457,
        30.3179)]
        '''
        mydb = mysql.connector.connect(host='localhost', user='root', database=STOCK_DATABASE)
        mycursor = mydb.cursor()
        mycursor.execute('select max(day) from %s;' % self.finance_table)
        latest_day = mycursor.fetchone()
        if latest_day is None:
            print('Error: cannot get the data from table %s' % self.finance_table)
            return

        latest_day = latest_day[0]
        self.init_finance_table(start_date=latest_day)
        self.finance_data.to_sql(con=engine, if_exists='append', name=self.finance_table, dtype={'day':DATETIME()})     
        mydb.close()

    def authenticate(self):
        jdk.auth(self.username, self.password)
    

    def init_light(self):
        self.authenticate()
        self.stock = jdk.normalize_code(self.stock)
        self.stock_info = jdk.get_security_info(self.stock)
        
        if self.stock_info is None:
            print('Error: Cannot get data or stock code not correct!')

        self.finance_table = self.__generate_table_name() + '_finance'
        self.price_table = self.__generate_table_name() + '_price'


    def init(self):
        '''
        Get price, open, close, high, low, volume. And finantial data, TTM, PB, etc. 
        '''
        self.authenticate()
        self.stock = jdk.normalize_code(self.stock)
        self.stock_info = jdk.get_security_info(self.stock)

        if self.stock_info is None:
            print('Error: Cannot get data or stock code not correct!')

        self.finance_table = self.__generate_table_name() + '_finance'
        self.price_table = self.__generate_table_name() + '_price'

        price_data = jdk.get_price(self.stock, start_date=self.stock_info.start_date, end_date=datetime.now())
        # remove NaN data
        self.price_data = price_data.dropna()
        self.price_data.index.name = 'date'

        print('%s[%s] from %s - %s ' % (self.stock_info.display_name, self.stock, 
               self.stock_info.start_date, self.stock_info.end_date))
        
        # get financial data
        #self.__init_finance_table()


    def init_finance_table(self, start_date=0):
        self.authenticate()
        self.stock = jdk.normalize_code(self.stock)
        self.stock_info = jdk.get_security_info(self.stock)

        if self.stock_info is None:
            print('Error: Cannot get data or stock code not correct!')
        '''Internal usage. To get finance table'''
        
        q = jdk.query(jdk.valuation).filter(jdk.valuation.code == self.stock)
        end_date = datetime.now().date()
        
        if start_date == 0:
            df = jdk.get_fundamentals_continuously(q, end_date=end_date, count=5000)
        else:
            # get the days between start date and end date
            date_span = jdk.get_trade_days(start_date=start_date, end_date=end_date)
            if len(date_span) == 0:
                return
            df = jdk.get_fundamentals_continuously(q, end_date=end_date, count=len(date_span))

        if df is None:
            return

        self.finance_data = df.swapaxes('items', 'minor_axis')
        self.finance_data = self.finance_data[self.stock]
        del self.finance_data['day.1']
        del self.finance_data['code.1']
        del self.finance_data['id']
        return

    def insert_mapping_entry(self):
        '''
        Insert to stock and finance table name mapping table. 
        User can use this table to find the table name according to a specific stock code. 
        '''
        mydb = mysql.connector.connect(host='localhost', user='root', database=STOCK_DATABASE)
        mycursor = mydb.cursor()
        stock = self.stock.split('.')[0]
        # insert into a table
        sql = "INSERT INTO %s (table_code, table_name) VALUES ('%s', '%s')" % (STOCK_ID_MAPPING, stock, self.finance_table)
        print("INSERT:", sql)
        try:
            mycursor.execute(sql)
            # without commit nothing will happened. 
            mydb.commit()
        except:
            pass
        mydb.close()
        return 

    def insert_price_mapping(self):
        '''
        Insert to stock_price_mapping table. This table is used for mapping the stock name and the price table name. 
        '''
        mydb = mysql.connector.connect(host='localhost', user='root', database=STOCK_DATABASE)
        mycursor = mydb.cursor()
        stock = self.stock.split('.')[0]
        # insert into a table
        sql = "INSERT INTO %s (stock_code, stock_table_name) VALUES ('%s', '%s')" % (STOCK_PRICE_MAPPING, stock, self.price_table)
        print("INSERT:", sql)
        try:
            mycursor.execute(sql)
            mydb.commit()
        except:
            pass
        mydb.close()
        return 

    def creat_price_mapping_table(self):
        if if_table_exists(STOCK_DATABASE, 'stock_price_mapping') == False:
            mydb = mysql.connector.connect(host='localhost', user='root', database=STOCK_DATABASE)
            mycursor = mydb.cursor()
            # create table
            mycursor.execute('create table %s (stock_code CHAR(30) NOT NULL UNIQUE, stock_table_name CHAR(30) NOT NULL, PRIMARY KEY(stock_code));' 
                             % STOCK_PRICE_MAPPING)
        else:
            return

    def create_mapping_entry(self):
        if if_table_exists(STOCK_DATABASE, 'stock_mapping') == False:
            mydb = mysql.connector.connect(host='localhost', user='root', database=STOCK_DATABASE)
            mycursor = mydb.cursor()
            # create table
            mycursor.execute('create table %s (table_code CHAR(30) NOT NULL UNIQUE, table_name CHAR(30) NOT NULL, PRIMARY KEY(table_code));' 
                             % STOCK_ID_MAPPING)
        else:
            return 

TARGET_COLUMNS = ['pe_ratio']

def read_price_data(stock_code, start_date, end_date):
    '''
    read price information from database or remote data source
    '''
    mydb = mysql.connector.connect(host='localhost', user='root', database=STOCK_DATABASE)
    mycursor = mydb.cursor()

    try:
        sql = 'select stock_table_name from %s where stock_code = "%s";' % (STOCK_PRICE_MAPPING, stock_code)
        mycursor.execute(sql)
        #print(sql)
        # if there is no such row, it will return none. At this time, this will trigger an exception.
        table_name = mycursor.fetchone()[0]
        print('Debug: Using existing table %s '% table_name )
    except:
        # We need to create that table
        stock = StockMonitor(stock_code, '18951518869', 'ceshi123')
        stock.init()
        engine = create_engine("mysql+mysqldb://root:"+"@localhost/%s" % STOCK_DATABASE)
        stock.to_mysql_price(engine)
        table_name = stock.price_table
        print('Debug: Create new table %s '% table_name )

    engine = create_engine("mysql+mysqldb://root:"+"@localhost/%s" % STOCK_DATABASE)
    df = pd.read_sql('select date,open,close,high,low,volume from %s where date > "%s" and date < "%s";' % (table_name, start_date, end_date), 
                    con=engine, index_col='date')
    return df

stock_set = ['601318.XSHG', '601088.XSHG', '600028.XSHG', '300070.XSHE', '000651.XSHE', '601166.XSHG', '002508.XSHE',
             '002027.XSHE', '002304.XSHE', '600048.XSHG', '601211.XSHG', '600019.XSHG', '600104.XSHG', '000848.XSHE', 
             '600377.XSHG', '000581.XSHE', '600332.XSHG', '002327.XSHE', '300144.XSHE', '000895.XSHE', '600660.XSHG',
             '000425.XSHE', '600761.XSHG', '300244.XSHE', '002415.XSHE', '002024.XSHE', '601566.XSHG', '600004.XSHG',
             '000887.XSHE', '600674.XSHG', '603799.XSHG', '603808.XSHG', '600054.XSHG']

def read_finance_data(stock_code, target, start_date, end_date):
    '''To read financial data from a database or a remote peer'''
    mydb = mysql.connector.connect(host='localhost', user='root', database=STOCK_DATABASE)
    mycursor = mydb.cursor()
    sql = 'select table_name from %s where table_code = "%s";' % (STOCK_ID_MAPPING, stock_code)
    mycursor.execute(sql)
    print(sql)

    try:
        # if there is no such row, it will return none. At this time, this will trigger an exception.
        table_name = mycursor.fetchone()[0]
        existing = True
    except:
        # We need to create that table
        stock = StockMonitor(stock_code, '18951518869', 'ceshi123')
        stock.init()
        engine = create_engine("mysql+mysqldb://root:"+"@localhost/%s" % STOCK_DATABASE)
        stock.to_mysql_finance(engine)
        existing = False
        table_name = stock.finance_table    
    # check the column
    mycursor.execute('show columns from %s;' % table_name)
    res = mycursor.fetchall()
    res = [i[0] for i in res]
    # the target is not correct
    if target not in res:
        return None

    engine = create_engine("mysql+mysqldb://root:"+"@localhost/%s" % STOCK_DATABASE)
    if existing == True:
        stock = StockMonitor(stock_code, '18951518869', 'ceshi123')
        stock.init_light()
        stock.to_sync_finance(engine)

    df = pd.read_sql('select day, %s from %s where day > "%s" and day < "%s";' % (target, table_name, start_date, end_date), 
                    con=engine, index_col='day')
    return df


def get_all_financial_data():
    df_set = []
    jdk.auth('18951518869', 'ceshi123')

    for stock in stock_set:
        stock_info = jdk.get_security_info(stock)             
        stock = stock.split('.')[0]

        df = read_finance_data(stock, 'pe_ratio', '2016-1-1', '2018-10-4')
        if df is None:
            print(stock)
            continue
        df_set.append(df)
        try:
            waveline.draw_diagram(df, 'PE-TTM', stock, stock_info.display_name)
        except:
            continue


if __name__ == '__main__':
    stock = StockMonitor('600532', '18951518869', 'ceshi123')
    stock.init()


    
    
