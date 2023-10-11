#just here for reference. This is the old batch pipeline

'''


'''
import datetime
import re
import csv
import os
import sys
import time
import config
import azure.storage.blob as azureblob
import azure.batch.batch_service_client as batch
from azure.common.credentials import ServicePrincipalCredentials
import azure.batch.models as batchmodels


BATCH_NODE_STATES = ['idle', 'rebooting', 'reimaging', 'running', 'unusable', 'creating', 'starting',
                     'waitingForStartTask', 'startTaskFailed', 'unknown', 'leavingPool', 'offline', 'preempted']
BATCH_NODE_BAD_STATES = ['unusable', 'startTaskFailed', 'unknown', 'offline', 'preempted']
BATCH_NODE_TERMINAL_STATES = ['idle', 'unusable', 'startTaskFailed', 'unknown', 'offline', 'preempted']


def wait_for_tasks_to_complete(batch_service_client, job_id, pool_id, timeout):
    """
    Returns list of incomplete tasks or False if tasks are complete.

    :param batch_service_client: A Batch service client.
    :type batch_service_client: `azure.batch.BatchServiceClient`
    :param str job_id: The id of the job whose tasks should be monitored.
    :param timedelta timeout: The duration to wait for task completion. If all
    tasks in the specified job do not reach Completed state within this time
    period, an exception will be raised.
    """
    try:
        timeout_expiration = datetime.datetime.now() + timeout
        print("The pipeline is currently running. Please check the azure portal for the status on this run. Monitoring all tasks for 'Completed' state, timeout in {}..."
              .format(timeout))
        resized = False
        while batch_service_client.pool.exists(pool_id):
            if batch_service_client.pool.get(pool_id).allocation_state == 'steady':
                sys.stdout.flush()
                tasks = batch_service_client.task.list(job_id)

                nodes = get_list_of_active_nodes(batch_service_client, pool_id)
                nodes_to_remove = []
                active_tasks = [task for task in tasks if
                                (task.state == batchmodels.TaskState.active or task.state == batchmodels.TaskState.preparing)]

                for node in nodes:
                    node_state = node.state
                    if active_tasks:
                        if node_state in BATCH_NODE_BAD_STATES:
                            print("Node %s shutting down with state: %s" % (node.id, node_state))
                            nodes_to_remove.append(node.id)
                    elif node_state in BATCH_NODE_TERMINAL_STATES:
                            print("Node %s shutting down with state: %s" % (node.id, node_state))
                            nodes_to_remove.append(node.id)

                if len(nodes_to_remove) > 0:
                    node_remove_param = batchmodels.NodeRemoveParameter(node_list=nodes_to_remove,
                                                                    node_deallocation_option='terminate')
                    batch_service_client.pool.remove_nodes(pool_id, node_remove_param)
                    time.sleep(5)
                    resized = True

                tasks = batch_service_client.task.list(job_id)
                incomplete_tasks = [task for task in tasks if
                                    task.state != batchmodels.TaskState.completed]
                failed_tasks = [task for task in tasks if
                                    task.execution_info.result == 'failure']
                if resized and (len(nodes) == 0):
                    print("Pool resized to 0 nodes")
                    #batch_service_client.pool.delete(pool_id) moving responsibility to server
                    if incomplete_tasks:
                        print("The following {} tasks are still incomplete:".format(len(incomplete_tasks)))
                        for incomplete_task in incomplete_tasks:
                            print(incomplete_task.id)
                        return incomplete_tasks
                    if failed_tasks:
                        print("The following {} tasks have failed:".format(len(failed_tasks)))
                        for failed_task in failed_tasks:
                            print(failed_task.id)
                        return failed_tasks
                    return False

                if not incomplete_tasks and not failed_tasks:
                    print("All tasks completed in pool")
                    return False
            time.sleep(15)
        if incomplete_tasks:
            print("The following {} tasks are still incomplete:".format(len(incomplete_tasks)))
            for incomplete_task in incomplete_tasks:
                print(incomplete_task.id)
            return incomplete_tasks
        if failed_tasks:
            print("The following {} tasks have failed:".format(len(failed_tasks)))
            for failed_task in failed_tasks:
                print(failed_task.id)
            return failed_tasks
        return False

        print()
        print("ERROR: Tasks did not reach 'Completed' state within timeout period of " + str(timeout))
    except Exception as err:
        print_batch_exception(err)
        if query_yes_no('Delete job?') == 'yes':
            batch_service_client.job.delete(job_id)

        if query_yes_no('Delete pool?') == 'yes':
            batch_service_client.pool.delete(pool_id)
        raise


def get_list_of_active_nodes(batch_service_client, pool_id):
    nodes = list(batch_service_client.compute_node.list(pool_id))
    return nodes

