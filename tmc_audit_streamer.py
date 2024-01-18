#!/usr/bin/env python3
# Andrew Wood (andrew.wood@broadcom.com)
# This is a proof of concept, no results are guaranteed

import logging
import os
import requests
import signal
import sys
import time
import threading

CSP_AUTHORIZE_TOKEN_URL = "https://console.cloud.vmware.com/csp/gateway/am/api/auth/api-tokens/authorize"

csp_token = os.getenv('CSP_TOKEN')
tmc_url = os.getenv('TMC_URL')
log_file_path = os.getenv('LOG_FILE_PATH')

if not csp_token or not tmc_url or not log_file_path:
    logging.critical("Error: Required environment variables CSP_TOKEN, TMC_URL, and/or LOG_FILE_PATH are not set.")
    sys.exit(1)


def get_log_level():
    level = os.getenv('LOG_LEVEL', 'INFO').upper()
    return {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'WARN': logging.WARNING,
        'ERROR': logging.ERROR,
        'FATAL': logging.CRITICAL,
        'CRITICAL': logging.CRITICAL
    }.get(level, logging.INFO)


# Setting the logging level based on the environment variable
logging.basicConfig(level=get_log_level())


class UTCFormatter(logging.Formatter):
    converter = time.gmtime

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = time.strftime(datefmt, ct)
        else:
            s = time.strftime("%Y-%m-%dT%H:%M:%S", ct)
        return s


# Function to apply the UTCFormatter to all handlers of a logger
def set_utc_formatter_to_logger(logger):
    utc_formatter = UTCFormatter(fmt='%(asctime)s: %(levelname)s: %(message)s',
                                 datefmt='%Y-%m-%dT%H:%M:%S')
    for handler in logger.handlers:
        handler.setFormatter(utc_formatter)


logging.basicConfig(level=logging.DEBUG)
root_logger = logging.getLogger()
set_utc_formatter_to_logger(root_logger)
requests_logger = logging.getLogger('requests')
set_utc_formatter_to_logger(requests_logger)

logging.info("Starting...")
log_file_lock = threading.Lock()


def signal_handler(sig, frame):
    logging.warning('Interrupt received, shutting down...')
    sys.exit(0)


def write_log(data, max_size=10 * 1024 * 1024, sleep_time=8):  # 10 MB, 8 seconds
    with log_file_lock:
        # Check if the current log file is over the size limit
        if os.path.exists(log_file_path) and os.path.getsize(log_file_path) >= max_size:
            logging.debug(f"Waiting {sleep_time}s to ensure Fluentd has read the data")
            # Wait to ensure Fluentd has read the data
            time.sleep(sleep_time)

            # Truncate the file
            open(log_file_path, 'w').close()

        # Write the data to the log file
        with open(log_file_path, 'a') as file:
            file.write(data + '\n')


def call_event_stream_api():
    # get access token using csp_token
    access_token = get_access_token()

    # index to trim suffix in url. everything after .com will be removed
    try:
        trim_index = tmc_url.index('.com') + 4
    except:
        logging.error('Invalid tmc_url. Please try again.')
        return
    # trim url and add stream api suffix
    url = tmc_url[:trim_index] + '/v1alpha1/events/stream'

    retry_delay_init = retry_delay = 10  # Starting delay, can increase on each retry
    max_retries_init = max_retries = 5  # Maximum number of retries

    # stream events from response
    logging.info("Attempting to read from tmc event stream...")
    while True:
        try:
            response = requests.get(
                url,
                headers={'Authorization': 'Bearer %s' % access_token},
                stream=True,
                timeout=(5, 60)
            )
            # Check if the request was successful
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        logging.info(f"Read: {decoded_line}")
                        if max_retries != max_retries_init:  # we've read a line successfully, so we'll reset everything
                            logging.debug(f"Resetting retries to {max_retries_init} and delay to {retry_delay_init}s")
                            max_retries = max_retries_init
                            retry_delay = retry_delay_init
                        write_log(decoded_line)
            elif response.status_code == 401:
                logging.warning("Error: Received status code 401. Re-authenticating and waiting 15s for a cooldown.")
                time.sleep(15)  # Wait for a bit before continuing
                access_token = get_access_token()
            else:
                logging.warning(f"Error: Received status code {response.status_code}")
                logging.info(f"Assuming you're being rate limited. Sleeping for 120s")
                time.sleep(120)  # Adjust the sleep time as needed

        except requests.exceptions.ChunkedEncodingError as e:
            logging.warning(f"Invalid chunk encoding {e}")
            if max_retries > 0:
                logging.debug(f"Going to retry. Waiting for {retry_delay}s before trying again.")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                max_retries -= 1
                continue
            else:
                logging.warning(f"Max retries of {max_retries_init} reached, terminating.")
                break
        except requests.exceptions.RequestException as e:
            logging.warning(f"Request failed: {e}")
            time.sleep(120)  # Adjust the sleep time as needed
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            time.sleep(120)  # Adjust the sleep time as needed
        except:
            continue


def get_access_token():
    url = CSP_AUTHORIZE_TOKEN_URL
    header = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {'refresh_token': csp_token}
    response = requests.post(url, data=payload, headers=header)

    try:
        access_token = response.json()['access_token']
    except:
        logging.error('Invalid csp_token. Please try again.')
        return

    return access_token


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    call_event_stream_api()
