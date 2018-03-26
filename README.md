# Rent Right Scraper

Rent right scraper is a Kubernetes CronJob and Deployment that work together to get the data necessary for Rent Right.

The CronJob runs on a regular schedule, publishing jobs to a PubSub topic. The Deployment listens on a subscription to that topic and performs a scraping job for each message, placing the data in Google Datastore, where it can be used by downstream applications.