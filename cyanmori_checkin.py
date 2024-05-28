import datetime
import os
import requests
import smtplib
from email.mime.text import MIMEText
import json
from lxml import etree


class User:
    def __init__(self, balance, remaining_traffic, remaining_days, vip_expiration_date):
        self.balance = balance
        self.remaining_traffic = remaining_traffic
        self.remaining_days = remaining_days
        self.vip_expiration_date = vip_expiration_date
        self.login_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.check_in_result = None
        
    def format_output(self):
        output = f"Balance: {self.balance}\n"
        output += f"Remaining Traffic: {self.remaining_traffic}\n"
        output += f"Remaining Days: {self.remaining_days}\n"
        output += f"Expiration Date: {self.vip_expiration_date}\n"
        output += f"Login Time: {self.login_time}"
        return output
    

session = requests.session()

cyanmori_username = os.environ.get("CYANMORI_USERNAME")
cyanmori_passwd = os.environ.get("CYANMORI_PASSWD")
qqemail_authorization_code = os.environ.get("QQEMAIL_AUTHORIZATION_CODE")

def login():
    log_in_url = "https://www.cyanmori.com/auth/login"
    user = {"email": cyanmori_username, "passwd": cyanmori_passwd}
    log_in_header = {
        "user-agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
    }
    resp = session.post(log_in_url, headers=log_in_header, data=user)
    print(resp.text.encode('utf-8').decode('unicode_escape'))

def get_user_info():
    user_info_url = 'https://www.cyanmori.com/user'
    user_info_header = {
        "user-agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
        "origin": "https://www.cyanmori.com",
        "Referer": "https://www.cyanmori.com/user"
    }
    resp = session.get(user_info_url, headers=user_info_header)
    user_info = format_user_info(resp.text)
    print(user_info.format_output())
    return user_info

def check_in():
    sign_in_url = "https://www.cyanmori.com/user/checkin"
    sign_in_header = {
        "user-agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
        "origin": "https://www.cyanmori.com",
        "referer": "https://www.cyanmori.com/user"
    }
    resp = session.post(sign_in_url, headers=sign_in_header)
    resp = resp.text.encode('utf-8').decode('unicode_escape')
    resp = json.loads(resp)
    msg = resp.get('msg')
    print(msg)
    return msg
 

def format_user_info(info):
    # 将HTML数据解析为Element对象
    root = etree.HTML(info)
    # 使用XPath选择器提取数据
    balance = root.xpath('//*[@id="kt_content"]/div[2]/div/div[2]/div[4]/div/div[1]/div/div/div/strong/text()')[0]
    remaining_traffic = root.xpath('//*[@id="kt_content"]/div[2]/div/div[2]/div[2]/div/div[1]/div/div/div/strong/text()')[0]
    remaining_days = root.xpath('//*[@id="kt_content"]/div[2]/div/div[2]/div[1]/div/div[1]/div/div/div/strong/span/text()')[0]
    if '已过期' in remaining_days:
        remaining_days = 0
    
    vip_expiration_date = str(root.xpath('//*[@id="kt_content"]/div[2]/div/div[2]/div[1]/div/div[2]/p/text()')[0]).split(':')[1]
    if '已过期' not in vip_expiration_date:        
        index = vip_expiration_date.find("到期")
        vip_expiration_date = vip_expiration_date[:index].strip()
        vip_expiration_date = datetime.datetime.strptime(vip_expiration_date,"%Y-%m-%d").date()
    else:
        vip_expiration_date = '已过期'
    user_info = User(balance,remaining_traffic,remaining_days,vip_expiration_date)
    return user_info

def combine():
    login()
    user_info = get_user_info()
    check_in_result = check_in()
    user_info.check_in_result = check_in_result
    html_table_str = generate_html_table(user_info)
    send_email(html_table_str)

def generate_html_table(user_info):
    table_html = "<table border='1' cellspacing='0' cellpadding='0'>"
    for key, value in user_info.__dict__.items():
        table_html += f"<tr><td>{key.replace('_',' ')}</td><td>{value}</td></tr>"
    table_html += "</table>"
    return table_html

# 自定义日期转换函数
def date_converter(obj):
    if isinstance(obj, datetime.date):
        return obj.strftime('%Y-%m-%d')
    raise TypeError(f"Object of type '{obj.__class__.__name__}' is not JSON serializable")


def send_email(msg):
    # SMTP服务器配置信息
    smtp_server = 'smtp.qq.com'
    smtp_port = 587
    sender_email = '2554545982@qq.com'
    password = qqemail_authorization_code

    # 使用SMTP登录邮箱，并进行身份验证
    mail_server = smtplib.SMTP(smtp_server, smtp_port)
    mail_server.starttls()
    mail_server.login(sender_email, password)

    # 构造消息对象
    message = MIMEText(msg, 'html')
    message['Subject'] = '机场签到'
    message['From'] = sender_email
    message['To'] = '2010713117@qq.com'

    # 发送邮件
    mail_server.sendmail(sender_email, ['2010713117@qq.com'], message.as_string())

    # 关闭SMTP连接
    mail_server.quit()

    print('邮件发送成功！')


if __name__ == '__main__':
    combine()
