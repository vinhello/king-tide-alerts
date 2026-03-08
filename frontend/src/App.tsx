import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Confirmation from "./pages/Confirmation";
import Unsubscribe from "./pages/Unsubscribe";
import Thanks from "./pages/Thanks";
import PrivacyPolicy from "./pages/PrivacyPolicy";
import TermsAndConditions from "./pages/TermsAndConditions";
import Feedback from "./pages/Feedback";
import History from "./pages/History";
import NotFound from "./pages/NotFound";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/confirm/:token" element={<Confirmation />} />
        <Route path="/unsubscribe/:token?" element={<Unsubscribe />} />
        <Route path="/thanks" element={<Thanks />} />
        <Route path="/privacy-policy" element={<PrivacyPolicy />} />
        <Route path="/terms-and-conditions" element={<TermsAndConditions />} />
        <Route path="/feedback" element={<Feedback />} />
        <Route path="/history" element={<History />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
