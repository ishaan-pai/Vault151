import { Link, NavLink } from "react-router-dom";

import { useCart } from "../cart/CartContext";

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `text-sm transition ${isActive ? "text-brass" : "text-muted hover:text-ink"}`;

export function Header() {
  const cart = useCart();

  return (
    <header className="border-b border-seam bg-surface">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-4 py-4">
        <Link to="/" className="flex items-baseline gap-2">
          <span className="text-lg font-semibold tracking-tight text-ink">Vault</span>
          <span className="text-lg font-semibold text-brass">151</span>
        </Link>

        <nav className="flex items-center gap-5">
          <NavLink to="/" end className={linkClass}>
            Featured
          </NavLink>
          <NavLink to="/cards" className={linkClass}>
            Catalogue
          </NavLink>
          <NavLink to="/orders" className={linkClass}>
            Find order
          </NavLink>
          <NavLink to="/cart" className={linkClass}>
            Cart
            {cart.count > 0 ? (
              <span className="ml-1 rounded-full bg-brass px-1.5 py-0.5 text-xs font-semibold text-canvas">
                {cart.count}
              </span>
            ) : null}
          </NavLink>
        </nav>
      </div>
    </header>
  );
}
