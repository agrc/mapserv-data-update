"""
Used to force the update of a local file geodatabase from SDE
even when there is a schema change. If the feature class does not
exist in the local file geodatabase it is created.

It would be cool to hook this to a link in the schema change email
so that you just needed to click on a link to force an update.

Scott Davis
Nov 2012
"""

import arcpy
import agrc

fgdb = r'C:\MapData\SGID10.gdb'
sde = r'C:\PythonScripts\DatabaseConnections\SGID10.sde'

# get parameters
fClass = arcpy.GetParameterAsText(0)
local = fgdb + '\\' + fClass

logger = agrc.logging.Logger()
emailer = agrc.email.Emailer('stdavis@utah.gov')
services = agrc.agserver.Services()

try:
    logger.logMsg('Finding sde feature class')
    fClass_SDE = agrc.arcpy_helpers.FindFeatureClassInSDE(fClass, sde)

    logger.logMsg('Deleting local data, if it exists already')
    agrc.arcpy_helpers.DeleteIfExists([local])

    logger.logMsg('Coping new data to local fgdb')
    arcpy.Copy_management(fClass_SDE, fClass)

except arcpy.ExecuteError as e:
    logger.logMsg('arcpy.ExecuteError')
    logger.logError()
    logger.logGPMsg()
    emailer.sendEmail(logger.scriptName + ' - arcpy.ExecuteError', logger.log)
except Exception as e:
    logger.logError()
    emailer.sendEmail(logger.scriptName + ' - Python Error', logger.log)
finally:
    logger.writeLogToFile()
