
# This Old Garmin

This is an app to push new GPX tracks from my old (unsupported) Garmin eTrek to Strava.


## Instructions

TODO


## Dev notes

The program runs permanently in the background.  It constantly scans drive letters for a drive that has the correct file.  The directory and file we are looking for is X:\Garmin\GPX\Current\Current.gpx. 

In the file Current.gpx (which is XML), we are looking for tracks.  The overall structure is:

```
<?xml><gpx>
<metadata>
...
</metadata>
<trk>
<name>Current Track: 02 SEP 2018 09:52</name>
<extensions>...</extensions>
<trkseg><trkpt ...></trkpt>
</trkseg>
</trk>
</gpx>
```

We are looking for `trk` sections that are not uploaded yet.

I think it will work best to upload any track that was not yet uploaded.  If the track does not belong on Strava, it can always be deleted.  Strava has checking and can flag bad tracks (like those for car driving).

It is not clear how the app will know which tracks were uploaded versus those that were not.  Strava has the date and time for every activities and the tracks in the GPX files have the same.  Maybe the app can query the date and time of the last activity on Strava and upload all tracks that come after that.  Alternatively, the app could note the uploads in a configuration file and use this information instead.  Clearly, checking Strava is superior because the app can be moved or used from more than a single host.


### TODO

Ctrl-C needs to work even when the app is waiting for the authorization code.  The HTTP server thread remains running and blocks Ctrl-C from shutting down the app.
