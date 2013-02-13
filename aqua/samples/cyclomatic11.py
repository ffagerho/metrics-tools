#!/usr/bin/python

class Foo:
	def __init__(self):
		self.__var1 = 0
		self.__var2 = 1

	def add(self, op):
		if op > 100:
			return self.__var1 + op
		else:
			return op - self.__var2

	def sub(self, op):
		if op < 2:
			return 10

		if op < 100:
			return op - self.__var2
		else:
			return self.__var1 - op
