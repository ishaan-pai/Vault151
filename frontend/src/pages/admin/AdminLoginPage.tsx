import { useState, type FormEvent } from "react";

import { useSignIn } from "../../api/adminQueries";

export function AdminLoginPage() {
  const signIn = useSignIn();
  const [username, setUsername] = useState("seller");
  const [password, setPassword] = useState("");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    signIn.mutate({ username, password });
  }

  const fieldClass =
    "mt-1 w-full rounded border border-seam bg-canvas px-3 py-2 text-sm text-ink";

  return (
    <form
      onSubmit={handleSubmit}
      className="mx-auto flex max-w-sm flex-col gap-4 rounded-lg border border-seam bg-surface p-6"
    >
      <h1 className="text-lg font-medium text-ink">Seller sign-in</h1>

      <div>
        <label className="block text-xs text-muted" htmlFor="admin-username">
          Username
        </label>
        <input
          id="admin-username"
          required
          autoComplete="username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          className={fieldClass}
        />
      </div>

      <div>
        <label className="block text-xs text-muted" htmlFor="admin-password">
          Password
        </label>
        <input
          id="admin-password"
          type="password"
          required
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className={fieldClass}
        />
      </div>

      {signIn.isError ? (
        <p className="text-sm text-danger">{signIn.error.message}</p>
      ) : null}

      <button
        type="submit"
        disabled={signIn.isPending}
        className="rounded border border-brass/50 bg-brass/10 px-4 py-2 text-sm text-brass transition enabled:hover:bg-brass/20 disabled:opacity-50"
      >
        {signIn.isPending ? "Checking\u2026" : "Sign in"}
      </button>

      <p className="text-xs text-muted">
        Five wrong attempts locks this address out for fifteen minutes.
      </p>
    </form>
  );
}
