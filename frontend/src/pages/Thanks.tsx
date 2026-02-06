import { Link } from "react-router-dom";
import { Heart } from "lucide-react";
import Header from "../components/Header";
import Footer from "../components/Footer";

export default function Thanks() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 mx-auto max-w-[720px] px-4 py-12 sm:py-16">
        <div className="flex flex-col items-center justify-center text-center min-h-[300px]">
          <Heart className="h-12 w-12 sm:h-16 sm:w-16 text-accent mb-6" />
          <h1 className="text-2xl sm:text-3xl mb-4">Thank you!</h1>
          <p className="text-muted-foreground mb-8 max-w-md">
            Your support helps keep King Tide Alert running. We appreciate it!
          </p>
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-md bg-primary px-6 sm:px-8 py-2.5 sm:py-3 text-sm sm:text-base text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Back to home
          </Link>
        </div>
      </main>

      <Footer />
    </div>
  );
}
