import { Link } from "react-router-dom";

import { StateMessage } from "../components/StateMessage";

export function NotFoundPage() {
  return (
    <StateMessage title="There is nothing at this address.">
      <Link to="/" className="text-sm text-brass underline">
        Back to the vault
      </Link>
    </StateMessage>
  );
}
