import { createCheckoutSession } from "../services/api";

export default function Footer() {
  const handleDonate = async () => {
    try {
      const { checkout_url } = await createCheckoutSession();
      window.location.href = checkout_url;
    } catch {
      alert("Unable to start checkout. Please try again.");
    }
  };

  return (
    <footer className="footer">
      <div className="footer-content">
        <button className="donate-button" onClick={handleDonate}>
          Buy me a coffee
        </button>
        <p className="attribution">
          Tide data from{" "}
          <a
            href="https://tidesandcurrents.noaa.gov/"
            target="_blank"
            rel="noopener noreferrer"
          >
            NOAA CO-OPS
          </a>
        </p>
        <p className="footer-links">
          <a href="/unsubscribe">Unsubscribe</a>
        </p>
      </div>
    </footer>
  );
}
