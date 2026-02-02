import Hero from "../components/Hero";
import SubscribeForm from "../components/SubscribeForm";
import TideChart from "../components/TideChart";
import Footer from "../components/Footer";

export default function Home() {
  return (
    <div className="page">
      <Hero />
      <SubscribeForm />
      <TideChart />
      <Footer />
    </div>
  );
}
