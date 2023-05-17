"""
WARNING: this script is designed to delete files and folders
Author: Rowan Chapman @rchapman83
"""
# --- Import Pythons core modules only ---
import os
import sys
import time
import logging
import logging.config

def remove(path):
    """
    The remove function is very basic. It checks if the path that is passed in is a directory or not and
    attempts to delete the dir or files.
    """
    if os.path.isdir(path):
        try:
            os.rmdir(path)
            logger.info('Removing folder: ' + path)
        except OSError:
            logger.error('Unable to remove folder: %s' + path)
            print('Unable to remove folder')
    else:
        try:
            if os.path.exists(path):
                os.remove(path)
                logger.info('Removing filename: ' + path)
        except OSError:
            logger.error('Unable to remove file: %s' + path)
            print('Unable to remove file')

def cleanup(number_of_days, path):
    """
    Removes files from the passed in path that are older than or equal
    to the number_of_days(parameter is transformed into seconds).
    Then we subtract that amount from today’s current time(measure in seconds).
    """
    time_in_secs = time.time() - (number_of_days * 24 * 60 * 60)
    """
    topdown is set to false to tell the walk method to traverse the directories from the innermost to the outermost.
    A loop over the files in the innermost folder is kicked off to check the last access time.
    If that time is less than or equal to time_in_secs, then the file is removed.
    Then a check is made on the root dir to see if it contains files. If it doesn’t, the folder is removed.
    """
    for root, dirs, files in os.walk(path, topdown=False):
        for file_ in files:
            full_path = os.path.join(root, file_)
            stat = os.stat(full_path)

            if stat.st_mtime <= time_in_secs:
                remove(full_path)

        if not os.listdir(root):
            remove(root)
# --- Entry point of app  ---
if __name__ == "__main__":
    """
    First up the script creates a log file and loads a logging config file to define handlers and formatters then we create a logger.
    After that we hit the cleanup function which accepts two vars; number of days old a file can be and path to search.
    Logger levels: debug, info, warning, error, critical.
    """
    logf_cur = 'cleanup.log'
    if os.path.isfile(logf_cur):
        print('Logfile found, checking size in Bytes.')
        if os.path.getsize(logf_cur) >= 1000000:
            try:
                print('Deleting old logfiland creating new one.')
                os.remove(logf_cur)
                logf_w = open(logf_cur, 'w')
                logf_w.write('** Start of log **\n')
                logf_w.close()
            except OSError:
                print('Unable to delete logfile.')
                quit()
        else:
            clock = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            logf_a = open(logf_cur, 'a')
            logf_a.write('** Running script & appending to log @ ' + clock + ' **\n')
            logf_a.close()
    else:
        print('No logfile found, creating one.')
        try:
            logf_w = open(logf_cur, 'w')
            logf_w.write('** Start of log **\n')
            logf_w.close()
        except OSError:
            print('Unable to create logfile.')
            quit()

    print('Logging ready, running cleanup process.')
    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger('console')

    days, path = int(sys.argv[1]), sys.argv[2]
    logger.info('Path to be interrogated is: ' + path)
    logger.info('Files older than ' + str(days) + ' days to be removed')
    cleanup(days, path)
