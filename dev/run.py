import add_9_tet_knots
import taskdb2.worker

taskdb2.worker.run_function('census_knots', 'task_hyp', add_9_tet_knots.add_hyp_data)
