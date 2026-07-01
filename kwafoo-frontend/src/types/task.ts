export interface TaskStatus {
  unprocessed_count: number
  total_count: number
  scheduler_jobs: Array<{ id: string; type: string }>
  pipeline_running: boolean
}

export interface TaskResult {
  status: string
  message: string
}