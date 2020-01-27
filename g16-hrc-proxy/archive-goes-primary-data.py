import json
import requests
from Chandra.Time import DateTime

URL = 'https://services.swpc.noaa.gov/json/goes/primary/'

def main():
    """
    Archive the primary GOES data. Run in a crontab once per week.
    Before installing:
    1. Decide on the location of the archive and update line 26
    2. Uncomment lines 26-27
    3. Delete line 25
    """
    datafiles = ['differential-protons-7-day', 'integral-protons-7-day',
                 'differential-electrons-7-day', 'integral-electrons-7-day',
                 'integral-proton-fluence-7-day', 'integral-electron-fluence-7-day',
                 'xrays-7-day']
    
    for datafile in datafiles:
        json_url = requests.get(f'{URL}/{datafile}.json')
        data = json_url.json()
        today = DateTime().fits
        filename = f'{datafile}-{today[:10]}.json'
        print(filename)
        # with open(filename, 'w') as f:
        #     json.dump(data, f)
    
    
if __name__ == "__main__":
    main()
