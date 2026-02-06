import { Link } from "react-router-dom";

export default function PrivacyPolicy() {
  return (
    <div className="page">
      <div className="legal-page">
        <h1>Privacy Policy</h1>
        <p className="legal-updated">Last updated: February 2026</p>

        <section>
          <h2>What We Collect</h2>
          <p>
            When you subscribe to King Tide Alerts, we collect the following
            information:
          </p>
          <ul>
            <li>
              <strong>Name:</strong> Used to personalize your alerts
            </li>
            <li>
              <strong>Email address:</strong> Used to send tide alerts (if you
              choose email notifications)
            </li>
            <li>
              <strong>Phone number:</strong> Used to send SMS alerts (if you
              choose SMS notifications)
            </li>
          </ul>
        </section>

        <section>
          <h2>How We Use Your Data</h2>
          <p>Your information is used solely to:</p>
          <ul>
            <li>Send you tide alerts before high tide events in Sausalito</li>
            <li>Send confirmation messages when you subscribe</li>
            <li>Process unsubscribe requests</li>
          </ul>
          <p>
            We do <strong>not</strong> use your data for marketing, advertising,
            or any purpose other than delivering tide alerts.
          </p>
        </section>

        <section>
          <h2>Data Sharing</h2>
          <p>
            We do <strong>not</strong> sell, rent, or share your personal
            information with third parties except as required to deliver our
            service:
          </p>
          <ul>
            <li>
              <strong>Resend:</strong> Our email delivery provider
            </li>
            <li>
              <strong>Twilio:</strong> Our SMS delivery provider
            </li>
          </ul>
          <p>
            These providers process your data only to deliver messages on our
            behalf.
          </p>
        </section>

        <section>
          <h2>Data Retention</h2>
          <p>
            We retain your subscription information only while your subscription
            is active. When you unsubscribe, your data is permanently deleted
            from our systems.
          </p>
        </section>

        <section>
          <h2>Your Rights</h2>
          <p>You have the right to:</p>
          <ul>
            <li>
              <strong>Unsubscribe:</strong> Click the unsubscribe link in any
              email, reply STOP to any SMS, or visit{" "}
              <Link to="/unsubscribe">kingtidealert.com/unsubscribe</Link>
            </li>
            <li>
              <strong>Request deletion:</strong> Unsubscribing automatically
              deletes all your data
            </li>
          </ul>
        </section>

        <section>
          <h2>Contact</h2>
          <p>
            For questions about this privacy policy or your data, visit{" "}
            <Link to="/">kingtidealert.com</Link>.
          </p>
        </section>

        <Link to="/" className="back-link">
          Back to Home
        </Link>
      </div>
    </div>
  );
}
