import { execFileSync } from "node:child_process";
import path from "node:path";

/** Rebuilds the E2E database from scratch so every run starts from known data. */
export default function globalSetup() {
  const backend = path.resolve(__dirname, "../../backend");
  execFileSync(path.join(backend, ".venv/bin/python"), ["-m", "app.seed", "--reset"], {
    cwd: backend,
    env: { ...process.env, WF_DATABASE_URL: "sqlite:///./workflow-e2e.db" },
    stdio: "inherit",
  });
}
