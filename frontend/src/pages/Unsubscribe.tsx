import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { CheckCircle, XCircle, Loader2, Info } from "lucide-react";
import { unsubscribe } from "../services/api";
import Header from "../components/Header";
import Footer from "../components/Footer";

export default function Unsubscribe() {
  const { token } = useParams<{ token: string }>();
  const [status, setStatus] = useState<"loading" | "success" | "error" | "idle">(
    token ? "loading" : "idle"
  );
  const [message, setMessage] = useState("");

  useEffect(() => {
    async function doUnsubscribe() {
      if (!token) return;
      try {
        const response = await unsubscribe(token);
        setStatus("success");
        setMessage(response.message);
      } catch {
        setStatus("error");
        setMessage("Invalid or expired unsubscribe link.");
      }
    }
    doUnsubscribe();
  }, [token]);

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 mx-auto max-w-[720px] px-4 py-12 sm:py-16">
        <div className="flex flex-col items-center justify-center text-center min-h-[300px]">
          {status === "idle" && (
            <>
              <Info className="h-12 w-12 sm:h-16 sm:w-16 text-muted-foreground mb-6" />
              <h1 className="text-2xl sm:text-3xl mb-4">Unsubscribe</h1>
              <p className="text-muted-foreground mb-8">
                Use the link from your email or SMS to unsubscribe.
              </p>
              <Link
                to="/"
                className="inline-flex items-center justify-center rounded-md bg-primary px-6 sm:px-8 py-2.5 sm:py-3 text-sm sm:text-base text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                Back to home
              </Link>
            </>
          )}

          {status === "loading" && (
            <>
              <Loader2 className="h-12 w-12 sm:h-16 sm:w-16 text-primary mb-6 animate-spin" />
              <p className="text-lg text-muted-foreground">Processing your request...</p>
            </>
          )}

          {status === "success" && (
            <>
              <CheckCircle className="h-12 w-12 sm:h-16 sm:w-16 text-secondary mb-6" />
              <h1 className="text-2xl sm:text-3xl mb-4">Unsubscribed</h1>
              <p className="text-muted-foreground mb-8">{message}</p>
              <Link
                to="/"
                className="inline-flex items-center justify-center rounded-md bg-primary px-6 sm:px-8 py-2.5 sm:py-3 text-sm sm:text-base text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                Back to home
              </Link>
            </>
          )}

          {status === "error" && (
            <>
              <XCircle className="h-12 w-12 sm:h-16 sm:w-16 text-destructive mb-6" />
              <h1 className="text-2xl sm:text-3xl mb-4">Oops</h1>
              <p className="text-muted-foreground mb-8">{message}</p>
              <Link
                to="/"
                className="inline-flex items-center justify-center rounded-md bg-primary px-6 sm:px-8 py-2.5 sm:py-3 text-sm sm:text-base text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                Back to home
              </Link>
            </>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
