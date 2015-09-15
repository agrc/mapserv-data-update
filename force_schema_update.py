"""
Used to force the update of a local file geodatabase from SDE
even when there is a schema change. If the feature class does not
exist in the local file geodatabase it is created.

It would be cool to hook this to a link in the schema change email
so that you just needed to click on a link to force an update.
"""

import arcpy
from agrc import logging
from agrc import messaging
from agrc import arcpy_helpers
import settings

fgdb = r'\\172.16.17.53\ArcGISServer\data\SGID10.gdb'
sde = r'.\database_connections\SGID10.sde'

# get parameters
fClass = arcpy.GetParameterAsText(0)
local = fgdb + '\\' + fClass

logger = logging.Logger()
emailer = messaging.Emailer(settings.NOTIFICATION_EMAILS)

try:
    logger.logMsg('Finding sde feature class')
    fClass_SDE = arcpy_helpers.FindFeatureClassInSDE(fClass, sde)

    logger.logMsg('Deleting local data, if it exists already')
    arcpy_helpers.DeleteIfExists([local])

    logger.logMsg('Coping new data to local fgdb')
    arcpy.Copy_management(fClass_SDE, local)

except arcpy.ExecuteError as e:
    logger.logMsg('arcpy.ExecuteError')
    logger.logError()
    logger.logGPMsg()
    emailer.sendEmail(logger.scriptName + ' - arcpy.ExecuteError', logger.log)
    raise e
except Exception as e:
    logger.logError()
    emailer.sendEmail(logger.scriptName + ' - Python Error', logger.log)
    raise e
finally:
    logger.writeLogToFile()
