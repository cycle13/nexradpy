#!/usr/bin/env python3

from functools import wraps
from time import time


def timing(f):
	'''
	see https://codereview.stackexchange.com/questions/169870/decorator-to-measure-execution-time-of-a-function
	'''
	@wraps(f)
	def wrapper(*args, **kwargs):
		start = time()
		result = f(*args, **kwargs)
		end = time()
		print(f'Elapsed time running {f.__name__}: {(end - start) / 60} minutes')
		return result
	return wrapper