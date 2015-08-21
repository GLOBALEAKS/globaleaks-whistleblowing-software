# -*- coding: utf-8 -*-
#
#   statistics_sched
#   ****************
#
#  Statistics works collecting every N-th minutes the amount of important
#  operations happened
#
#  This impact directly the statistics collection for OpenData purpose and
#  private information.
#  The anomaly detection based on stress level measurement.

import os
from twisted.internet import defer

from globaleaks.anomaly import Alarm, compute_activity_level
from globaleaks.jobs.base import GLJob
from globaleaks.settings import GLSetting, transact
from globaleaks.models import Stats, Anomalies
from globaleaks.utils.utility import log, datetime_now, datetime_null


def get_workingdir_space():
    statvfs = os.statvfs(GLSetting.working_path)
    free_bytes = statvfs.f_frsize * statvfs.f_bavail
    total_bytes = statvfs.f_frsize * statvfs.f_blocks
    return free_bytes, total_bytes

def get_ramdisk_space():
    statvfs = os.statvfs(GLSetting.ramdisk_path)
    free_bytes = statvfs.f_frsize * statvfs.f_bavail
    total_bytes = statvfs.f_frsize * statvfs.f_blocks
    return free_bytes, total_bytes


@transact
def save_anomalies(store, anomalies_list):
    anomalies_counter = 0
    for anomaly in anomalies_list:
        anomalies_counter += 1
        anomaly_date, anomaly_desc, alarm_raised = anomaly

        newanom = Anomalies()
        newanom.alarm = alarm_raised
        newanom.date = anomaly_date
        newanom.events = anomaly_desc
        store.add(newanom)

    if anomalies_counter:
        log.debug("save_anomalies: Saved %d anomalies collected during the last hour" %
                  anomalies_counter)


class AnomaliesSchedule(GLJob):
    """
    This class check for Anomalies, using the Alarm() object
    implemented in anomaly.py
    """
    name = "Anomalies"

    @defer.inlineCallbacks
    def operation(self):
        """
        Every X seconds is checked if anomalies are happening
        from anonymous interaction (submission/file/comments/whatever flood)
        If the alarm has been raise, logs in the DB the event.
        """
        yield compute_activity_level()


def get_anomalies():
    anomalies = []
    for when, anomaly_blob in dict(GLSetting.RecentAnomaliesQ).iteritems():
        anomalies.append(
            [when, anomaly_blob[0], anomaly_blob[1]]
        )
    return anomalies

def clean_anomalies():
    GLSetting.RecentAnomaliesQ = {}

def get_statistics():
    statsummary = {}

    for descblob in GLSetting.RecentEventQ:
        if 'event' not in descblob:
            continue

        statsummary.setdefault(descblob['event'], 0)
        statsummary[descblob['event']] += 1

    return statsummary

@transact
def save_statistics(store, start, end, activity_collection):
    newstat = Stats()
    newstat.start = start
    newstat.summary = dict(activity_collection)
    newstat.free_disk_space = get_workingdir_space()[0]
    store.add(newstat)

    if activity_collection:
        log.debug("save_statistics: Saved statistics %s collected from %s to %s" %
                  (activity_collection, start, end))

class StatisticsSchedule(GLJob):
    """
    Statistics just flush two temporary queue and store them
    in the database.
    """
    name = "Statistics Sched"
    collection_start_datetime = datetime_null()

    def __init__(self):
        self.collection_start_datetime = datetime_now()
        GLJob.__init__(self)

    @classmethod
    def reset(cls):
        GLSetting.RecentEventQ = []
        GLSetting.RecentAnomaliesQ = {}

    @defer.inlineCallbacks
    def operation(self):
        """
        executed every 60 minutes
        """

        # ------- Anomalies section ------
        anomalies_to_save = get_anomalies()
        yield save_anomalies(anomalies_to_save)
        clean_anomalies()
        # ------- END of Anomalies section ------

        current_time = datetime_now()
        statistic_summary = get_statistics()

        yield save_statistics(StatisticsSchedule.collection_start_datetime,
                              current_time, statistic_summary)

        StatisticsSchedule.reset()
        StatisticsSchedule.collection_start_datetime = current_time

        log.debug("Saved stats and time updated, keys saved %d" %
                  len(statistic_summary.keys()))


class ResourcesCheckSchedule(GLJob):
    """
    Resources Check Scheduleis a job that verify the available
    resources in the GlobaLeaks box.
    At the moment is implemented only a monitor for the disk space,
    because the files that might be uploaded depend directly from
    this resource.
    """
    name = "Resources Check"

    def operation(self):
        free_disk_bytes, total_disk_bytes = get_workingdir_space()
        free_ramdisk_bytes, total_ramdisk_bytes = get_ramdisk_space()

        alarm = Alarm()
        alarm.check_disk_anomalies(free_disk_bytes, total_disk_bytes, free_ramdisk_bytes, total_ramdisk_bytes)
