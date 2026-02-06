import { Link } from "react-router-dom";
import { Coffee, ExternalLink } from "lucide-react";
import { Button } from "./ui/button";
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
    <footer className="w-full border-t border-border/50 bg-card/30 mt-8 sm:mt-16">
      <div className="mx-auto max-w-[720px] px-4 py-6 sm:py-8">
        <div className="flex flex-col gap-4 sm:gap-6">
          {/* Donation Button */}
          <div className="flex justify-center">
            <Button
              onClick={handleDonate}
              className="gap-2 bg-accent hover:bg-accent/90"
            >
              <Coffee className="h-4 w-4" />
              Buy me a coffee
            </Button>
          </div>

          {/* Attribution */}
          <div className="text-center text-xs sm:text-sm text-muted-foreground">
            <a
              href="https://tidesandcurrents.noaa.gov/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 hover:text-primary transition-colors"
            >
              Tide data from NOAA CO-OPS
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>

          {/* Legal Links */}
          <div className="flex flex-wrap justify-center gap-3 sm:gap-4 text-xs sm:text-sm text-muted-foreground">
            <Link to="/privacy-policy" className="hover:text-primary transition-colors">
              Privacy Policy
            </Link>
            <span>|</span>
            <Link to="/terms-and-conditions" className="hover:text-primary transition-colors">
              Terms
            </Link>
            <span>|</span>
            <Link to="/feedback" className="hover:text-primary transition-colors">
              Feedback
            </Link>
            <span>|</span>
            <Link to="/unsubscribe" className="hover:text-primary transition-colors">
              Unsubscribe
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
