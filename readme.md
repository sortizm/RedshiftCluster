# Redshift cluster
Simple script to create/delete and check status of a cluster.

The script is based on the configuration found in aws.cfg

## Get started
1. Install __boto3__, __click__, __psycopg2__
2. Rename _aws.cfg.template_ as _aws.cfg_ and set the variables from the credentials and cluster sections.
3. Run
```bash
./cluster.py up     # to create the cluster
./cluster.py status # to get the cluster information
./cluster.py down   # to delete the cluster
```
