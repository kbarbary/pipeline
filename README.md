Pipeline 2.0
============

*Experimental next-gen Nearby Supernova Factory pipeline*

Raw Data
--------

![pipeline dataflow](https://cdn.rawgit.com/snfactory/pipeline/master/pipeline.svg)

- **Image & Log Data:** Copied from CC using rsync. Note that there
  are occasionally extra junk files on HPSS that do not exist at
  CC. HPSS should contain a superset of the files at the CC. (These
  files are additionally backed up to the HPSS tape system.)

- **Weather:** Weather data from Mauna Kea Weather Center is used. Files
  are synced from a public site to `raw/weather`.

- **IAU Names:** The [IAU Supernova HTML
    page](http://www.cbat.eps.harvard.edu/lists/Supernovae.html) is
    synced to `raw/iauc`.

- **Dust Maps:** The Schlegel, Finkbeiner & Davis (1998) dust maps have been
  copied into `raw/dust`.

- **Calibration Data**


Scripts
-------

Run `<cmd> -h` or `<cmd> --help` for usage info for each script.

- `check-raw-data`: Checks that all files at CC are present on HPSS.
- `pull-raw-data`: Pull files from CC to project.
- `archive-raw-data`: Archive files from /project to HPSS.
- `pull-raw-weather and iauc`: Pull weather and IAU webpages to local locations.
