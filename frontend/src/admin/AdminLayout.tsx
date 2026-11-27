import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";

import { useSession, useSignOut } from "../api/adminQueries";
import { StateMessage } from "../components/StateMessage";
import { AdminLoginPage } from "../pages/admin/AdminLoginPage";

const tabClass = ({ isActive }: { isActive: boolean }) =>
  `border-b-2 px-1 pb-2 text-sm transition ${
    isActive
      ? "border-brass text-brass"
      : "border-transparent text-muted hover:text-ink"
  }`;

/**
 * Wraps every admin page. If there is no valid session the sign-in form is shown
 * instead of the page - the browser never holds a readable token, so "are we signed
 * in" is answered by asking the server, not by reading storage.
 */
export function AdminLayout() {
  const session = useSession();
  const signOut = useSignOut();
  const navigate = useNavigate();

  if (session.isPending) return <StateMessage title="Checking your session&hellip;" />;
  if (session.isError) return <AdminLoginPage />;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-seam pb-3">
        <div className="flex items-baseline gap-3">
          <h1 className="text-lg font-medium text-ink">Seller admin</h1>
          <span className="text-xs text-muted">{session.data.username}</span>
        </div>
        <div className="flex items-center gap-4">
          <Link to="/" className="text-sm text-muted hover:text-brass">
            View shop
          </Link>
          <button
            type="button"
            onClick={() =>
              signOut.mutate(undefined, {
                onSuccess: () => void navigate("/admin"),
              })
            }
            className="text-sm text-muted underline hover:text-brass"
          >
            Sign out
          </button>
        </div>
      </div>

      <nav className="flex gap-6">
        <NavLink to="/admin" end className={tabClass}>
          Inventory
        </NavLink>
        <NavLink to="/admin/add" className={tabClass}>
          Add a card
        </NavLink>
        <NavLink to="/admin/orders" className={tabClass}>
          Orders
        </NavLink>
        <NavLink to="/admin/reports" className={tabClass}>
          Reports
        </NavLink>
      </nav>

      <Outlet />
    </div>
  );
}
