import { Link, Route, Routes } from "react-router-dom";

import { AdminLayout } from "./admin/AdminLayout";
import { Header } from "./components/Header";
import { CardDetailPage } from "./pages/CardDetailPage";
import { CartPage } from "./pages/CartPage";
import { CataloguePage } from "./pages/CataloguePage";
import { CheckoutPage } from "./pages/CheckoutPage";
import { HomePage } from "./pages/HomePage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { OrderLookupPage } from "./pages/OrderLookupPage";
import { OrderPage } from "./pages/OrderPage";
import { AdminAddCardPage } from "./pages/admin/AdminAddCardPage";
import { AdminInventoryPage } from "./pages/admin/AdminInventoryPage";
import { AdminListingPage } from "./pages/admin/AdminListingPage";
import { AdminOrdersPage } from "./pages/admin/AdminOrdersPage";
import { AdminReportsPage } from "./pages/admin/AdminReportsPage";

export function App() {
  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <Header />

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/cards" element={<CataloguePage />} />
          <Route path="/cards/:listingId" element={<CardDetailPage />} />
          <Route path="/cart" element={<CartPage />} />
          <Route path="/checkout" element={<CheckoutPage />} />
          <Route path="/orders" element={<OrderLookupPage />} />
          <Route path="/orders/:publicRef" element={<OrderPage />} />
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<AdminInventoryPage />} />
            <Route path="add" element={<AdminAddCardPage />} />
            <Route path="orders" element={<AdminOrdersPage />} />
            <Route path="reports" element={<AdminReportsPage />} />
            <Route path="listings/:listingId" element={<AdminListingPage />} />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>

      <footer className="border-t border-seam px-4 py-6 text-center text-xs text-muted">
        Vault 151 &middot; prices in Canadian dollars &middot;{" "}
        <Link to="/admin" className="hover:text-brass">
          Seller
        </Link>
      </footer>
    </div>
  );
}
