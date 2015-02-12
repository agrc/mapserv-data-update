# Pulls new data from sde to local file geodatabases on mapserv machines

import arcpy
import time
from agrc import logging
from agrc import messaging
from agrc import update
from datetime import date
from datetime import timedelta
import rebuild_locators
import settings
import os


class Runner():

    def __init__(self):
        self.start_time = time.time()
        self.logger = logging.Logger()
        self.emailer = messaging.Emailer(settings.NOTIFICATION_EMAILS,
                                         testing=not settings.SEND_EMAILS)

    def runWithTryCatch(self):
        try:
            self.run()
            self.logger.logMsg('\nScript was successful!')
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

    def run(self):
        self.logger.logMsg("Looping through file geodatabases")
        errors = []
        for db in settings.DATABASES:
            self.archive(db)
            fgd = r'{}\{}.gdb'.format(settings.DBPATH, db)
            sde = r'{}\{}.sde'.format('.\database_connections', db)
            tup = update.updateFGDBfromSDE(fgd, sde, self.logger)
            errors = errors + tup[0]

            self.logger.logMsg('compacting geodatabase')
            arcpy.Compact_management(fgd)

        if update.wasModifiedToday('Roads',
                                   r'{}\{}.gdb'.format(settings.DBPATH,
                                                       'SGID10')):
            rebuild_locators.Runner(self.logger, self.emailer).roads()
        if update.wasModifiedToday('AddressPoints',
                                   r'{}\{}.gdb'.format(settings.DBPATH,
                                                       'SGID10')):
            rebuild_locators.Runner(self.logger, self.emailer).address_points()

        end_time = time.time()
        elapsed_time = end_time - self.start_time
        self.logger.logMsg("total minutes: " + str(elapsed_time / 60))

        if len(errors) > 0:
            txt = "Updated Datasets: \n{}\n\nUpdate Errors:\n{}\n\nLog:\n{}"
            self.emailer.sendEmail(
                self.logger.scriptName + " - Update Errors",
                txt.format("\n".join(update.changes),
                           "\n\n".join(errors),
                           self.logger.log))
        else:
            txt = "Updated Datasets: \n{}\n\nLog:\n{}"
            self.emailer.sendEmail(
                self.logger.scriptName + " - Success",
                txt.format('\n'.join(update.changes),
                           self.logger.log))

        self.logger.writeLogToFile()

        print("done")

    def archive(self, db):
        self.logger.logMsg('** Archiving {}'.format(db))
        archiveFolder = '{}\{}'.format(settings.DBPATH, '_Archives')

        # create archives folder if it doesn't exist
        if not os.path.exists(archiveFolder):
            os.makedirs(archiveFolder)

        self.logger.logMsg('cleaning up old archives')
        arcpy.env.workspace = archiveFolder
        backups = arcpy.ListWorkspaces('{}_*'.format(db), 'FileGDB')
        oneWeek = timedelta(weeks=1)
        today = date.today()
        if backups is not None:
            for b in backups:
                bdate = b[-14:-4]
                year = int(bdate[:4])
                month = int(bdate[5:7])
                day = int(bdate[8:10])
                archiveDate = date(year, month, day)

                if archiveDate < today - oneWeek or archiveDate == today:
                    self.logger.logMsg('Deleting {}'.format(b))
                    arcpy.Delete_management(b)

        archivePath = '{}\{}_{}.gdb'.format(
            archiveFolder, db, str(date.today()))
        self.logger.logMsg('Copying {}'.format(archivePath))
        arcpy.Copy_management(r'{}\{}.gdb'.format(settings.DBPATH, db),
                              archivePath)

if __name__ == "__main__":
    Runner().runWithTryCatch()
