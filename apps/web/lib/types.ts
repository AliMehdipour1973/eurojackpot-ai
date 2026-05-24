export interface Draw {
  draw_date: number
  main_numbers: number[]
  euro_numbers: number[]
  day_of_week?: number
  ticket_sales_amount?: number
  jackpot_amount?: number
  jackpot_winners?: number
}

export interface FrequencyItem {
  number: number
  frequency: number
}

export interface FrequencyResponse {
  window: number
  as_of_draw: number
  frequencies: FrequencyItem[]
}

export interface GeneratorResponse {
  mode: string
  main_numbers: number[]
  euro_numbers: number[]
  next_draw_date: string
  training_draws: number
  based_on_features_from: number
  disclaimer: string
  backtest_reference: {
    hit_rate_improvement_vs_random: string
  }
}
