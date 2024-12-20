from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

# If you want to run a snippet of code before or after the crew starts, 
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class QualityMonitoring():
	"""QualityMonitoring crew"""

	# Learn more about YAML configuration files here:
	# Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
	# Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
	#agents_config = 'config/agents.yaml'
	#tasks_config = 'config/tasks.yaml'

	# If you would like to add tools to your agents, you can learn more about it here:
	# https://docs.crewai.com/concepts/agents#agent-tools
	@agent
	def supervisor(self) -> Agent:
		"""Create Supervisor Agent"""
		return Agent(
			config=self.agents_config['supervisor'],
			#llm=self.llm,
			verbose=True,
			#allow_delegation=False
		)

	@agent
	def operator(self) -> Agent:
		"""Create Operator Agent"""
		return Agent(
			config=self.agents_config['operator'],
			#llm=self.llm,
			verbose=True,
			allow_delegation=False
		)

	@agent
	def monitor(self) -> Agent:
		"""Create Monitor Agent"""
		return Agent(
			config=self.agents_config['monitor'],
			#llm=self.llm,
			verbose=True,
			allow_delegation=False
		)
  
	@agent
	def judge(self) -> Agent:
		"""Create Judge Agent"""
		return Agent(
			config=self.agents_config['judge'],
			#llm=self.llm,
			verbose=True,
			allow_delegation=False
		)
  
	@agent
	def reporting_analyst(self) -> Agent:
		"""Create Reporting Agent"""
		return Agent(
			config=self.agents_config['reporting_analyst'],
			#llm=self.llm,
			verbose=True,
			allow_delegation=False
		)

	# To learn more about structured task outputs, 
	# task dependencies, and task callbacks, check out the documentation:
	# https://docs.crewai.com/concepts/tasks#overview-of-a-task
	@task
	def monitor_task(self) -> Task:
		"""Create Monitor Task"""
		return Task(
			config=self.tasks_config['monitor_task'],
			#agent=self.monitor()
		)

	@task
	def operator_task(self) -> Task:
		"""Create Operator Task"""
		return Task(
			config=self.tasks_config['operator_task'],
			#agent=self.operator(),
			#context=[self.monitor_task()]
		)

	@task
	def judge_task(self) -> Task:
		"""Create Judge Task"""
		return Task(
			config=self.tasks_config['judge_task'],
			#agent=self.judge(),
			#context=[self.monitor_task(), self.operator_task()]
		)
  
	@task
	def reporting_task(self) -> Task:
		"""Create Reporting Task"""
		return Task(
			config=self.tasks_config['reporting_task'],
			#agent=self.judge(),
			#context=[self.monitor_task(), self.operator_task()]
   			output_file='output/customer_service_feedback_01.md'
		)

	# @task
	# def supervisor_task(self) -> Task:
	# 	"""Create Supervisor Task"""
	# 	return Task(
	# 		config=self.tasks_config['supervisor_task'],
	# 		#agent=self.supervisor(),
	# 		#context=[self.monitor_task(), self.operator_task(), self.judge_task()],
	# 		#output_file='output/customer_service_feedback.md'
	# 	)

	@crew
	def crew(self) -> Crew:
		"""Creates the QualityMonitoring crew"""
		# To learn how to add knowledge sources to your crew, check out the documentation:
		# https://docs.crewai.com/concepts/knowledge#what-is-knowledge

		return Crew(
			agents=[self.monitor(), self.operator(), self.judge(), self.reporting_analyst()], # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.hierarchical,
			verbose=True,
   			manager_agent=self.supervisor()
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)