import { Waves, TrendingUp, MapPin, AlertTriangle, HelpCircle } from "lucide-react";
import Header from "../components/Header";
import Footer from "../components/Footer";
import SubscribeForm from "../components/SubscribeForm";
import TideChart from "../components/TideChart";

const FAQ_ITEMS = [
  {
    question: "How does this service work?",
    answer:
      "We monitor NOAA tide predictions for the Sausalito station daily. When tides are forecasted to exceed 6.0 feet MLLW, we send you an alert 7 days before and another reminder 48 hours before the flooding event.",
  },
  {
    question: "What's the difference between a high tide alert and a king tide alert?",
    answer:
      "We send alerts for any tide predicted to reach 6.0 feet MLLW, which is when path flooding begins. Tides reaching 6.5 feet or higher are classified as king tides—the most extreme events—and are called out specifically in the alert.",
  },
  {
    question: "How accurate are the predictions?",
    answer:
      "NOAA tide predictions are highly accurate for timing and height under normal conditions. However, weather factors like storms, strong winds, and barometric pressure changes can cause actual water levels to differ. Always check current conditions before heading out.",
  },
  {
    question: "When do king tides typically occur?",
    answer:
      "In the San Francisco Bay Area, king tides most commonly occur from November through February, when the sun and moon's gravitational pull combine with the Earth's closest orbital approach. Exact dates vary each year.",
  },
  {
    question: "Is this service free?",
    answer:
      "Yes! King Tide Alert is a free community service. There are no hidden costs or premium tiers. We built this to help cyclists and pedestrians safely navigate the Bay Trail.",
  },
  {
    question: "How do I unsubscribe?",
    answer:
      "Every email includes an unsubscribe link at the bottom. You can also visit our unsubscribe page at any time to remove your email address from the alert list.",
  },
  {
    question: "Where does the tide data come from?",
    answer:
      "All tide data comes from the National Oceanic and Atmospheric Administration (NOAA). We use predictions from the Sausalito tide station (Station 9414806), which is the closest station to the affected path sections.",
  },
  {
    question: "What should I do if the path is flooded?",
    answer:
      "Use the Bridgeway Boulevard sidewalk as an alternate route, or time your trip to avoid the flooding window (approximately 2 hours before and after peak tide). Never attempt to ride or walk through deep floodwater.",
  },
  {
    question: "Does this cover other Bay Trail sections?",
    answer:
      "Currently, King Tide Alert focuses specifically on the Mill Valley–Sausalito path along Richardson Bay. This is one of the most flood-prone sections of the Bay Trail. We may expand coverage in the future.",
  },
  {
    question: "Will SMS alerts be available?",
    answer:
      "SMS alert support is in progress. We're working through the carrier registration process required to send text messages. For now, email alerts are the best way to stay informed.",
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

          {/* What Are King Tides Section */}
          <section className="py-8 sm:py-12">
            <div className="flex flex-col items-center text-center mb-6">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-3">
                <TrendingUp className="h-6 w-6 text-primary" />
              </div>
              <h2 className="text-xl sm:text-2xl">What Are King Tides?</h2>
            </div>
            <div className="bg-card rounded-lg border border-border p-6 sm:p-8 space-y-4">
              <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                King tides are exceptionally high tides that occur when the sun, moon, and Earth are in
                close alignment. This gravitational pull creates tides significantly higher than normal,
                pushing water levels well above average along coastlines and into low-lying areas.
              </p>
              <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                In the San Francisco Bay Area, king tides typically occur during the winter months—most
                commonly from November through February. During these events, tides in Richardson Bay
                near Sausalito can rise high enough to overtop the Bay Trail bike path, making sections
                impassable for cyclists and pedestrians.
              </p>
              <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                We send alerts when tides are predicted to reach <strong>6.0 feet MLLW</strong> (Mean
                Lower Low Water), the threshold at which path flooding begins. Tides reaching{" "}
                <strong>6.5 feet or higher</strong> are classified as king tides—the most extreme events
                that can bring significant flooding to the trail.
              </p>
              <div className="bg-muted rounded-lg p-4 sm:p-5 space-y-2">
                <p className="text-sm font-medium text-foreground">Key facts about king tides:</p>
                <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                  <li>They are completely predictable and happen every year</li>
                  <li>They are driven by astronomical cycles, not weather</li>
                  <li>Scientists consider them a preview of future daily sea levels due to climate change</li>
                </ul>
              </div>
            </div>
          </section>

          {/* The Mill Valley-Sausalito Path Section */}
          <section className="py-8 sm:py-12">
            <div className="flex flex-col items-center text-center mb-6">
              <div className="w-12 h-12 rounded-full bg-secondary/10 flex items-center justify-center mb-3">
                <MapPin className="h-6 w-6 text-secondary" />
              </div>
              <h2 className="text-xl sm:text-2xl">The Mill Valley–Sausalito Path</h2>
            </div>
            <div className="bg-card rounded-lg border border-border p-6 sm:p-8 space-y-4">
              <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                The Mill Valley–Sausalito Multiuse Path is a key segment of the San Francisco Bay
                Trail, a network of cycling and walking paths that rings the Bay. This scenic route
                runs along the Sausalito waterfront and Richardson Bay, connecting Mill Valley to
                downtown Sausalito.
              </p>
              <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                The path is heavily used by bike commuters traveling to and from the Golden Gate Bridge
                and the Sausalito ferry terminal, as well as recreational cyclists, joggers, and
                walkers enjoying the waterfront scenery. On weekends and during commute hours, the
                trail sees steady traffic.
              </p>
              <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                Several low-lying sections of the path sit just above sea level, particularly near
                Bothin Marsh, the Sausalito Boardwalk, and Dunphy Park. These areas are the first to
                flood during high tide events, forcing trail users to find alternate routes or turn
                back.
              </p>
            </div>
          </section>

          {/* Flooding Information Section */}
          <section className="py-8 sm:py-12">
            <div className="flex flex-col items-center text-center mb-6">
              <div className="w-12 h-12 rounded-full bg-accent/10 flex items-center justify-center mb-3">
                <AlertTriangle className="h-6 w-6 text-accent" />
              </div>
              <h2 className="text-xl sm:text-2xl">Flooding Information</h2>
            </div>
            <div className="bg-card rounded-lg border border-border p-6 sm:p-8 space-y-6">
              <div className="space-y-3">
                <h3 className="text-base font-medium">What Happens During Flooding</h3>
                <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                  When high tides exceed 6.0 feet, water overtops the path in low-lying sections.
                  Flooding typically lasts around 4 hours centered on the peak tide—roughly 2 hours
                  before and 2 hours after. Water depth varies from a few inches to knee-deep during
                  the most extreme king tide events.
                </p>
              </div>
              <div className="space-y-3">
                <h3 className="text-base font-medium">Alternate Routes</h3>
                <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                  When the path is flooded, cyclists and pedestrians can use the Bridgeway Boulevard
                  sidewalk as an alternate route through Sausalito. You can also time your ride to
                  avoid the flooding window—our alerts include the estimated peak time so you can
                  plan around it.
                </p>
              </div>
              <div className="border-l-4 border-accent bg-accent/5 rounded-r-lg p-4">
                <p className="text-sm font-medium text-foreground mb-1">Important</p>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Flooding estimates are based on NOAA tide predictions and may vary due to weather
                  conditions such as storms, wind, and barometric pressure. Always exercise caution
                  and check current conditions before heading out.
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
