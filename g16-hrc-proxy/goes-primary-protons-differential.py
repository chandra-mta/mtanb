import numpy as np
import json
import requests
from astropy.table import Table
from Chandra.Time import DateTime
from astropy.io import ascii

URL = 'https://services.swpc.noaa.gov/json/goes/primary/differential-protons-6-hour.json'

def fetch_goes_data():
    """
    Fetch the 6-hour file
    """
    json_url = requests.get(URL)
    data = json_url.json()
    t = Table(data)
    return t


def write_html(dat):
    """
    Return an html string containing the website code
    """
    
    string = f"""
<!DOCTYPE html>
<html>
<head>
   <meta charset="UTF-8">
   <title>GOES-16 Data: Differential </title>
</head>
<body style="width:95%;margin-left:10px; margin-right;10px;background-color:#FAEBD7;font-family:Georgia, "Times New Roman", Times, serif">

<div style='float:right;'>
<a href="../../sot.html">SOT home page</a>
<br/>
<a href="../index.html">Radiation Main Page</a>
</div>

<h2 style='margin-left:auto;margin-right:auto;'>REALTIME GOES-16 OBSERVATIONS: Differential</h2>
<br/> <br/>

<pre>
                            Most Recent GOES 16 Observations
                            Proton Flux particles/cm2-s-ster-MeV
<br/>
{'<br/>'.join(dat.pformat(max_lines=-1, max_width=-1))}
<br/>

</pre>

<hr/>

<div style='text-align:center;padding-top:10px;padding-bottom:20px;'>
<img src="http://services.swpc.noaa.gov/images/satellite-env.gif" style="margin-left:auto;margin-right:auto;">
</div>

<hr/>

<div style='float:right;'>
<a href="../../sot.html">Back to the SOT home page</a>
<br/>
<a href="../index.html">Back to Radiation Main Page</a>
</div>

<a href="https://www.swpc.noaa.gov/">
<img alt="Space Environment Center" src="../Logos/ssel.gif">
<br/>
Space Environment Center
</a>

<hr/>

<p style='padding-top:10px;padding-bottom:20px;'>
<a href="mailto:swolk@cfa.harvard.edu">Email problems to: Scott Wolk</a>
(<a href="https://hea-www.harvard.edu/~swolk/">Scott Wolk</a>) <br/>
...it is all his fault <br/>
</p>


<script>
setTimeout('location.reload()',100000)
</script>

</body>
</html>
"""
    
    return string


def main():
    """
    Fetch the GOES data. Manupulate and reorganize the data to get
    the most recent chunk of 2 hours of data with the format appropriate
    for the display on the MTA website. Write an updated MTA website with
    the most recent 2 hours of data.
    """

    t = fetch_goes_data()

    # Find the most recent 2 hours of data, t_new
    time_most_recent_g16 = t['time_tag'][-1][:-1]
    time_start_lookback = DateTime(DateTime(time_most_recent_g16).mjd - 2./24, format='mjd')
    now = DateTime().fits
    ok = np.array([DateTime(time_tag[:-1]).mjd > DateTime(time_start_lookback).mjd for time_tag in t['time_tag']], dtype=bool)
    t_new = t[ok]

    # Manipulate energy bands to create a temporaty energy table,
    # energy_tab, in order to sort by the lower energy channel and
    # to convert the energy labels from keV to MeV
    energy_bands = set(t_new['energy'])

    rows = []
    for energy_band_keV in energy_bands:
        tmp = energy_band_keV.split(' ')
        items = tmp[0].split('-')
        energy_lower = float(items[0]) / 1000  # convert from keV to MeV
        energy_upper = float(items[1]) / 1000  # convert from keV to MeV
        energy_band_MeV = f'{energy_lower}-{energy_upper} MeV'
        rows.append({'energy_keV': energy_band_keV,
                     'energy_MeV': energy_band_MeV,
                     'energy_lower': energy_lower})

    energy_tab = Table(rows)
    energy_tab.sort('energy_lower')

    # Build a reorganized table, dat, with the most recent 2 hours of data
    fluxes = {}
    fluxes = dict.fromkeys(energy_tab['energy_MeV'], [])
    for energy_band_keV, energy_band_MeV in zip(energy_tab['energy_keV'],
                                            energy_tab['energy_MeV']):
        ok = t_new['energy'] == energy_band_keV
        fluxes[energy_band_MeV] = np.array(t_new[ok]['flux'] * 1000) # per MeV not keV

    # Get and add a column with time tags
    ok = t_new['energy'] == t_new['energy'][0]
    time_tags = t_new['time_tag'][ok]
    names = ['time_tags'] + list(fluxes.keys())
    dat = Table(fluxes)
    dat.add_column(time_tags, name='time_tag', index=0)

    # Format fluxes
    for colname in dat.colnames:
        if 'MeV' in colname:        
            dat[colname].format = '.5f'

    # Write html
    string = write_html(dat)
    with open(f"./goes-primary-proton-differential.html", "w") as htmlfile:
        htmlfile.write(string)


if __name__ == "__main__":
    main()
