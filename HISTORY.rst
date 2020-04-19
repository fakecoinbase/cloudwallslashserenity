.. :changelog:

Release History
---------------

0.0.3 (2020-04-19)
+++++++++++++++++++

- Added new generic FeedHandler API
- Implemented PhemexFeedHandler
- Converted Phemex tick upload job to Kubernetes CronJob
- Moved Tickstore and Journal from serenity.mdrecorder to serenity.tickstore
- Critical fix for buy/sell code mapping in Phemex feed
- Upgraded to pandas 1.0.3

0.0.2 (2020-04-13)
+++++++++++++++++++

- Fixed dependencies in setup.py

0.0.1 (2020-04-13)
+++++++++++++++++++

- Initial implementation
