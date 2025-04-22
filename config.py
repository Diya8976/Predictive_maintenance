# config.py
import pymysql


DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'root',
    'database': 'predictive_maintenance',
    #'cursorclass': pymysql.cursors.DictCursor
}

EMAIL_CONFIG = {
    'from_email': 'vinniesharma965@gmail.com',
    'app_password': 'tlns lgtv yakb muer',
    'to_email': 'vinniesharma22@gmail.com'
}
