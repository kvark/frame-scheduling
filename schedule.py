dtime = 0
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
            self.current.start_times.append(time)
            #print time, self.next_time, id(self), self, self.current.length
            self.next_time = self.current.length.pop(0) + time
            #print "sched next", self.next_time
        return result
    def append(self, frame):
        global time
        frame.enqueue_times.append(time)
        super(Queue, self).append(frame)
    
class Frame:
    def __init__(self, start_time, length):
        self.start_time = start_time
        self.length = length
        self.end_time = 0
        self.enqueue_times = []
        self.start_times = []
        self.finish_times = []

main_thread = Queue()
pending_composite = []
compositor = Queue()
renderer = Queue()
scene_builder = Queue()

COMPOSITOR_SCHEDULE_ON_VSYNC = True

total_live_frames = 0
finished_frames = []
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
            main_thread.append(Frame(time, [30*1000, 8*1000, 14*1000, 39*1000]))
            total_live_frames += 1
        else:
            print "skipped scheduling frame"
    finished_frame = main_thread.schedule(time)
    
    if finished_frame:
        scene_builder.append(finished_frame)

    finished_frame = scene_builder.schedule(time)
    
    if finished_frame:
        if COMPOSITOR_SCHEDULE_ON_VSYNC:
            pending_composite.append(finished_frame)
        else:
            compositor.append(finished_frame)
  
    finished_frame = compositor.schedule(time)

    if finished_frame:
        renderer.append(finished_frame)

    finished_frame = renderer.schedule(time)

    if finished_frame:
        total_live_frames -= 1
        frame_count += 1
        frame_delay += time - finished_frame.start_time
        finished_frame.end_time = time
        finished_frames.append(finished_frame)
        #print time - finished_frame.start_time
      
    time += 1


## Output the result of the simulation


print frame_count
print 1000*1000. * frame_count / (end_time  * 1.0), "fps"
print frame_delay / (frame_count * 1000.0), "ms", (frame_delay / (frame_count * 1000.0)) / (1000/60.), "frames"

f = open("out.html", "w+")
print >> f, "<div style='position: relative; height:40px'>"
print >> f, "<style>.frame:hover { background: red } .frame { background: black; color: green; opacity:0.5 } .schedule { background: gray } .vsync { background: blue }</style>"
def print_times(frames):
    frame_no = 0
    for frame in frames:
        top = 0
        print >> f, "<div class='frame' style='position: absolute; top: %fpx; left: %fpx; width: %fpx; height:40px'>%d</div>" % (top, frame.start_time/1000., (frame.end_time - frame.start_time)/1000., frame_no)
        top += 42
        for times in zip(frame.enqueue_times, frame.start_times, frame.finish_times):
            print >> f, "<div class='frame schedule' style='position: absolute; top: %fpx; left: %fpx; width: %fpx; height:10px'>%d</div>" % (top, times[0]/1000., (times[2]-times[0])/1000., frame_no)
            top += 10
            print >> f, "<div class='frame' style='position: absolute; top: %fpx; left: %fpx; width: %fpx; height:20px'></div>" % (top, times[1]/1000., (times[2]-times[1])/1000.)
            top += 22
        frame_no += 1

print_times(finished_frames)

vsync_time = 0
while vsync_time < end_time:
    if vsync_time % 16666 == 0:
        print >> f, "<div class='vsync' style='position: absolute; left: %fpx; top: 0px; width: 1px; height:800px'></div>" % (vsync_time/1000.)
    vsync_time += 1

print >> f, "</div>"

