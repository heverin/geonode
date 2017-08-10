import os
from pprint import pprint
import celery
from celery.task import task
from geonode.geoserver.helpers import gs_slurp
from geonode.cephgeo.models import CephDataObject, DataClassification
from geonode.cephgeo.gsquery import nested_grid_update
from django.core.exceptions import ObjectDoesNotExist
from celery.utils.log import get_task_logger
import geonode.settings as settings
from geonode.cephgeo.utils import get_data_class_from_filename
from geonode.cephgeo import ceph_client
from swiftclient.exceptions import ClientException

from geonode.automation.models import AutomationJob, CephDataObjectResourceBase
from geonode.cephgeo.models import LidarCoverageBlock
from celery.decorators import periodic_task
import datetime

logger = get_task_logger("geonode.tasks.ceph_update")


def transform_log_to_list(log):
    log_list = []
    log = log.strip()
    log_list = log.split('\r\n')

    # print 'Log List:', log_list
    logger.info('Cleaned log.')

    return log_list


def get_uid_from_filename(filename):
    name = filename.split('.')[0]
    uid = int((name.split('_')[3].split('U')[-1:]).pop(0))
    print 'UID', uid

    block_object = LidarCoverageBlock.objects.get(uid=uid)

    return block_object


def update_job_status(job):

    if job.status == AutomationJob.STATUS_CHOICES.done_ceph:
        job.status = AutomationJob.STATUS_CHOICES.done_database
        job.save()
        logger.info('Updated job status to %s', AutomationJob.STATUS_CHOICES.done_database)


@task(name='geonode.tasks.ceph_update.ceph_metadata_update')
def ceph_metadata_update():
    """
        NOTE: DOES NOT WORK
          Outputs error 'OperationalError: database is locked'
          Need a better way of making celery write into the database
    """
    print '#' * 10
    print 'Scheduler'
    print '#' * 10

    #: Get from AutomationJob Mode
    job = AutomationJob.objects.get(status=AutomationJob.STATUS_CHOICES.done_ceph)
    uploaded_objects_list = transform_log_to_list(job.ceph_upload_log)

    # Pop first line containing header
    uploaded_objects_list.pop(0)
    """NAME,LAST_MODIFIED,SIZE_IN_BYTES,CONTENT_TYPE,GEO_TYPE,FILE_HASH GRID_REF"""

    # Loop through each metadata element
    csv_delimiter = ','
    objects_inserted = 0
    objects_updated = 0
    gridref_dict_by_data_class = dict()
    logger.info("Encoding {0} ceph data objects".format(
        len(uploaded_objects_list)))
    for ceph_obj_metadata in uploaded_objects_list:
        metadata_list = ceph_obj_metadata.split(csv_delimiter)
        # logger.info("-> {0}".format(ceph_obj_metadata))
        # Check if metadata list is valid
        if len(metadata_list) is 6:
            # try:
            """
                Retrieve and check if metadata is present, update instead if there is
            """
            ceph_obj = None
            for x in metadata_list:
                print 'Metadata', x

            ceph_obj = None
            try:
                ceph_obj = CephDataObjectResourceBase.objects.get(name=metadata_list[0])
                # Commented attributes are not relevant to update
                # ceph_obj.grid_ref = metadata_list[5]
                # ceph_obj.data_class = get_data_class_from_filename(metadata_list[0])
                # ceph_obj.content_type = metadata_list[3]

                ceph_obj.last_modified = metadata_list[1]
                ceph_obj.size_in_bytes = metadata_list[2]
                ceph_obj.file_hash = metadata_list[4]

                ceph_obj.save()

                objects_updated += 1
            except ObjectDoesNotExist:
                ceph_obj = CephDataObjectResourceBase(name=metadata_list[0],
                                                      last_modified=metadata_list[1],
                                                      size_in_bytes=metadata_list[2],
                                                      content_type=metadata_list[3],
                                                      data_class=get_data_class_from_filename(
                    metadata_list[0]),
                    file_hash=metadata_list[4],
                    grid_ref=metadata_list[5],
                    block_uid=get_uid_from_filename(
                    metadata_list[0]))
                ceph_obj.save()

                objects_inserted += 1
            if ceph_obj is not None:
                # Construct dict of gridrefs to update
                if DataClassification.gs_feature_labels[ceph_obj.data_class] in gridref_dict_by_data_class:
                    gridref_dict_by_data_class[DataClassification.gs_feature_labels[
                        ceph_obj.data_class].encode('utf8')].append(ceph_obj.grid_ref.encode('utf8'))
                else:
                    gridref_dict_by_data_class[DataClassification.gs_feature_labels[
                        ceph_obj.data_class].encode('utf8')] = [ceph_obj.grid_ref.encode('utf8'), ]
            # except Exception as e:
            #    print("Skipping invalid metadata list: {0}".format(metadata_list))
        else:
            print("Skipping invalid metadata list (invalid length): {0}".format(
                metadata_list))

    # Pass to celery the task of updating the gird shapefile
    result_msg = "Succesfully encoded metadata of [{0}] of objects. Inserted [{1}], updated [{2}].".format(
        objects_inserted + objects_updated, objects_inserted, objects_updated)

    update_job_status(job)

    print 'GRIDREF DICT BY DATA CLASS'
    print gridref_dict_by_data_class
    # sample
    #{'LAZ':
    #     ['E232N1745', 'E231N1744', 'E231N1745', 'E232N1744', 'E232N1744',
    #     'E230N1745', 'E232N1745', 'E231N1744', 'E231N1745', 'E230N1745']
    #}

    # if update_grid:
    #     result_msg += " Starting feature updates for PhilGrid shapefile."
    #     grid_feature_update.delay(gridref_dict_by_data_class)
    # print result_msg


@task(name='geonode.tasks.ceph_update.ceph_metadata_remove', queue='update')
def ceph_metadata_remove(uploaded_objects_list, update_grid=True, delete_from_ceph=False):
    """
        Remove ceph metadata objects and clear philgrid feature for specified georefs
    """
    # Pop first line containing header
    uploaded_objects_list.pop(0)
    """NAME,LAST_MODIFIED,SIZE_IN_BYTES,CONTENT_TYPE,GEO_TYPE,FILE_HASH GRID_REF"""
    print "Update grid: [" + str(update_grid) + "] Delete Ceph Objects: [" + str(delete_from_ceph) + "]"

    # Loop through each metadata element
    csv_delimiter = ','
    objects_deleted = 0
    objects_not_found = 0
    gridref_dict_by_data_class = dict()
    logger.info("Removing {0} ceph data objects".format(len(uploaded_objects_list)))

    # Create ceph connection
    cephclient = ceph_client.CephStorageClient(settings.CEPH_OGW['default']['USER'], settings.CEPH_OGW[
        'default']['KEY'], settings.CEPH_OGW['default']['LOCATION'])

    for ceph_obj_metadata in uploaded_objects_list:
        metadata_list = ceph_obj_metadata.split(csv_delimiter)
        logger.info("-> {0}".format(ceph_obj_metadata))
        # Check if metadata list is valid
        if len(metadata_list) is 6:
            # try:
            """
                Retrieve and check if metadata is present and delete Ceph Data Object
            """
            ceph_obj = None
            try:
                # Retrieve object
                ceph_obj = CephDataObject.objects.get(name=metadata_list[0])

                # Add object to list for grid removal
                if DataClassification.gs_feature_labels[ceph_obj.data_class] in gridref_dict_by_data_class:
                    gridref_dict_by_data_class[DataClassification.gs_feature_labels[
                        ceph_obj.data_class].encode('utf8')].append(ceph_obj.grid_ref.encode('utf8'))
                else:
                    gridref_dict_by_data_class[DataClassification.gs_feature_labels[
                        ceph_obj.data_class].encode('utf8')] = [ceph_obj.grid_ref.encode('utf8'), ]

                # Delete object
                ceph_obj.delete()
                objects_deleted += 1
            except ObjectDoesNotExist:
                objects_not_found += 1

            # except Exception as e:
            #    print("Skipping invalid metadata list: {0}".format(metadata_list))
        else:
            print("Skipping invalid metadata list (invalid length): {0}".format(
                metadata_list))

    # Pass to celery the task of updating the gird shapefile
    result_msg = "Succesfully deleted metadata of [{0}] of objects. [{1}] objects not found.".format(
        objects_deleted, objects_not_found)
    if update_grid:
        result_msg += " Starting feature deletion for PhilGrid shapefile."
        grid_feature_update.delay(gridref_dict_by_data_class, field_value=0)
    print result_msg


@task(name='geonode.tasks.ceph_update.grid_feature_update', queue='update')
def grid_feature_update(gridref_dict_by_data_class, field_value=1):
    """
        :param gridref_dict_by_data_class: contains mapping of [feature_attr] to [grid_ref_list]
        :param field_value: [1] or [0]
        Update the grid shapefile feature attribute specified by [feature_attr] on gridrefs in [gridref_list]
    """
    x = 1
    for feature_attr, grid_ref_list in gridref_dict_by_data_class.iteritems():
        logger.info("Updating feature attribute [{0}]".format(feature_attr))
        print 'INDEX NESTED GRID UPDATE', x
        nested_grid_update(grid_ref_list, feature_attr, field_value)

        logger.info("Finished task for feature [{0}]".format(feature_attr))


# @task
# def setup_periodic_tasks(sender, **kwargs):

#     sender.add_periodic_task(60.0, ceph_metadata_update(), name='Automation Model Update')
