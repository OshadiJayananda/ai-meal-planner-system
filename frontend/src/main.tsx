import React from "react";
import ReactDOM from "react-dom/client";
import { Activity, ChefHat, Clock, Flame, Loader2, Play, RotateCcw, Sparkles } from "lucide-react";
import { createMealPlan, listSessions, MealPlanResult, SessionSummary } from "./services/api";
import "./styles.css";

const samplePrompts = [
  "Create a vegetarian meal plan using beans and spinach, target 1500 kcal",
  "I need a weight loss meal plan with chicken and rice around 1400 calories",
  "Analyze calories of these meals: oatmeal with banana, chicken stir-fry, lentil soup"
];

function formatStep(step: string) {
  return step.replaceAll("_", " ");
}

function MetricCard({ label, value, suffix }: { label: string; value?: number; suffix: string }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value ?? 0}</strong>
      <small>{suffix}</small>
    </div>
  );
}

function App() {
  const [prompt, setPrompt] = React.useState(samplePrompts[0]);
  const [age, setAge] = React.useState(22);
  const [weight, setWeight] = React.useState(70);
  const [result, setResult] = React.useState<MealPlanResult | null>(null);
  const [sessions, setSessions] = React.useState<SessionSummary[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    listSessions().then(setSessions).catch(() => setSessions([]));
  }, []);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const nextResult = await createMealPlan(prompt, age, weight);
      setResult(nextResult);
      setSessions(await listSessions());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate the meal plan");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="planner-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Multi-agent nutrition planner</p>
            <h1>AI Meal Planner</h1>
          </div>
          <ChefHat aria-hidden="true" />
        </div>

        <form className="planner-form" onSubmit={handleSubmit}>
          <label htmlFor="prompt">Meal request</label>
          <textarea
            id="prompt"
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            rows={6}
            placeholder="Describe your goal, ingredients, restrictions, and calorie target"
          />

          <div className="form-grid">
            <label>
              Age
              <input type="number" min="0" max="120" value={age} onChange={(event) => setAge(Number(event.target.value))} />
            </label>
            <label>
              Weight kg
              <input type="number" min="0" max="400" value={weight} onChange={(event) => setWeight(Number(event.target.value))} />
            </label>
          </div>

          <div className="sample-row">
            {samplePrompts.map((item) => (
              <button key={item} type="button" className="sample-button" onClick={() => setPrompt(item)}>
                {item}
              </button>
            ))}
          </div>

          <div className="action-row">
            <button className="primary-button" type="submit" disabled={isLoading}>
              {isLoading ? <Loader2 className="spin" aria-hidden="true" /> : <Play aria-hidden="true" />}
              Generate
            </button>
            <button className="icon-button" type="button" title="Reset result" onClick={() => setResult(null)}>
              <RotateCcw aria-hidden="true" />
            </button>
          </div>
        </form>

        {error && <div className="error-banner">{error}</div>}
      </section>

      <section className="result-panel">
        <div className="summary-band">
          <MetricCard label="Calories" value={result?.daily_totals.total_calories} suffix="kcal" />
          <MetricCard label="Protein" value={result?.daily_totals.total_protein_g} suffix="g" />
          <MetricCard label="Carbs" value={result?.daily_totals.total_carbs_g} suffix="g" />
          <MetricCard label="Fat" value={result?.daily_totals.total_fat_g} suffix="g" />
        </div>

        <div className="content-grid">
          <article className="output-section">
            <div className="section-title">
              <Sparkles aria-hidden="true" />
              <h2>Generated Meal Plan</h2>
            </div>
            <pre className="meal-output">
              {isLoading ? "The agents are preparing your plan..." : result?.final_output ?? "Your generated meal plan will appear here."}
            </pre>
          </article>

          <aside className="side-section">
            <div className="section-title">
              <Activity aria-hidden="true" />
              <h2>Agent Workflow</h2>
            </div>
            <ol className="workflow-list">
              {(result?.executed_steps.length ? result.executed_steps : ["coordinator", "meal_generation", "nutrition_analysis", "format_output"]).map((step) => (
                <li key={step}>{formatStep(step)}</li>
              ))}
            </ol>

            <div className="section-title history-title">
              <Clock aria-hidden="true" />
              <h2>Recent Sessions</h2>
            </div>
            <div className="history-list">
              {sessions.length === 0 && <p>No saved sessions yet.</p>}
              {sessions.slice(0, 6).map((session) => (
                <div className="history-item" key={session.id}>
                  <strong>{session.goal ?? "Meal plan"}</strong>
                  <span>{session.user_input}</span>
                  <small>
                    <Flame aria-hidden="true" />
                    {session.total_calories ?? 0} kcal
                  </small>
                </div>
              ))}
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(<App />);
