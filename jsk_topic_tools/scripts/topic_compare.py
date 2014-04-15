#!/usr/bin/env python
# -*- coding: utf-8 -*-

import roslib; roslib.load_manifest("jsk_topic_tools")
import roslib.message
import rospy
import os, sys
import time
import traceback


class ROSTopicCompare(object):
    subscriberArray = []
    topicSizesArray = []
    topicTimesArray = []
    scaleType = 0
    captureSize = 100

    def __init__(self, scale="KB", captureSize=100):
        if scale == "B":
            self.scaleType = 1
        elif scale == "KB":
            self.scaleType = 2
        elif scale == "MB":
            self.scaleType = 3

        self.captureSize = captureSize

    def _gen_callback(self):
        self.topicSizesArray.append([])
        self.topicTimesArray.append([])
        _topic_num = len(self.subscriberArray)
        def _callback(msg):
            topic_num = _topic_num
            try:
                t = time.time()
                self.topicTimesArray[topic_num].append(t)
                self.topicSizesArray[topic_num].append(len(msg._buff))
                assert(len(self.topicTimesArray[topic_num]) == len(self.topicSizesArray[topic_num]))
                if len(self.topicTimesArray[topic_num]) > self.captureSize:
                    self.topicTimesArray[topic_num].pop(0)
                    self.topicSizesArray[topic_num].pop(0)
            except:
                traceback.print_exc()
        return _callback

    def registerTopic(self, topic_name):
        sub = rospy.Subscriber(topic_name, rospy.AnyMsg, self._gen_callback())
        self.subscriberArray.append(sub)
        print "subscribed as %d: %s" % (len(self.subscriberArray)-1, topic_name)

    def printBandWidth(self):
        current_time = time.time()
        print ""
        print "No.\tavg/sec\t\tavg/msg\t\tmin/msg\t\tmax/msg\t\tquant."
        for i in range(len(self.subscriberArray)):
            try:
                n = len(self.topicTimesArray[i])
                start_time = self.topicTimesArray[i][0]
                total_bytes = sum(self.topicSizesArray[i])
                bytes_per_sec = 1.0 * total_bytes / (current_time - start_time)
                bytes_per_msg = total_bytes / n
                max_size = max(self.topicSizesArray[i])
                min_size = min(self.topicSizesArray[i])
                res = [bytes_per_sec, bytes_per_msg, min_size, max_size]

                if self.scaleType == 1: # B
                    bps, bpm, ms, Ms = ["%.2fB" % v for v in res]
                elif self.scaleType == 2: # KB
                    bps, bpm, ms, Ms = ["%.2fKB" % (v/1000) for v in res]
                elif self.scaleType == 3: # MB
                    bps, bpm, ms, Ms = ["%.2fMB" % (v/1000000) for v in res]
                else:
                    raise "error: invalid scale type"
                    quit()

                print "%d\t%s\t%s\t%s\t%s\t%d" % (i, bps, bpm, ms, Ms, n)
            except:
                pass

def onShutdown():
    i = 0
    print "subscribed topic:"
    for sub in tc.subscriberArray:
        print "%d: %s" % (i, sub.name)
        i += 1

def fullUsage():
    print "[Usage] rosrun jsk_topic_tools topic_compare.py [Option] <topic_name_1>..<topic_name_n>"
    print "[Option]"
    print "-h: full usage"
    print "-b: show value as bytes"
    print "-m: show value as megabytes"

if __name__ == '__main__':
    # check if valid argument
    if len(sys.argv) < 2:
        print "[Usage] rosrun jsk_topic_tools topic_compare.py <topic_name_1>..<topic_name_n>"
        quit()

    rospy.init_node("topic_compare")

    # check options
    if "-h" in sys.argv:
        fullUsage()
        quit()
    elif "-b" in sys.argv:
        tc = ROSTopicCompare("B")
    elif "-m" in sys.argv:
        tc = ROSTopicCompare("MB")
    else:
        tc = ROSTopicCompare()

    for name in sys.argv[1:]:
        if name[0] != "/":
            continue
        tc.registerTopic(name)

    rospy.on_shutdown(onShutdown)

    while not rospy.is_shutdown():
        rospy.rostime.wallsleep(1.0)
        tc.printBandWidth()