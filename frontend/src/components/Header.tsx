import { Link, useLocation, useNavigate } from "react-router-dom";
import { Waves } from "lucide-react";

function scrollToSection(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
}

export default function Header() {
  const location = useLocation();
  const navigate = useNavigate();
  const isHome = location.pathname === "/";

  function handleLogoClick(e: React.MouseEvent) {
    if (isHome) {
      e.preventDefault();
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  function handleSectionClick(e: React.MouseEvent, id: string) {
    e.preventDefault();
    if (isHome) {
      scrollToSection(id);
    } else {
      navigate(`/#${id}`);
    }
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/50 bg-card/80 backdrop-blur-md">
      <div className="mx-auto max-w-[720px] px-4 py-3 sm:py-4">
        <div className="flex items-center justify-between">
          <Link to="/" onClick={handleLogoClick} className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <Waves className="h-7 w-7 sm:h-8 sm:w-8 text-primary" />
            <span className="text-lg sm:text-xl font-medium text-foreground">King Tide Alert</span>
          </Link>
          <nav className="flex items-center gap-4 sm:gap-5">
            <a
              href="#status"
              onClick={(e) => handleSectionClick(e, "status")}
              className="hidden sm:inline text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Status
            </a>
            <a
              href="#tides"
              onClick={(e) => handleSectionClick(e, "tides")}
              className="hidden sm:inline text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Tides
            </a>
            <a
              href="#faq"
              onClick={(e) => handleSectionClick(e, "faq")}
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
