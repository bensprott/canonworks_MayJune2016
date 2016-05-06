'''
This class is meant to be able to match entries and figure out 
if they are related.
Created on Oct 21, 2014

@author: Ben Sprott
'''

class CompareEntries(object):
    '''
    classdocs
    '''


    def __init__(self, dbConn):
        '''
        Constructor
        '''
        self.dbConn = dbConn
        
    
    def findRelatedEntries(self, entryText):
        '''
        goes through the entire database and finds related entries
        '''
        cur = self.dbConn.execute('select id, user_name, title, text from entries')        
        entries = [dict(id=row[0], user_name=[1], title=row[2], text=row[3]) for row in cur.fetchall()]
        
        