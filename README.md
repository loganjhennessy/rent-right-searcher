# Rent Right Searcher

Rent right searcher is a Kubernetes CronJob written in Python that finds rental listings to scrape.

The CronJob runs on a regular schedule, publishing jobs to a PubSub topic. Downstream, another micro-service listens on
a subscription to the PubSub topic and does the scraping.

## TODO

1. Unit tests