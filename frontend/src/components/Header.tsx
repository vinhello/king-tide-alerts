import { Link } from "react-router-dom";
import { Waves } from "lucide-react";

export default function Header() {
  return (
    <header className="w-full border-b border-border/50 bg-card/50 backdrop-blur-sm">
      <div className="mx-auto max-w-[720px] px-4 py-3 sm:py-4">
        <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <Waves className="h-7 w-7 sm:h-8 sm:w-8 text-primary" />
          <span className="text-lg sm:text-xl font-medium text-foreground">King Tide Alerts</span>
        </Link>
      </div>
    </header>
  );
}
