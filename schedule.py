time = 0
end_time = 1000000
frame_count = 0
frame_delay = 0
class Queue(list):
    def __init__(self):
        self.current = None
        self.next_time = 0
    def schedule(self, time):
        result = None
        if self.next_time == time:
            #print id(self), "finished", time
            if self.current:
                result = self.pop(0)
                result.finish_times.append(time)
                self.current = None

        if self.next_time <= time and len(self) and not self.current:
            self.current = self[0]
            #print time, self.next_time, id(self), self, self.current.length
            self.next_time = self.current.length.pop(0) + time
            #print "sched next", self.next_time
        return result
    def append(self, frame):
        global time
        frame.start_times.append(time)
        super(Queue, self).append(frame)
    
class Frame:
    def __init__(self, start_time, length):
        self.start_time = start_time
        self.length = length
        self.finish_times = []
        self.start_times = []

main_thread = Queue()
pending_composite = []
compositor = Queue()
renderer = Queue()

COMPOSITOR_SCHEDULE_ON_VSYNC = True

total_live_frames = 0
frame_times = []
composite_times = []
mt_times = []
render_times = []
while time < end_time:
    if time % 16666 == 0:
        # vsync

        
        if len(pending_composite):
            if len(pending_composite) > 1:
                print "skipping frames for composite"
            if len(compositor) == 0:
                compositor.append(pending_composite.pop())
                pending_composite = []

        MAX_QUEUE_LENGTH = 1
        # back pressure -- don't let the queue grow too long
        #if len(main_thread) <= MAX_QUEUE_LENGTH:
        if total_live_frames <= 1:
            main_thread.append(Frame(time, [2*1000, 8*1000, 12*1000]))
            total_live_frames += 1
        else:
            print "skipped scheduling frame"
    finished_frame = main_thread.schedule(time)

    if finished_frame:
        mt_times.append((finished_frame.start_times[-1], finished_frame.finish_times[-1]))
        if COMPOSITOR_SCHEDULE_ON_VSYNC:
            pending_composite.append(finished_frame)
        else:
            compositor.append(finished_frame)
  
    finished_frame = compositor.schedule(time)

    if finished_frame:
        composite_times.append((finished_frame.start_times[-1], finished_frame.finish_times[-1]))
        total_live_frames -= 1
        renderer.append(finished_frame)

    finished_frame = renderer.schedule(time)

    if finished_frame:
        render_times.append((finished_frame.start_times[-1], finished_frame.finish_times[-1]))
        frame_count += 1
        frame_delay += time - finished_frame.start_time
        frame_times.append((finished_frame.start_time, time))
        #print time - finished_frame.start_time
      
    time += 1

print frame_count
print 1000*1000. * frame_count / (end_time  * 1.0), "fps"
print frame_delay / (frame_count * 1000.0), "ms"

f = open("out.html", "w+")
print >> f, "<div style='position: relative; height:40px'>"
print >> f, "<style>.frame:hover { background: red } .frame { background: black } .vsync { background: blue }</style>"
def print_times(times):
    print >> f, "<div style='position: relative; height:42px'>"
    for frame in times:
        print >> f, "<div class='frame' style='position: absolute; left: %fpx; width: %fpx; height:40px'></div>" % (frame[0]/1000., (frame[1]-frame[0])/1000.)
    print >> f, "</div>"

print_times(frame_times)
print_times(mt_times)
print_times(composite_times)
print_times(render_times)

vsync_time = 0
while vsync_time < end_time:
    if vsync_time % 16666 == 0:
        print >> f, "<div class='vsync' style='position: absolute; left: %fpx; top: 0px; width: 1px; height:800px'></div>" % (vsync_time/1000.)
    vsync_time += 1

print >> f, "</div>"

