import { Waves } from "lucide-react";
import Header from "../components/Header";
import Footer from "../components/Footer";
import SubscribeForm from "../components/SubscribeForm";
import TideChart from "../components/TideChart";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative w-full bg-gradient-to-br from-[#0A7EA4] via-[#0D9488] to-[#0EA5E9] text-white overflow-hidden">
          {/* Wave pattern background */}
          <div className="absolute inset-0 opacity-10">
            <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
              <pattern id="waves" x="0" y="0" width="100" height="100" patternUnits="userSpaceOnUse">
                <path
                  d="M0 50 Q 25 25, 50 50 T 100 50"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                />
                <path
                  d="M0 70 Q 25 45, 50 70 T 100 70"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                />
              </pattern>
              <rect width="100%" height="100%" fill="url(#waves)" />
            </svg>
          </div>

          <div className="relative mx-auto max-w-[720px] px-4 py-12 sm:py-16 md:py-24">
            <div className="flex flex-col items-center text-center gap-3 sm:gap-4">
              <Waves className="h-12 w-12 sm:h-16 sm:w-16 mb-2" />
              <h1 className="text-3xl sm:text-4xl md:text-5xl leading-tight">
                King Tide Alerts
              </h1>
              <p className="text-base sm:text-lg md:text-xl text-white/90 max-w-2xl leading-relaxed">
                Get notified before high tides flood the Bay Trail bike path through Sausalito, California.
                Free alerts sent 7 days and 48 hours before flooding events.
              </p>
            </div>
          </div>
        </section>

        <div className="mx-auto max-w-[720px] px-4">
          {/* Subscribe Form Section */}
          <section className="py-8 sm:py-12">
            <SubscribeForm />
          </section>

          {/* Tide Chart Section */}
          <section className="py-8 sm:py-12">
            <TideChart />
          </section>
        </div>
      </main>

      <Footer />
    </div>
  );
}
