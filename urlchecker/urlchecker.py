import requests
import logging
import argparse

from configparser import ConfigParser

_has_dbops = False
try:
    from dbops import dbops
    _has_dbops = True
except:
    pass

def _check_http_ok(url, timeout=30, \
                   user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:54.0) Gecko/20100101 Firefox/54.0'):
    try:
        headers = {'User-agent' : user_agent}
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        logging.info('URL %s returned HTTP 200 OK' % url)
        return True

    except Exception as e:
        logging.error('URL %s raised an exception' % url)
        logging.exception(e)

    return False

def check_url(url):
    return _check_http_ok(url)

_db_inited = False
def init_db(db_host, db_database, db_user, db_pass):
    global _has_dbops
    assert _has_dbops, 'AppCensus dbops module not available'

    global _db_inited

    try:
        dbops.init(db_host, db_database, db_user, db_pass)
        _db_inited = True
        logging.info('Database initialization (host=%s, db=%s, user=%s) successful' % (db_host, db_database, db_user))
    
    except Exception as e:
        _db_inited = False
        logging.error('Database initialization (host=%s, db=%s, user=%s) raised an exception' % (db_host, db_database, db_user))
        logging.exception(e)

def check_db_urls(db_update=True):
    global _has_dbops
    assert _has_dbops, 'AppCensus dbops module not available'

    global _db_inited
    assert _db_inited, 'Database connection not initialized, must run init_db() first'

    urls = dbops.get_policy_urls_and_active()
    for url,previous_active in urls:
        is_active = check_url(url)

        if(previous_active != is_active):
            if(db_update):
                dbops.insert_policy(url, is_url_active=is_active)
            logging.info('Updated url=%s | previous=%s | current=%s' % (url, bool(previous_active), is_active))
        
def _parse_args():
    parser = argparse.ArgumentParser(description='Check privacy policy URLs, update the database')

    parser.add_argument('credentials', help='Path to a credentials file containing \
                                             database credentials. See credentials.secrets.example for format')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--test', action='store_true', help='Run _test() function instead of main program body')

    return parser.parse_args()

def _parse_config(config_file):
    config = ConfigParser()
    config.read(config_file)

    database_header = 'Database'
    assert database_header in config.sections(), 'No Database section found in config file %s' % config_file
    db_cred = {'host':config.get(database_header, 'host'), \
               'database':config.get(database_header, 'database'), \
               'user':config.get(database_header, 'user'), \
               'password':config.get(database_header, 'password')}
    logging.info('Found database credentials for host=%s, database=%s, user=%s' % (db_cred['host'], db_cred['database'], db_cred['user']))

    return db_cred


def _test():
    logging.info('TEST MODE')

    assert check_url('http://google.com')
    assert not check_url('http://docs.python-requests.org/v64cAWHsN0WbYUU5h1xKKpc3xAlPhk')

    check_db_urls(db_update=False)

    logging.info('Test OK!')

if __name__ == '__main__':
    args = _parse_args()
    if(args.verbose or args.test):
        logging.basicConfig(level=logging.INFO)
        logging.info('here')
        print('there')

    db_creds = _parse_config(args.credentials)
    init_db(db_creds['host'], db_creds['database'], db_creds['user'], db_creds['password'])

    if(args.test):
        _test()
    else:
        check_db_urls()

