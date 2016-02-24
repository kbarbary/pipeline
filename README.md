Pipeline 2.0
============

*Experimental next-gen Nearby Supernova Factory pipeline*

Raw Data
--------

- **Images** Located on HPSS in tar files, with one tar file per night of data.
  Files are found in `/nersc/projects/snfactry/raw/YY/DDD.tar` and can be unpacked with the
  htar command. Files were copied from CC. Note that there are occasionally extra junk files
  on HPSS that do not exist at CC. HPSS should contain a superset of the files at the CC.

Scripts
-------

- `check-raw-data`: Checks that all files at CC are present on HPSS.
