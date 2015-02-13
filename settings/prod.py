DBPATH = r"\\ITAS104SP\ArcGISServer\data"
DATABASES = ["SGID10", "UDES", "FiberVerification"]
NOTIFICATION_EMAILS = ['stdavis@utah.gov']
SEND_EMAILS = True
LOCATORS_FGDB = r'\\172.16.17.53\ArcGISServer\locators\Locators.gdb'
BASE_FGDB = '{}\{}'.format(DBPATH, 'SGID10.gdb')
GIS_SERVER_CONNECTION = r'.\gis_servers\arcgis on 172.16.17.54_6080 (admin)'
LOCATOR_NOTIFICATION_EMAILS = ['stdavis@utah.gov',
                               'kkgreen@utah.gov',
                               'zbeck@utah.gov',
                               'sgourley@utah.gov']
AGS_IP = '172.16.17.54'
ORIGINALS_FOLDER = 'originals_prod'
