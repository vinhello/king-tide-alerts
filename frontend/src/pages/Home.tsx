import { Waves, TrendingUp, AlertTriangle, HelpCircle } from "lucide-react";
import Header from "../components/Header";
import Footer from "../components/Footer";
import SubscribeForm from "../components/SubscribeForm";
import TideChart from "../components/TideChart";

const FAQ_ITEMS = [
  {
    question: "How does this service work?",
    answer:
      "We monitor NOAA tide predictions for the Sausalito station (9414806) daily. When tides are forecasted to exceed 6.0 feet MLLW, we send you an alert 7 days before and a reminder 48 hours before the event.",
  },
  {
    question: "What's the difference between a high tide alert and a king tide alert?",
    answer:
      "We alert for any tide predicted to reach 6.0 feet MLLW, when path flooding begins. Tides at 6.5 feet or higher are classified as king tides and called out specifically in the alert.",
  },
  {
    question: "How accurate are the predictions?",
    answer:
      "NOAA tide predictions are highly accurate under normal conditions. Weather factors like storms, wind, and pressure changes can cause actual levels to differ, so always check conditions before heading out.",
  },
  {
    question: "When do king tides typically occur?",
    answer:
      "In the Bay Area, king tides most commonly occur from November through February, when the sun and moon's gravitational pull combine with the Earth's closest orbital approach.",
  },
  {
    question: "Is this free? How do I unsubscribe?",
    answer:
      "Yes, completely free with no hidden costs. Every email includes an unsubscribe link, or visit our unsubscribe page anytime.",
  },
  {
    question: "What should I do if the path is flooded?",
    answer:
      "Use the Bridgeway Boulevard sidewalk as an alternate route, or time your trip outside the flooding window (~2 hours before and after peak tide). Never ride or walk through deep floodwater.",
  },
  {
    question: "What area does this cover?",
    answer:
      "King Tide Alert focuses on the Mill Valley–Sausalito path along Richardson Bay—one of the most flood-prone sections of the Bay Trail.",
  },
];

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
                King Tide Alert
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

          {/* King Tides & the Bay Trail Section */}
          <section className="py-8 sm:py-12">
            <div className="flex flex-col items-center text-center mb-6">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-3">
                <TrendingUp className="h-6 w-6 text-primary" />
              </div>
              <h2 className="text-xl sm:text-2xl">King Tides & the Bay Trail</h2>
            </div>
            <div className="bg-card rounded-lg border border-border p-6 sm:p-8 space-y-4">
              <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                King tides are the highest tides of the year, caused by the alignment of the sun, moon,
                and Earth. In the Bay Area they typically occur from November through February, pushing
                water levels high enough to overtop low-lying sections of the Bay Trail near Sausalito.
              </p>
              <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                The Mill Valley–Sausalito Multiuse Path runs along Richardson Bay and is popular with
                bike commuters heading to the Golden Gate Bridge and ferry. Sections near Bothin Marsh,
                the Sausalito Boardwalk, and Dunphy Park sit close to sea level and are the first to
                flood. We send alerts at <strong>6.0 ft MLLW</strong> (flooding threshold) and flag
                tides at <strong>6.5 ft+</strong> as king tides.
              </p>
              <div className="bg-muted rounded-lg p-4 sm:p-5 space-y-2">
                <p className="text-sm font-medium text-foreground">Key facts:</p>
                <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                  <li>Completely predictable—they happen every year on a known schedule</li>
                  <li>Driven by astronomical cycles, not weather</li>
                  <li>Considered a preview of future daily sea levels due to climate change</li>
                </ul>
              </div>
            </div>
          </section>

          {/* Flooding Information Section */}
          <section className="py-8 sm:py-12">
            <div className="flex flex-col items-center text-center mb-6">
              <div className="w-12 h-12 rounded-full bg-accent/10 flex items-center justify-center mb-3">
                <AlertTriangle className="h-6 w-6 text-accent" />
              </div>
              <h2 className="text-xl sm:text-2xl">When Flooding Happens</h2>
            </div>
            <div className="bg-card rounded-lg border border-border p-6 sm:p-8 space-y-4">
              <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                When tides exceed 6.0 feet, water overtops the path in low-lying sections. Flooding
                typically lasts ~4 hours around the peak (2 hours before and after), with depths
                ranging from inches to knee-deep during the most extreme events. The Bridgeway
                Boulevard sidewalk works as an alternate route, or you can time your ride outside
                the flooding window using the peak time in our alerts.
              </p>
              <div className="border-l-4 border-accent bg-accent/5 rounded-r-lg p-4">
                <p className="text-sm font-medium text-foreground mb-1">Important</p>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Flooding estimates are based on NOAA predictions and may vary due to storms, wind,
                  and pressure changes. Always check current conditions before heading out.
                </p>
              </div>
            </div>
          </section>

          {/* FAQ Section */}
          <section className="py-8 sm:py-12">
            <div className="flex flex-col items-center text-center mb-6">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-3">
                <HelpCircle className="h-6 w-6 text-primary" />
              </div>
              <h2 className="text-xl sm:text-2xl">Frequently Asked Questions</h2>
            </div>
            <div className="bg-card rounded-lg border border-border p-6 sm:p-8">
              <div className="divide-y divide-border">
                {FAQ_ITEMS.map((item, index) => (
                  <div key={index} className={index === 0 ? "pb-5" : index === FAQ_ITEMS.length - 1 ? "pt-5" : "py-5"}>
                    <h3 className="text-base font-medium mb-2">{item.question}</h3>
                    <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">{item.answer}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  );
}
