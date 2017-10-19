#!/usr/bin/env python
#coding: utf-8

import time, os
import subprocess,re
from multiprocessing import Pool

SRV_ADDRS = 'http://auto-verification.openspeech.cn/'
TIME_FMT = "%Y%m%d"
DATE = time.strftime(TIME_FMT, time.localtime())
MAX_PROCESSOR = 20
CONF = './patrol'

def _ab_exec(testline):

	'''单路测试流程'''
	#依据pid生成临时文件
	pid = str(os.getpid())
	tmp_file = '/tmp/' + DATE + '_' + pid + '.tmp'
	
	#正则匹配格式
	pat_jid = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
	pat_res = re.compile('"res".*')
	pat_num = re.compile(r'{"res": (.*?),(.*)')
	#收集结果返回，结果呈现
	result = []
	result.append(testline.strip('\n'))
	print '%-80s testing...' %testline.strip('\n')
	
	#测试用文件
	if not os.path.exists(tmp_file):
		os.mknod(tmp_file)
	with open(tmp_file, 'w') as fhand:
		fhand.write(testline)
	
	cmd = 'ab -t 60 -v 4 -n 1 -c 1  -p ' + tmp_file + ' -T "text" ' + SRV_ADDRS
	child = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	out = child.stdout.read().split('\n')

	for line in out:
		if re.search(pat_jid, line):
			#找到jid格式的数据
			jid = "jobId="+line
			result.append(jid)
			with open(tmp_file, 'w') as fhand:
				fhand.write(jid)
			break
		elif re.search(pat_res, line):
			#找到res出错信息
			result.append(line)
			break
		
	#结果分析循环
	for i in [5,10,15,30,60,61]:
		time.sleep(i)
		child = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
		out = child.stdout.read().split('\n')
		
		flag = 0
		for line in out:
			if re.search(pat_res, line):
				#分析res,0=成功，-1=失败，-2=等待重试
				#未分析到res，则认为出错，保留out作为debug依据
				flag = 1
				if re.match(pat_num, line).group(1).strip('"') == '0':
					result.append('sreq ' + str(i) + ' OK')
					print 'sreq %s OK' %str(i)
					os.remove(tmp_file)
					return result
				elif re.match(pat_num, line).group(1).strip('"') == '-1':
					result.append('sreq ' + str(i) + ' FAIL')
					print 'sreq %s FAIL' %str(i)
					os.remove(tmp_file)
					return result
				elif re.match(pat_num, line).group(1).strip('"') == '-2':
					if i == 61:
						#超时返回失败
						result.append('sreq ' + str(i) + ' TIMEOUT')
						print 'sreq %s TIMEOUT' %str(i)
						os.remove(tmp_file)
						return result
					else:
						result.append('sreq ' + str(i) + ' TRY AGAIN')
						print 'sreq %s TRY AGAIN' %str(i)
						break
		#没有匹配到res
		if not flag:
			result.append('sreq ' + str(i) + ' DETECT ERROR')
			print 'sreq %s ERROR' %str(i)
			os.remove(tmp_file)
			return result


#定长切分						
def list_of_groups(init_list, childern_list_len):
	list_of_groups = zip(*(iter(init_list),) *childern_list_len)
	end_list = [list(i) for i in list_of_groups]
	count = len(init_list) % childern_list_len
	end_list.append(init_list[-count:]) if count !=0 else end_list
	return end_list


#按照切分长度，进行多进程请求
def multi_detect(config):
	with open(config) as  conf:
		split_list = list_of_groups(conf.readlines(), MAX_PROCESSOR)
	for i in split_list:
		p = Pool(len(i))
		result = []
		for payload in i:
			result.append(p.apply_async(_ab_exec, args=(payload,)))
		p.close()
		p.join()
		#等待结果，会阻塞（等待时间取决于最慢的任务处理时间）
		#为了分析结果必须等待
		for res in result:
			print '%-80s %s' %(res.get()[0],res.get()[-1])


#串行测试
'''def multi_detect(config):

	with open(config) as  conf:
		hconf = conf.readlines()
	for i in hconf:
		_ab_exec(i)
'''


if __name__ == '__main__':
	multi_detect(CONF)