import { api } from './client'

export interface BenchmarkEntry {
  id: number; user_id: number; session_id?: number
  benchmark_type: string; value: number; recorded_at: string; notes?: string
}

export const listBenchmarks = (benchmark_type?: string) =>
  api.get<BenchmarkEntry[]>('/benchmarks', { params: benchmark_type ? { benchmark_type } : {} })
    .then(r => r.data)

export const createBenchmark = (data: {
  benchmark_type: string; value: number; session_id?: number; notes?: string
}) => api.post<BenchmarkEntry>('/benchmarks', data).then(r => r.data)
