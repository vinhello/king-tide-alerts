import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { unsubscribe } from "../services/api";

export default function Unsubscribe() {
  const { token } = useParams<{ token: string }>();
  const [status, setStatus] = useState<"loading" | "success" | "error" | "idle">(
    token ? "loading" : "idle"
  );
  const [message, setMessage] = useState("");

  useEffect(() => {
    async function doUnsubscribe() {
      if (!token) return;
      try {
        const response = await unsubscribe(token);
        setStatus("success");
        setMessage(response.message);
      } catch {
        setStatus("error");
        setMessage("Invalid or expired unsubscribe link.");
      }
    }
    doUnsubscribe();
  }, [token]);

  return (
    <div className="page">
      <section className="status-page">
        {status === "idle" && (
          <>
            <h1>Unsubscribe</h1>
            <p>Use the link from your email or SMS to unsubscribe.</p>
          </>
        )}
        {status === "loading" && <p>Processing your request...</p>}
        {status === "success" && (
          <>
            <h1>Unsubscribed</h1>
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
