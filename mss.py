#!/bin/env python
#coding:utf-8
import subprocess,time,threading,logging,json

Log_file = '/var/log/mss.log'
Conf_file = '/opt/patrol/config.json'

#读入json格式的配置文件
with open(Conf_file) as config:
	conf = json.load(config)
	iplist = conf.keys()
	
#取本机IP  
hostip = subprocess.Popen('hostname -i', stdout=subprocess.PIPE, shell=True).stdout.read().strip()

if hostip in iplist:
	compons = conf[hostip]['compon']
else:
	print "host not in iplist"
	exit(1)

#日志收集
logging.basicConfig(
    level=logging.DEBUG,
    format = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt = '%a, %d %b %Y %H:%M:%S',
    filename = Log_file,
    filemode = 'w')


#屏显日志
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)


#多线程检测组件存活
def pidof(compon):
    pid = subprocess.Popen('pidof ' + compon, stdout = subprocess.PIPE, shell = True).communicate()[0].strip()
    return pid
	

def pidtest(compon, nsec=5):
	logging.debug('testing %-7s' %compon)
	pid1 = pidof(compon)
	time.sleep(nsec)
	pid2 = pidof(compon)
	if pid1 == pid2 and len(pid1.split()) == compons[compon]:
		logging.debug("%-10s ......ok" %compon)
	else:
		logging.warning("%-10s ....fail" %compon)


def main():
	threads = []
	nloops = range(len(compons))
	
	for key in compons:
		t = threading.Thread(target=pidtest, args=(key, 5))
		threads.append(t)
		
	for i in nloops:
		threads[i].start()
		
	for i in nloops:
		threads[i].join()
		
if __name__ == '__main__':
	main() 
