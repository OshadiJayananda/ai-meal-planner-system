export type Meal = {
  name?: string;
  type?: string;
  description?: string;
  calories?: number;
  nutrition?: {
    calories?: number;
    protein_g?: number;
    carbs_g?: number;
    fat_g?: number;
    confidence?: string;
  };
};

export type MealPlanResult = {
  session_id: number;
  user_input: string;
  age: number;
  weight: number;
  goal: string;
  diet_type: string;
  ingredients: string[];
  avoid_ingredients: string[];
  target_calories: number;
  executed_steps: string[];
  meals: Meal[];
  daily_totals: {
    total_calories?: number;
    total_protein_g?: number;
    total_carbs_g?: number;
    total_fat_g?: number;
  };
  final_output: string;
  errors: string[];
};

export type SessionSummary = {
  id: number;
  user_input: string;
  age: number;
  weight: number;
  created_at: string;
  goal?: string;
  diet_type?: string;
  target_calories?: number;
  total_calories?: number;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...init?.headers
    },
    ...init
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail ?? "Request failed");
  }

  return response.json() as Promise<T>;
}

export function createMealPlan(prompt: string, age: number, weight: number) {
  return request<MealPlanResult>("/api/meal-plan", {
    method: "POST",
    body: JSON.stringify({ prompt, age, weight })
  });
}

export function listSessions() {
  return request<SessionSummary[]>("/api/sessions");
}
