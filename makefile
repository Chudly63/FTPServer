PORT = 21000
LOG = log.txt

run :
	python FTPServer.py ${LOG} ${PORT}
