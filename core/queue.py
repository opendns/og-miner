import threading
import Queue

class TaskQueue(object):
	def __init__(self):
		self.counter = 0
		self.mutex = threading.Lock()
		self.queue = Queue.Queue()

	def push(self, task):
	    self.queue.put(task, False)

	    self.mutex.acquire(True)
	    self.counter += 1
	    self.mutex.release()

	def get(self):
		try:
			task = self.queue.get(block=False)
		except Queue.Empty:
			task = None
		return task

	def pop(self):
	    self.queue.task_done()
	    
	    self.mutex.acquire(True)
	    self.counter -= 1
	    self.mutex.release()

	def count(self):
	    return self.counter