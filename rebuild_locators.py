# Updates data and rebuilds address locators

import arcpy
from agrc import logging, messaging, ags
import settings
import os


locatorRoads = r'{}\Roads'.format(settings.LOCATORS_FGDB)
locatorAddressPoints = r'{}\AddressPoints'.format(settings.LOCATORS_FGDB)

baseRoads = r'{}\Roads'.format(settings.BASE_FGDB)
baseAddressPoints = r'{}\AddressPoints'.format(settings.BASE_FGDB)


sddraftsFolder = r'{}\sddrafts'.format(os.getcwd())

locators_roads = [
            'Roads_AddressSystem_ACSALIAS',
            'Roads_AddressSystem_ALIAS1',
            'Roads_AddressSystem_ALIAS2',
            'Roads_AddressSystem_STREET',
            ]
locator_addressPoints = 'AddressPoints_AddressSystem'


class Runner():
    def __init__(self, logger, emailer):
        self.logger = logger
        self.emailer = emailer
        self.agsAdmin = ags.AGSAdmin(settings.AGS_USERNAME,
                                     settings.AGS_PASSWORD,
                                     settings.AGS_IP)

    def roads(self):
        self.update_data(baseRoads, locatorRoads)
        for l in locators_roads:
            self.rebuild_locator(l)
        self.sendSuccessEmail('Roads')

    def address_points(self):
        self.update_data(baseAddressPoints, locatorAddressPoints)
        self.rebuild_locator(locator_addressPoints)
        self.sendSuccessEmail('AddressPoints')

    def update_data(self, source, dest):
        self.logger.logMsg('updating {} from {}'.format(dest, source))
        arcpy.TruncateTable_management(dest)
        arcpy.Append_management(source, dest, "NO_TEST")

    def rebuild_locator(self, locator):
        self.logger.logMsg('rebuilding {}'.format(locator))
        arcpy.env.workspace = settings.LOCATORS_FGDB
        arcpy.RebuildAddressLocator_geocoding(locator)
        sdFile = '{}\{}.sd'.format(sddraftsFolder, locator)

        # clear out any old .sd files
        if arcpy.Exists(sdFile):
            arcpy.Delete_management(sdFile)
        sddraftFile = '{}\{}.sddraft'.format(sddraftsFolder, locator)
        if arcpy.Exists(sddraftFile):
            arcpy.Delete_management(sddraftFile)

        # delete existing locator service
        # service = r'Geolocators/' + locator
        # serviceType = 'GeocodeServer'
        # self.logger.logMsg('deleting existing service')
        # self.agsAdmin.deleteService(service, serviceType)

        # need to make a copy of the .sddraft file
        # since StateService deletes it
        self.logger.logMsg('publishing new service')
        arcpy.Copy_management(
            '{}\{}\{}.sddraft'.format(sddraftsFolder,
                                      settings.ORIGINALS_FOLDER,
                                      locator),
            sddraftFile)
        arcpy.StageService_server(sddraftFile, sdFile)
        arcpy.UploadServiceDefinition_server(sdFile,
                                             settings.GIS_SERVER_CONNECTION)

        self.logger.logMsg('validating service status')
        if (not self.agsAdmin.getStatus(service, serviceType)['realTimeState']
                == 'STARTED'):
            raise '{} was not restarted successfully!'.format(service)

    def sendSuccessEmail(self, fc):
        body = ('The {} feature class was updated and all ',
                'associated locators were rebuilt.').format(fc)
        self.emailer.sendEmail('{}-related locators were rebuilt'.format(fc),
                               body)

    def runWithTryCatch(self):
        try:
            self.roads()
            self.address_points()
            self.logger.logMsg('\nScript completed successfully!')
        except arcpy.ExecuteError:
            self.logger.logMsg('arcpy.ExecuteError')
            self.logger.logError()
            self.logger.logGPMsg()
            self.emailer.sendEmail(
                self.logger.scriptName + ' - arcpy.ExecuteError',
                self.logger.log)
        except Exception:
            self.logger.logError()
            self.emailer.sendEmail(
                self.logger.scriptName + ' - Python Error',
                self.logger.log)
        finally:
            self.logger.writeLogToFile()

if __name__ == "__main__":
    Runner(
        logging.Logger(),
        messaging.Emailer(settings.LOCATOR_NOTIFICATION_EMAILS,
                          testing=not settings.SEND_EMAILS)).runWithTryCatch()
