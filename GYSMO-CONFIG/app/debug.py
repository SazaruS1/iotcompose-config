#import logging
import os
import time

from dotenv import load_dotenv

load_dotenv()

#logging.basicConfig(  # filename='logs/caubios.log',
#    level=logging.WARNING,
#    format='%(asctime)s - %(name)s - %(threadName)s -  %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
#
#logger = logging.getLogger(__name__)

print("Debug information for GYSMO...")


for key, value in os.environ.items():
    print(f"{key}: {value}")



counter = 1
print(f"{counter} mouton")
while True:
    counter += 1
    time.sleep(1)
    print(f"{counter} moutons")