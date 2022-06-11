"""

Skrypt w języku python, dzięki któremu można pobrać aktualny kurs ze strony NBP
jak i również zapisać dane z  bazy danych do pliku.

Args:
  `-r`: Generuje plik xlsx z aktualnymi danymi znajdującymi się w bazie danych\n
  `-u`: Pobiera aktualne wartości kursów walutowych i wpisuje do bazy danych.\n


"""


import requests
import logging
import mysql.connector as connection
import pandas as pd
import sys

logging.basicConfig(
  filename='main.log',
  filemode='w',
  format='%(asctime)s - %(message)s', 
  encoding='utf-8', 
  level=logging.DEBUG)


class CollectCurrency:
  """
  `CollectCurrency` klasa dzięki której możemy zadeklarować pobieranie kursów walutowych.

  Args:
    table (str): Tabela z NBP (A,B,C).
    currency (str): Waluta, którą chcemy uzyskać np. USD.
  """
  def __init__(self, table, currency):
    self.table = table
    self.currency = currency
    self.Value = 0

  def collect(self):
    """
    `collect` pobiera aktualne kursy.

    Returns:
      varname.Value: Wartość aktualnego kurstu.
    """
    try:
      fvalue = requests.get(f'http://api.nbp.pl/api/exchangerates/rates/{self.table}/{self.currency}/')
      fvalue = fvalue.json()
      fvalue = fvalue['rates'][0]['mid']
      self.Value = fvalue

    except:
      logging.info(f'The data was not collected correctly ({self.currency})')
      
def UnitPrice():
  dollar = CollectCurrency('A','USD')
  euro = CollectCurrency('A','EUR')
  euro.collect()
  dollar.collect()

  if dollar.Value != 0 or euro.Value != 0:
    try:
      cnx = connection.connect(
        user='root',
        passwd='',
        host='localhost',
        database='mydb')
      
      logging.info('Successfully connected to the database')

      if cnx.is_connected():
          cnx.autocommit = False
          cursor = cnx.cursor()

          sql = f'UPDATE mydb.product SET '

          if euro.Value != 0:
            sql = sql+f'UnitPriceEuro = UnitPrice * {float(euro.Value)}'

          if euro.Value != 0 and dollar.Value != 0:
            sql = sql + ','

          if dollar.Value != 0:
            sql = sql+f'UnitPriceUSD = UnitPrice * {float(dollar.Value)}'

          cursor.execute(sql)
          cnx.commit()
          logging.info('The data has been updated')
          cnx.close()

    except connection.Error as err:
      logging.error(err)

  else:
    logging.error("No data to be processed")

def RenderXLS():

  try:
    cnx = connection.connect(
      user='root',
      passwd='',
      host='localhost',
      database='mydb',)

    logging.info('Successfully connected to the database')

    if cnx.is_connected():
      query = 'SELECT ProductID,DepartmentID,Category,IDSKU,ProductName,Quantity,UnitPrice,UnitPriceUSD,UnitPriceEuro,Ranking,ProductDesc,UnitsInStock,UnitsInOrder from mydb.product;'

      cursor = cnx.cursor()
      cursor.execute(query)

      names = [i[0] for i in cursor.description]

      
      df = pd.DataFrame(cursor.fetchall(), columns=names)
    
      writer = pd.ExcelWriter('data_dump.xlsx', engine='xlsxwriter', )
      df.to_excel(writer, sheet_name='Data', index = False, startrow=0)
      writer.save()
      cnx.close()

      logging.info('The data has been entered into the file')
    else:
      logging.error("Database connection error")

  except connection.Error as err:
    logging.error(err)

if __name__ == "__main__":
  try:

    if sys.argv[1] == '-u':
      UnitPrice()

    elif sys.argv[1] == '-r':
      RenderXLS()

    elif sys.argv[1] == '-h':
      print('-u | Downloads current data on exchange rates from the NBP website \n-r | Creates an xlsx file with the current data contained in the database')

  except:
    UnitPrice()
    RenderXLS()
