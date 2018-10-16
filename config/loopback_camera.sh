#!/usr/bin/env bash


sudo modprobe v4l2loopback

gphoto2 --stdout --capture-movie | \
    gst-launch-1.0 fdsrc fd=0 ! decodebin name=dec ! queue ! \
                    videoconvert ! tee ! v4l2sink device=/dev/video1