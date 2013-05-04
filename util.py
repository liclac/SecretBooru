import os

path = lambda filename: os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)

def zerofill_delete(path):
	with open(path, 'wb') as f:
		for _ in range(os.path.getsize(path)):
			f.write('\0')
	os.remove(path)
