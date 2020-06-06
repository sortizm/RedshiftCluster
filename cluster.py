#!/usr/bin/env python

from configparser import ConfigParser
from time import sleep

import boto3
import click
import psycopg2

SLEEP_TIME_SECONDS = 20


@click.group()
@click.pass_context
def cluster(ctx):
    """Start/Destroy the Redshift Cluster, or display status"""
    config = ConfigParser()
    config.read('aws.cfg')
    redshift = boto3.client('redshift',
                            region_name=config['cluster']['region'],
                            aws_access_key_id=config['credentials']['aws_key'],
                            aws_secret_access_key=config['credentials']['aws_secret']
                            )
    ctx.obj = {
        'redshift': redshift,
        'config': config,
        'cluster_id': config['cluster']['cluster_identifier']
    }


@cluster.command()
@click.pass_context
def up(ctx):
    """Starts redshift cluster"""
    redshift = ctx.obj['redshift']
    config = ctx.obj['config']['cluster']
    iam_roles = [x for _, x in ctx.obj['config']['iam_roles'].items()]

    redshift.create_cluster(
        ClusterType=config['cluster_type'],
        NodeType=config['node_type'],
        NumberOfNodes=int(config['nodes']),
        DBName=config['db'],
        Port=int(config['db_port']),
        ClusterIdentifier=config['cluster_identifier'],
        MasterUsername=config['db_user'],
        MasterUserPassword=config['db_password'],
        IamRoles=iam_roles
    )

    wait_for_cluster_availability(redshift, config['cluster_identifier'], 'Available')
    run_initialisation_scripts(redshift, config, ctx.obj['config']['sql'])
    print('Cluster initialised')


def wait_for_cluster_availability(redshift, cluster_id, availability):
    response_availability = None
    while response_availability != availability:
        print(f"Waiting for availability '{availability}' but it is '{response_availability}'")
        response = redshift.describe_clusters(ClusterIdentifier=cluster_id)
        response_availability = response['Clusters'][0]['ClusterAvailabilityStatus']
        sleep(SLEEP_TIME_SECONDS)


def run_initialisation_scripts(redshift, config, sql_scripts):
    host = get_host(redshift, config['cluster_identifier'])
    for name, script in sql_scripts.items():
        run_sql_script(name,
                       script,
                       config['db_user'],
                       config['db_password'],
                       host,
                       config['db_port'],
                       config['db']
                       )


def get_host(redshift, cluster_id):
    response = redshift.describe_clusters(ClusterIdentifier=cluster_id)
    return response['Clusters'][0]['Endpoint']['Address']


def run_sql_script(key, script, user, password, host, port, db):
    print(f"Running SQL script '{key}': {script}")
    con = psycopg2.connect(f"postgresql://{user}:{password}@{host}:{port}/{db}")
    con.set_isolation_level(0)
    cur = con.cursor()
    with open(script, 'r') as s:
        cur.execute(s.read())
        con.commit()


@cluster.command()
@click.pass_context
def down(ctx):
    """Deletes redshift cluster without creating snapshot"""
    redshift = ctx.obj['redshift']
    cluster_id = ctx.obj['cluster_id']

    redshift.delete_cluster(
        ClusterIdentifier=cluster_id,
        SkipFinalClusterSnapshot=True)

    wait_for_deletion(redshift, cluster_id)
    print('Cluster was deleted')


def wait_for_deletion(redshift, cluster_id):
    while True:
        print(f"Waiting for deletion of '{cluster_id}'")
        try:
            redshift.describe_clusters(ClusterIdentifier=cluster_id)
        except redshift.exceptions.ClusterNotFoundFault:
            return
        sleep(SLEEP_TIME_SECONDS)


@cluster.command()
@click.pass_context
def status(ctx):
    """Shows status of the redshift cluster"""
    redshift = ctx.obj['redshift']
    cluster_id = ctx.obj['cluster_id']
    try:
        response = redshift.describe_clusters(
            ClusterIdentifier=cluster_id
        )
    except redshift.exceptions.ClusterNotFoundFault:
        print(f"Cluster not found '{cluster_id}'")
        return
    print_status(response['Clusters'][0], ctx.obj['config']['status'])


def print_status(cluster_response, status_config):
    for var, val in status_config.items():
        value = None
        try:
            for section in val.split(','):
                if not value:
                    value = cluster_response[section]
                else:
                    value = value[section]
        except KeyError:
            value = "Value not found"
        print(f"{var} : {value}")


if __name__ == '__main__':
    cluster()
