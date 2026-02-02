import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { confirmSubscription } from "../services/api";

export default function Confirmation() {
  const { token } = useParams<{ token: string }>();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    async function confirm() {
      if (!token) {
        setStatus("error");
        setMessage("Invalid confirmation link.");
        return;
      }
      try {
        const response = await confirmSubscription(token);
        setStatus("success");
        setMessage(response.message);
      } catch {
        setStatus("error");
        setMessage("Invalid or expired confirmation link.");
      }
    }
    confirm();
  }, [token]);

  return (
    <div className="page">
      <section className="status-page">
        {status === "loading" && <p>Confirming your subscription...</p>}
        {status === "success" && (
          <>
            <h1>Confirmed!</h1>
            <p>{message}</p>
          </>
        )}
        {status === "error" && (
          <>
            <h1>Oops</h1>
            <p>{message}</p>
          </>
        )}
        <Link to="/" className="back-link">
          Back to home
        </Link>
      </section>
    </div>
  );
}
