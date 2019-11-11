import os
import yaml

# import psycopg2
# from psycopg2.extras import RealDictCursor

import pymysql.cursors



class db_conn(object):
    '''
    Simple database connection and query layer.  
    Opens and closes and new connection each query.
    Define db connection params in config file.

    Config file follows yaml format and should contain one dict entry per database:
    {
        "(database name)":
        {
            "server" : (server name/ip),
            "user"   : (db username),
            "pwd "   : (db password,
            "port"   : (db server port),
            "type"   : (db type: mysql, postgresql),
        },
    }

    TODO: improve error/warning reporting and logging
    '''

    def __init__(self, configFile):

        self.readOnly = 0
        self.VALID_DB_TYPES = ('mysql', 'postgresql')

        #parse config file
        assert os.path.isfile(configFile), f"ERROR: config file '{configFile}'' does not exist.  Exiting."
        with open(configFile) as f: self.config = yaml.safe_load(f)


    def connect(self, database):
        '''
        Connect to the specified database.  
        '''

        #get db connect data
        assert database in self.config, f"ERROR: database '{database}' not defined in config file.  Exiting."
        config = self.config[database]
        server       = config['server']
        user         = config['user']
        pwd          = config['pwd']
        port         = int(config['port']) if 'port' in config else 0
        type         = config['type']

        #check type is valid
        assert type in self.VALID_DB_TYPES, f"ERROR: database type '{type}' not supported.  Exiting."

        #connect
        try:
            if  type == 'mysql': 
                conn = pymysql.connect(user=user, password=pwd, host=server, database=database)
            elif type == 'postgresql': 
                conn = psycopg2.connect(user=user, password=pwd, host=server, port=port, database=database)
        except Exception as e:
            conn = None
            print ("ERROR: Could not connect to database.")
            print ('ERROR: ', e)

        return conn


    def query(self, database, query, getOne=False, getColumn=False, getInsert=False):
        '''
        Executes basic query.  Determines query type and returns fetchall on select, otherwise rowcount on other query types.
        Returns false on any exception error.  Opens and closes a new connection each time.
        '''

        #print (query)
        result = False

        try:
            conn = self.connect(database)

            #get database type
            type = self.config[database]['type']

            #determine query type and check for read only restriction
            qtype = query.strip().split()[0]
            if self.readOnly and qtype not in ('select'):
                print ('ERROR: Attempting to write to DB in read-only mode.')
                return False

            #get cursor
            #todo: use "with" syntax?
            cursor = None
            if   type == 'mysql':
                cursor = conn.cursor(pymysql.cursors.DictCursor)
            elif type == 'postgresql':
                conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                cursor = conn.cursor(cursor_factory=RealDictCursor)

            #execute query and determine return value by qtype
            if cursor:
                cursor.execute(query)
                if   qtype in ('select'): result = cursor.fetchall()
                elif getInsert          : result = cursor.fetchone()
                else                    : result = cursor.rowcount
                cursor.close()

            #requesting one result?
            if getOne and isinstance(result, list):
                if len(result) == 0: result = False
                else               : result = result[0] 

            #requesting single column (to remove associative/dictionary key for easy query)
            if getColumn and result:
                if isinstance(result, list): result = [row[getColumn] for row in result]
                else                       : result = result[getColumn]

        except Exception as e:
            print ('ERROR: ', e)
            result = False

        finally:
            if cursor: cursor.close()
            if conn: conn.close()

        return result



