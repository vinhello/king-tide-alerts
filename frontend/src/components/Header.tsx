import { Link } from "react-router-dom";
import { Waves } from "lucide-react";

export default function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/50 bg-card/80 backdrop-blur-md">
      <div className="mx-auto max-w-[720px] px-4 py-3 sm:py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <Waves className="h-7 w-7 sm:h-8 sm:w-8 text-primary" />
            <span className="text-lg sm:text-xl font-medium text-foreground">King Tide Alert</span>
          </Link>
          <nav className="flex items-center gap-4 sm:gap-5">
            <a
              href="#status"
              className="hidden sm:inline text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Status
            </a>
            <a
              href="#tides"
              className="hidden sm:inline text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Tides
            </a>
            <a
              href="#faq"
              className="hidden sm:inline text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              FAQ
            </a>
            <Link
              to="/history"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              History
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
}
