import { Link } from "react-router-dom";
import Header from "../components/Header";
import Footer from "../components/Footer";

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 mx-auto max-w-[720px] px-4 py-8 sm:py-12">
        <div className="bg-card rounded-lg border border-border p-6 sm:p-8">
          <div className="prose">
            <h1>Privacy Policy</h1>
            <p className="text-sm text-muted-foreground">Last updated: February 2026</p>

            <h2>What We Collect</h2>
            <p>
              When you subscribe to King Tide Alert, we collect the following
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

            <h2>Data Retention</h2>
            <p>
              We retain your subscription information only while your subscription
              is active. When you unsubscribe, your data is permanently deleted
              from our systems.
            </p>

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

            <h2>Contact</h2>
            <p>
              For questions about this privacy policy or your data, visit{" "}
              <Link to="/">kingtidealert.com</Link>.
            </p>
          </div>

          <div className="mt-8 pt-6 border-t border-border">
            <Link
              to="/"
              className="inline-flex items-center justify-center rounded-md bg-primary px-6 py-2.5 text-sm text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              Back to Home
            </Link>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
