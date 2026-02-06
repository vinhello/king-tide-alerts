import { Link } from "react-router-dom";
import Header from "../components/Header";
import Footer from "../components/Footer";

export default function TermsAndConditions() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 mx-auto max-w-[720px] px-4 py-8 sm:py-12">
        <div className="bg-card rounded-lg border border-border p-6 sm:p-8">
          <div className="prose">
            <h1>Terms and Conditions</h1>
            <p className="text-sm text-muted-foreground">Last updated: February 2026</p>

            <h2>Program Information</h2>
            <ul>
              <li>
                <strong>Program name:</strong> King Tide Alerts
              </li>
              <li>
                <strong>Description:</strong> SMS and email alerts for high tides
                that may cause flooding on the Bay Trail bike path through
                Sausalito
              </li>
              <li>
                <strong>Message frequency:</strong> Up to 2 messages per tide
                event (a 7-day advance notice and a 48-hour reminder)
              </li>
            </ul>

            <h2>SMS Terms</h2>
            <p>By subscribing to SMS alerts, you agree to the following:</p>
            <ul>
              <li>
                <strong>Message and data rates may apply.</strong> Standard
                messaging rates from your carrier apply to messages sent to and
                from our service.
              </li>
              <li>
                <strong>Opt-out:</strong> Reply <strong>STOP</strong> to any
                message to unsubscribe from SMS alerts.
              </li>
              <li>
                <strong>Help:</strong> Reply <strong>HELP</strong> for assistance
                or visit{" "}
                <Link to="/">kingtidealert.com</Link>.
              </li>
            </ul>

            <h2>Service Description</h2>
            <p>
              King Tide Alerts uses tide prediction data from NOAA to notify
              subscribers before high tides that may cause flooding in Sausalito.
              Alerts are sent approximately 7 days and 48 hours before predicted
              high tide events.
            </p>
            <p>
              <strong>Disclaimer:</strong> Flooding times are estimates based on
              predicted tide data. Actual conditions may vary due to weather,
              wind, and other factors. This service is informational only. Always
              follow official guidance from the National Weather Service and local
              authorities.
            </p>

            <h2>Eligibility</h2>
            <p>
              This service is intended for individuals who live, work, or commute
              in the San Francisco Bay Area and want to be notified about high
              tide events in Sausalito.
            </p>

            <h2>Privacy</h2>
            <p>
              Your information is used only to deliver tide alerts. We do not
              share your data with third parties for marketing purposes. See our{" "}
              <Link to="/privacy-policy">Privacy Policy</Link> for details.
            </p>

            <h2>Contact</h2>
            <p>
              For support or questions, visit{" "}
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
