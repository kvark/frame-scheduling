time = 0
end_time = 1000000
frame_count = 0
frame_delay = 0
class Queue(list):
    def __init__(self):
        self.current = None
        self.next_time = 0
    def schedule(self, time):
        print "sched", time
        global frame_delay
        global frame_count
        if self.next_time == time:
            if self.current:
                frame_count += 1
                frame_delay += time - self.current.start_time 
                print time - self.current.start_time 
                self.pop(0)

        if self.next_time <= time and len(self):
            self.current = self[0]
            self.next_time = self.current.length + time
            print "sched next", self.next_time
    
class Frame:
    def __init__(self, start_time, length):
        self.start_time = start_time
        self.length = length[0]

main_thread = Queue()
compositor = Queue()
while time < end_time:
    if time % 16666 == 0:
        # vsync

        MAX_QUEUE_LENGTH = 1
        # back pressure -- don't let the queue grow too long
        if len(main_thread) <= MAX_QUEUE_LENGTH:
            main_thread.append(Frame(time, (18*1000,)))
            main_thread.schedule(time)
        else:
            print "skipped frame"
    if main_thread.next_time == time:
        #print current
        main_thread.schedule(time)
        
    time += 1

print frame_count
print 1000*1000. * frame_count / (end_time  * 1.0), "fps"
print frame_delay / (frame_count * 1000.0), "ms"
