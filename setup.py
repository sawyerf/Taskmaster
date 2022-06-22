from setuptools	import setup, find_packages

setup(
	name='Taskmaster',
	description='This program is a job control task.',
	long_description_content_type='text/markdown',
	install_requires=['pyyaml'],
	packages=find_packages(include=[
		'taskmaster', 'taskmaster.*',
	]),
	entry_points={
		'console_scripts': [
			'taskmasterd = taskmaster.taskmasterd:main',
			'taskmasterctl = taskmaster.taskmasterctl:main'
		]
	}
)