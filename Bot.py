import smtplib
import ssl
import time
import requests
from lxml import etree
from lxml import html
from datetime import datetime
from datetime import date
from datetime import timedelta
import pytz
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import imaplib
import email
import json
from tzlocal import get_localzone

port = 465
local_tz = str(get_localzone())
with open('input_info.txt', 'r') as file:
  for index, line in enumerate(file):
    if index == 0:
      my_email = line.split(' ')[1].strip()
    elif index == 1:
      bot_email = line.split(' ')[1].strip()
    elif index == 2:
      password = line.split(' ')[1].strip()
    elif index == 3:
      zip_code = line.split(' ')[1].strip()
    elif index == 4:
      send_time = line.split(' ')[1].strip().split(':')
      send_hour = int(send_time[0])
      send_minute = int(send_time[1])
context = ssl.create_default_context()
session = requests.session()
sent = False  
while True:
    time.sleep(1)
    datet = datetime.now()
    if datet.hour == send_hour and datet.minute == send_minute and not sent:
        #Construct email
        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
          dateNow = str(datet.date().month) + "/" + str(datet.date().day) + "/" + str(datet.date().year)
          x = requests.session()
          headers = {'content-type': 'application/json'}
          data = '[{"name":"getSunV3LocationSearchUrlConfig","params":{"query":" + ' + zip_code + '","language":"en-US","locationType":"locale"}}]'
          response = requests.post('https://weather.com/api/v1/p/redux-dal', headers=headers, data=data)
          weather = requests.get('https://weather.com/weather/today/' + response.text.split('"placeId":["')[1].split('"')[0])
          weather = str(etree.tostring(html.fromstring(weather.content).xpath('/html/body')[0]))
          weather_out = weather.split('CurrentConditions--tempValue')[1].split('>')[1].split('<')[0]
          weather_word = weather.split('CurrentConditions--phraseValue')[1].split('>')[1].split("<")[0]
          #Recieving info
          reminder = ''
          mail = imaplib.IMAP4_SSL('smtp.gmail.com')
          mail.login(bot_email, password)
          mail.select('inbox')
          status, data = mail.search(None, 'ALL')
          mail_ids = []
          for block in data:
              mail_ids += block.split()
          breakable = False
          for i in range(len(mail_ids) - 1, 0, -1):
              status2, data2 = mail.fetch(mail_ids[i], '(RFC822)')
              mail_content = ''
              for response_part in data2:
                  message = email.message_from_bytes(response_part[1])
                  yesterday = date.today() - timedelta(days=1)
                  yesterday_datetime = datetime(yesterday.year, yesterday.month, yesterday.day, tzinfo=pytz.timezone(local_tz))
                  splitted_date = message['Date'].split(' ')
                  splitted_time = message['Date'].split(':')
                  month = 1 if splitted_date[2] == 'Jan' else 2 if splitted_date[2] == 'Feb' else 3 if splitted_date[2] == 'Mar' else 4 if splitted_date[2] == 'Apr' else 5 if splitted_date[2] == 'May' else 6 if splitted_date[2] == 'Jun' else 7 if splitted_date[2] == 'Jul' else 8 if splitted_date[2] == 'Aug' else 9 if splitted_date[2] == 'Sept' else 10 if splitted_date[2] == 'Oct' else 11 if splitted_date[2] == 'Nov' else 12
                  msg_date = datetime(int(splitted_date[3]), month, int(splitted_date[1]), int(splitted_time[0][len(splitted_time[0]) - 2:len(splitted_time[0])]), int(splitted_time[1]), tzinfo=pytz.UTC).astimezone(pytz.timezone(local_tz))
                  if msg_date < yesterday_datetime:
                      if reminder == '':
                          mail_content = 'No new reminders'
                      breakable = True
                      break
                  else:
                      if message.is_multipart():
                          mail_content = ''
                          for part in message.get_payload():
                              if part.get_content_type() == 'text/plain':
                                  mail_content += part.get_payload()
                      else:
                          mail_content = message.get_payload()
                      if '> wrote' in mail_content:
                          contents = mail_content.split('\n')
                          mail_content = ''
                          for content in contents:
                              if '> wrote:' not in content:
                                  mail_content += content + '\n'
                              else:
                                  break
                      mail_content = mail_content.strip()
                      if mail_content[0:3] == 'cmd': 
                        if ' birthday ' in mail_content and ' add ' in mail_content:
                          inp_date = mail_content.split('/')
                          inp_date = inp_date[0].split(' ')[-1].split('\r')[0] + '/' + inp_date[1].split(' ')[0].split('\r')[0]
                          splitted_words = mail_content.split(' ')
                          name = ''
                          for x in splitted_words:
                            if x[0].isupper():
                              with open('birthday.json', 'r') as file:
                                birthdays = json.load(file)
                                try:
                                  name = x.replace("'s", '')
                                  if name not in birthdays[inp_date]:
                                    birthdays[inp_date].append(name)
                                    with open('birthday.json', 'w', encoding='utf-8') as file:
                                      json.dump(birthdays, file, ensure_ascii=False)
                                  break
                                except KeyError:
                                  name = x.replace("'s", '')
                                  birthdays[inp_date] = [name.replace("'s", '')]
                                  with open('birthday.json', 'w', encoding='utf-8') as file:
                                      json.dump(birthdays, file, ensure_ascii=False)
                                  break
                        elif ' remove ' in mail_content and ' birthday ' in mail_content:
                          inp_date = mail_content.split('/')
                          inp_date = inp_date[0].split(' ')[-1].split('\r')[0] + '/' + inp_date[1].split(' ')[0].split('\r')[0]
                          splitted_words = mail_content.split(' ')
                          name = ''
                          for x in splitted_words:
                            if x[0].isupper():
                              name = x.replace("'s", '')
                              break
                          try:
                            with open('birthday.json', 'r') as file:
                              birthdays = json.load(file)
                              birthdays[inp_date].remove(name)
                            with open('birthday.json', 'w', encoding='utf-8') as file:
                              json.dump(birthdays, file, ensure_ascii=False)
                          except:
                            print('That could not be removed')
                      else:    
                        reminder += '-' + mail_content + '\n'
                      break
              if breakable:
                  break
          if reminder == '':
              reminder = 'No new reminders'
          # Sending info
          server.login(bot_email, password)
          msg = MIMEMultipart("alternative")
          msg['Subject'] = "Your morning reminder!"
          msg['From'] = bot_email
          msg['To'] = my_email
          birthdays_out = ''
          try:
            with open('birthday.json', 'r', encoding='utf-8') as file:
              birthdays = json.load(file)      
              today = birthdays[str(datet.date().month) + '/' + str(datet.date().day)]
              for i in today:
                birthdays_out += '-' + i + '\n'
          except KeyError:
            birthdays_out = 'None today'
          day = datet.weekday()
          day = 'Monday' if day == 0 else 'Tuesday' if day == 1 else 'Wednesday' if day == 2 else 'Thursday' if day == 3 else 'Friday' if day == 4 else 'Saturday' if day == 5 else 'Sunday'
          email = """<html>
                  <body>
                  <p>Good Morning!</p>
                  <p> Today's date is: """ + dateNow + """</p>
                  <p>The weather right now is """ + weather_word + """ and """ + weather_out + """.</p>
                  <p>Reminders:<br> """ + reminder.replace('\n', '<br>') + """</p>
                  <p>Birthdays:<br>""" + birthdays_out.replace('\n', '<br>') + """</p>
                  Today is """ + day + """
                  </body>
                  </html>"""
          msg.attach(MIMEText(email, 'html'))
          server.sendmail(bot_email, my_email, msg.as_string())
          sent = True
          print('email sent')
    elif not (datet.minute == send_minute) and sent:
        sent = False