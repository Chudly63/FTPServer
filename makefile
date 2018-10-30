run :
	python FTPServer.py -v log.txt 21000

log : 
	cat log.txt

rm :
	rm log.txt
