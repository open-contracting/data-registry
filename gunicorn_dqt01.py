import multiprocessing

errorlog = '/home/datlab/logs/data_registry_datlab_eu.log'
loglevel = 'info'
accesslog = '/home/datlab/logs/data_registry_datlab_eu.log'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

workers = multiprocessing.cpu_count() * 2 + 1
