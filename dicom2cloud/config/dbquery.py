from __future__ import print_function
import sqlite3
import pandas
import glob
from os.path import join,abspath, isdir,isfile
from os import access, R_OK, W_OK
import datetime

class DBI():
    def __init__(self, test=False):
        """
        Init for connection to config db
        :param dbfile:
        """
        #locate db in config/
        if test:
            dbname = 'd2c-test.db'
        else:
            dbname= 'd2c.db'
        cpath1 = join('config',dbname)
        cpath2 = join('..',cpath1)
        if access(dbname,R_OK):
            self.dbfile = abspath(dbname)
        elif access(cpath1, R_OK):
            self.dbfile = abspath(cpath1)
        elif access(cpath2, R_OK):
            self.dbfile = abspath(cpath2)
        else:
            raise IOError("Unable to locate Config db")

        self.c = None

    def validstring(self,ref):
        if not isinstance(ref,str) and not isinstance(ref,unicode):
            raise ValueError('Ref is not valid string')
        return ref

    def connect(self):
        self.conn = sqlite3.connect(self.dbfile)
        self.c = self.conn.cursor()

    def closeconn(self):
        self.conn.close()

    def deleteData(self,table):
        """
        TODO: This is causing database locking ??
        :param table:
        :return:
        """
        if self.c is None:
            self.connect()
        self.c.execute('DELETE FROM `' + table + '`')
        print('Table data deleted: ', table)
        self.conn.close()


    def getCaptions(self):
        """
        Get dict of config
        :return: name=value pairs or None
        """
        if self.c is None:
            self.connect()
        self.c.execute("SELECT process FROM processes")
        qry = self.c.fetchall()
        data = [d[0] for d in qry]
        return data

    def getRefs(self):
        """
        Get dict of config
        :return: name=value pairs or None
        """
        if self.c is None:
            self.connect()
        self.c.execute("SELECT ref FROM processes")
        qry = self.c.fetchall()
        data = [d[0] for d in qry]
        return data

    def getDescription(self,caption):
        if self.c is None:
            self.connect()
        self.c.execute("SELECT description FROM processes WHERE process=?", (self.validstring(caption),))
        data = self.c.fetchone()
        if data is not None:
            data = data[0]
        return data

    def getCaption(self,ref):
        if self.c is None:
            self.connect()
        self.c.execute("SELECT process FROM processes WHERE ref=?", (self.validstring(ref),))
        data = self.c.fetchone()
        if data is not None:
            data = data[0]
        return data

    def getProcessModule(self,ref):
        if self.c is None:
            self.connect()
        self.c.execute("SELECT module FROM processes WHERE ref=?", (self.validstring(ref),))
        data = self.c.fetchone()
        if data is not None:
            data = data[0]
        return data

    def getProcessClass(self,ref):
        if self.c is None:
            self.connect()
        self.c.execute("SELECT class FROM processes WHERE ref=?", (self.validstring(ref),))
        data = self.c.fetchone()
        if data is not None:
            data = data[0]
        return data

    def getFiles(self,uuid):
        if self.c is None:
            self.connect()
        self.c.execute("SELECT filename FROM dicomfiles WHERE uuid=?", (self.validstring(uuid),))
        data = self.c.fetchall()
        if data is not None:
            data = [d[0] for d in data]
        return data

    def addDicomdata(self,dicomdata):
        """
        Load new dicomdata for series
        :param dicomdata: dict with dicomdata fields
        :return:
        """
        #'patientid', 'patientname', 'seriesnum', 'sequence', 'protocol', 'imagetype'
        if self.c is None:
            self.connect()
        if isinstance(dicomdata,dict):
            self.c.execute("INSERT INTO dicomdata (uuid,patientid,patientname,seriesnum,sequence,protocol,imagetype) VALUES (?,?,?,?,?,?,?)", (dicomdata['uuid'],dicomdata['patientid'], dicomdata['patientname'], dicomdata['seriesnum'], dicomdata['sequence'], dicomdata['protocol'], dicomdata['imagetype']))
            self.conn.commit()
            print('Dicomdata loaded: ', dicomdata)
            rtn = 1
        else:
            self.conn.rollback()
            print('Invalid data for Dicomdata')
            rtn = 0
        return rtn
            
    def addDicomfile(self,uuid,dicomfile):
        if self.c is None:
            self.connect()
        if self.validstring(uuid) and isfile(dicomfile):
            self.c.execute("INSERT INTO dicomfiles (filename,uuid) VALUES(?,?)", (dicomfile,uuid))
            self.conn.commit()
            print('Dicomfile loaded: ', dicomfile)
            rtn = 1
        else:
            self.conn.rollback()
            print('Invalid data for Dicomfile')
            rtn = 0
        return rtn

    def hasFile(self,dicomfile):
        rtn = False
        if self.c is None:
            self.connect()
        self.c.execute("SELECT COUNT(*) FROM dicomfiles WHERE filename=?", (dicomfile,))
        data = self.c.fetchone()
        if data is not None and data[0] > 0:
            rtn = True
        return rtn
            
    def getUuids(self):
        if self.c is None:
            self.connect()
        self.c.execute("SELECT uuid FROM dicomdata")
        qry = self.c.fetchall()
        data = [d[0] for d in qry]
        return data

    def getNewUuids(self):
        if self.c is None:
            self.connect()
        self.c.execute("SELECT uuid FROM dicomdata")
        qry = self.c.fetchall()
        self.c.execute("SELECT uuid FROM seriesprocess")
        sps = self.c.fetchall()
        data = [d[0] for d in qry if d not in sps]
        return data

    def hasUuid(self,uuid):
        rtn = False
        if self.c is None:
            self.connect()
        self.c.execute("SELECT COUNT(*) FROM dicomdata WHERE uuid=?", (self.validstring(uuid),))
        data = self.c.fetchone()
        if data is not None and data[0] > 0:
            rtn = True
        return rtn

    def getNumberFiles(self,uuid):
        if self.c is None:
            self.connect()
        self.c.execute("SELECT COUNT(*) FROM dicomfiles WHERE uuid=?", (self.validstring(uuid),))
        data = self.c.fetchone()
        if data is not None:
            data = data[0]
        return data

    def getDicomdata(self,uuid,fieldname):
        if self.c is None:
            self.connect()
        if not self.validstring(fieldname) or fieldname == 'all':
            self.c.execute("SELECT uuid,patientid,patientname,seriesnum,sequence,protocol,imagetype FROM dicomdata WHERE uuid=?", (self.validstring(uuid),))
            data = self.c.fetchall()
            if data is not None:
                data = {'uuid': data[0][0],
                           'patientid': data[0][1],
                           'patientname': data[0][2],
                           'seriesnum': data[0][3],
                           'sequence': data[0][4],
                           'protocol': data[0][5],
                           'imagetype': data[0][6]}
        else:
            self.c.execute("SELECT " + fieldname + " FROM dicomdata WHERE uuid=?", (self.validstring(uuid),))
            data = self.c.fetchall()
            if data is not None:
                data = data[0][0]
        return data

    def getRef(self,processname):
        if self.c is None:
            self.connect()
        self.c.execute("SELECT ref FROM processes WHERE process=?", (self.validstring(processname),))
        data = self.c.fetchone()
        if data is not None:
            data = data[0]
        return data

    def setSeriesProcess(self,uuid,pid,server,status,starttime,outputdir):
        if self.c is None:
            self.connect()
        if self.validstring(uuid) and self.validstring(server):
            self.c.execute("INSERT INTO seriesprocess (uuid,processid,server,status,starttime,outputdir) VALUES(?,?,?,?,?,?)", (uuid,pid,server,status,starttime, outputdir))
            self.conn.commit()
            print('Seriesprocess loaded: ', uuid)
            rtn = 1
        else:
            self.conn.rollback()
            print('Invalid data for Seriesprocess')
            rtn = 0
        return rtn

    def getProcessId(self,processname):
        if self.c is None:
            self.connect()
        self.c.execute("SELECT id FROM processes WHERE process=?", (self.validstring(processname),))
        data = self.c.fetchone()
        if data is not None:
            data = data[0]
        return data

    def getProcessField(self,fieldname,processname):
        if self.c is None:
            self.connect()
        self.c.execute("SELECT " + fieldname + " FROM processes WHERE process=?", (self.validstring(processname),))
        data = self.c.fetchone()
        if data is not None:
            data = data[0]
        return data

    def getActiveProcesses(self):
        if self.c is None:
            self.connect()
        self.c.execute("SELECT sp.uuid,p.process,sp.server,sp.status,sp.starttime,sp.endtime, sp.outputdir FROM seriesprocess as sp, processes as p WHERE sp.processid = p.id")
        data = self.c.fetchall()

        return data

    def setSeriesProcessInprogress(self, uuid):
        if self.c is None:
            self.connect()
        if self.validstring(uuid):
            status=2 #in progress - correlate with lookup status
            self.c.execute("UPDATE seriesprocess SET status=? WHERE uuid=?" ,(status,uuid))
            self.conn.commit()
            print('Seriesprocess updated: ', uuid)
            rtn = 1
        else:
            self.conn.rollback()
            print('Invalid data for Seriesprocess')
            rtn = 0
        return rtn

    def setSeriesProcessFinished(self, uuid):
        if self.c is None:
            self.connect()
        if self.validstring(uuid):
            status=3 #Finished - correlate with lookup status
            endtime = datetime.datetime.now()
            self.c.execute("UPDATE seriesprocess SET status=?, endtime=? WHERE uuid=?" ,(status,endtime,uuid))
            self.conn.commit()
            print('Seriesprocess loaded: ', uuid)
            rtn = 1
        else:
            self.conn.rollback()
            print('Invalid data for Seriesprocess')
            rtn = 0
        return rtn

    def deleteSeriesData(self,uuid):
        """
        Remove all data from database for a series
        :param uuid:
        :return:
        """
        rtn = False
        if self.c is None:
            self.connect()
        if self.validstring(uuid):
            self.c.execute('DELETE FROM dicomdata WHERE uuid=?', (uuid,)) #cascade NOT working?
            self.c.execute('DELETE FROM dicomfiles WHERE uuid=?', (uuid,))
            self.c.execute('DELETE FROM seriesprocess WHERE uuid=?', (uuid,))
            self.conn.commit()
            print('Series data deleted: ', uuid)
            rtn = True
        return rtn

#############################################################################
if __name__ == "__main__":
    import os

    print(os.getcwd())
    try:
        dbi = DBI()
        dbi.connect()
        data = dbi.getCaptions()
        print(data)
        #Delete
        # uuid = '5d74a20b44ec1dfd0af4fbc6bb680e0f557c14a08a143b843ef40977697e2bea'
        # dbi.deleteSeriesData(uuid)
        ds = dbi.getNewUuids()
        print(ds)

    except:
        raise IOError("cannot access db")

