run :
	python FTPServer.py -v log.txt 21000

run2 :
	python FTPServer.py -v log.txt 21001

log : 
	cat log.txt

rm :
	rm log.txt
