import signal

SIGNALS = {
	'ABRT':   signal.SIGABRT,
	'ALRM':   signal.SIGALRM,
	'BUS':    signal.SIGBUS,
	'CHLD':   signal.SIGCHLD,
	'CLD':    signal.SIGCLD,
	'CONT':   signal.SIGCONT,
	# 'EMT':    signal.SIGEMT,
	'FPE':    signal.SIGFPE,
	'HUP':    signal.SIGHUP,
	'ILL':    signal.SIGILL,
	# 'INFO':   signal.SIGINFO,
	'INT':    signal.SIGINT,
	'IO':     signal.SIGIO,
	'IOT':    signal.SIGIOT,
	'KILL':   signal.SIGKILL,
	# 'LOST':   signal.SIGLOST,
	'PIPE':   signal.SIGPIPE,
	'POLL':   signal.SIGPOLL,
	'PROF':   signal.SIGPROF,
	'PWR':    signal.SIGPWR,
	'QUIT':   signal.SIGQUIT,
	'SEGV':   signal.SIGSEGV,
	# 'STKFLT': signal.SIGSTKFLT,
	'STOP':   signal.SIGSTOP,
	'SYS':    signal.SIGSYS,
	'TERM':   signal.SIGTERM,
	'TRAP':   signal.SIGTRAP,
	'TSTP':   signal.SIGTSTP,
	'TTIN':   signal.SIGTTIN,
	'TTOU':   signal.SIGTTOU,
	# 'UNUSED': signal.SIGUNUSED,
	'URG':    signal.SIGURG,
	'USR1':   signal.SIGUSR1,
	'USR2':   signal.SIGUSR2,
	'VTALRM': signal.SIGVTALRM,
	'WINCH':  signal.SIGWINCH,
	'XCPU':   signal.SIGXCPU,
	'XFSZ':   signal.SIGXFSZ
}


class Global:
	CONFIG_FILE = ''
	program_list = dict()

PID_FILE = '/tmp/taskmaster.pid'
LOCK_FILE = '/tmp/taskmasterd.lock'