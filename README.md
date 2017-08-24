# patrol
巡检脚本：

一、目录规划
	1.	脚本存放目录/opt/patrol/，主体脚本为mss.py，配置文件为config.json
	2.	脚本运行产生的日志文件存放于/var/log/mss.log，考虑到巡检出错会由运维人员介入处理，日志仅保留最近一次的执行结果，防止文件堆积
	
二、使用方法
	1.	使用部署的ansible主控端进行配置文件分发及指令下发(这台主机已在CMDB维护用途，如需下架等操作请知会我)
	2.	ansible的配置文件为/etc/ansible/ansible.cfg，主机列表为/etc/ansible/hosts，在主机列表文件中对主机按所在机房和所属业务进行了分组
	3.	使用中，如果主机有功能或IP地址上的变动，需要及时维护主机列表和脚本配置文件并使用ansible将脚本配置文件下发到所有mss主机（对应组：all）
	$ansible all -m copy -a "src=/opt/patrol dest=/opt" 
	4.  巡检命令
  $ansible [group_name] -m shell -a 'python /opt/patrol/mss.py'
	5.  主控端如有迁移需求，需要同时拷贝ansible的ansible.cfg和hosts文件。
