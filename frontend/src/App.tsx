import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Confirmation from "./pages/Confirmation";
import Unsubscribe from "./pages/Unsubscribe";
import Thanks from "./pages/Thanks";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/confirm/:token" element={<Confirmation />} />
        <Route path="/unsubscribe/:token?" element={<Unsubscribe />} />
        <Route path="/thanks" element={<Thanks />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
