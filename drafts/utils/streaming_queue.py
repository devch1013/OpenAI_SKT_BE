class StreamingQueue:
    def __init__(self):
        self.main_queue = list()
        self.end_flag = False

    def __len__(self):
        return len(self.main_queue)

    def append(self, new_text):
        # print(new_text)
        self.main_queue.append(new_text)

    def get(self):
        """
        return and delete first object of queue
        """
        return self.main_queue.pop(0)

    def end_job(self):
        self.end_flag = True

    def is_end(self):
        return self.end_flag and len(self.main_queue) == 0

    def is_empty(self):
        return len(self.main_queue) == 0

    def is_streaming_end(self):
        return self.end_flag and len(self.main_queue) > 0
    
    def __str__(self) -> str:
        if len(self.main_queue)>0:
            return self.main_queue[-1]
        else:
            return "empty"

    def refresh(self):
        return ""
