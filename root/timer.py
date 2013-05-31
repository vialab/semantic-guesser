import time

class Timer:
    
    def __init__(self, title=None):
        self.title = title
        
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.elapsed = self.end - self.start
        print "{} took {:.3f} seconds".format(self.title, self.elapsed)

# if __name__ == '__main__':      
#     with Timer('test'):
#         time.sleep(2)