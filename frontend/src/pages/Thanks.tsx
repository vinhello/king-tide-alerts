import { Link } from "react-router-dom";

export default function Thanks() {
  return (
    <div className="page">
      <section className="status-page">
        <h1>Thank you!</h1>
        <p>Your support helps keep King Tide Alerts running. We appreciate it!</p>
        <Link to="/" className="back-link">
          Back to home
        </Link>
      </section>
    </div>
  );
}
