import { Link } from "react-router-dom";
import { Waves } from "lucide-react";
import Header from "../components/Header";
import Footer from "../components/Footer";

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 mx-auto max-w-[720px] px-4 py-12 sm:py-16">
        <div className="flex flex-col items-center justify-center text-center min-h-[400px]">
          <Waves className="h-12 w-12 sm:h-16 sm:w-16 text-muted-foreground mb-6" />
          <h1 className="text-3xl sm:text-4xl mb-4">404</h1>
          <p className="text-lg sm:text-xl text-muted-foreground mb-8 px-4">
            Page not found
          </p>
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-md bg-primary px-6 sm:px-8 py-2.5 sm:py-3 text-sm sm:text-base text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Return to Home
          </Link>
        </div>
      </main>

      <Footer />
    </div>
  );
}
