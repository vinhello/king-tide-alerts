import { useState } from "react";
import type { NotificationPreference, SubscribeRequest } from "../types";
import { subscribe } from "../services/api";

export default function SubscribeForm() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [preference, setPreference] =
    useState<NotificationPreference>("email");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("loading");
    setErrorMessage("");

    const data: SubscribeRequest = {
      name,
      notification_preference: preference,
    };
    if (preference === "email" || preference === "both") {
      data.email = email;
    }
    if (preference === "sms" || preference === "both") {
      data.phone = phone;
    }

    try {
      await subscribe(data);
      setStatus("success");
    } catch (err: unknown) {
      setStatus("error");
      if (err && typeof err === "object" && "response" in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setErrorMessage(
          axiosErr.response?.data?.detail || "Something went wrong"
        );
      } else {
        setErrorMessage("Something went wrong");
      }
    }
  };

  if (status === "success") {
    return (
      <section className="subscribe-form">
        <div className="success-message">
          <h2>Check your inbox!</h2>
          <p>
            We sent a confirmation link. Click it to activate your king tide
            alerts.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="subscribe-form">
      <h2>Get Alerts</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="name">Name</label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            placeholder="Your name"
          />
        </div>

        <div className="form-group">
          <label htmlFor="preference">Notify me via</label>
          <select
            id="preference"
            value={preference}
            onChange={(e) =>
              setPreference(e.target.value as NotificationPreference)
            }
          >
            <option value="email">Email</option>
            <option value="sms" disabled>SMS (coming soon)</option>
            <option value="both" disabled>Both (coming soon)</option>
          </select>
        </div>

        {(preference === "email" || preference === "both") && (
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="you@example.com"
            />
          </div>
        )}

        {(preference === "sms" || preference === "both") && (
          <div className="form-group">
            <label htmlFor="phone">Phone</label>
            <input
              id="phone"
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              required
              placeholder="+1 (555) 123-4567"
            />
          </div>
        )}

        {status === "error" && (
          <p className="error-message">{errorMessage}</p>
        )}

        <button type="submit" disabled={status === "loading"}>
          {status === "loading" ? "Subscribing..." : "Subscribe"}
        </button>
      </form>
    </section>
  );
}
