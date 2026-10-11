import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { CheckCircle, Loader2, Mail, MessageCircle } from "lucide-react";
import Header from "../components/Header";
import Footer from "../components/Footer";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { submitFeedback } from "../services/api";

type Status = "idle" | "loading" | "success" | "error";

const GENERIC_ERROR = "Something went wrong sending your feedback. Please try again.";
const RATE_LIMIT_ERROR = "Too many messages from your connection. Please try again later.";

function errorMessageFor(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const axiosErr = err as { response?: { status?: number; data?: { detail?: unknown } } };
    if (axiosErr.response?.status === 429) return RATE_LIMIT_ERROR;
    const detail = axiosErr.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return GENERIC_ERROR;
}

export default function Feedback() {
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState("");
  // Honeypot: hidden from people, filled in by bots. The backend drops
  // submissions where it is non-empty.
  const [website, setWebsite] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setStatus("loading");
    setErrorMessage("");

    try {
      await submitFeedback({
        message: message.trim(),
        subject: subject.trim() || undefined,
        email: email.trim() || undefined,
        website: website || undefined,
      });
      setStatus("success");
    } catch (err: unknown) {
      setStatus("error");
      setErrorMessage(errorMessageFor(err));
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1">
        <div className="mx-auto max-w-[720px] px-4 py-8 sm:py-12">
          {/* Header */}
          <div className="text-center mb-8 sm:mb-12">
            <div className="inline-flex items-center justify-center w-12 h-12 sm:w-16 sm:h-16 rounded-full bg-primary/10 mb-4">
              <MessageCircle className="h-6 w-6 sm:h-8 sm:w-8 text-primary" />
            </div>
            <h1 className="text-2xl sm:text-3xl mb-3">Send Us Feedback</h1>
            <p className="text-muted-foreground max-w-lg mx-auto">
              Have suggestions, questions, or issues with King Tide Alert? We'd love to hear from you.
            </p>
          </div>

          {status === "success" ? (
            <div className="bg-card border border-border rounded-lg p-6 sm:p-8 shadow-sm">
              <div className="flex flex-col items-center text-center gap-4">
                <CheckCircle className="h-10 w-10 sm:h-12 sm:w-12 text-secondary" />
                <h2 className="text-lg sm:text-xl">Thanks, your feedback has been sent.</h2>
                <Link
                  to="/"
                  className="inline-flex items-center justify-center rounded-md bg-primary px-6 py-2.5 text-sm text-primary-foreground hover:bg-primary/90 transition-colors"
                >
                  Back to home
                </Link>
              </div>
            </div>
          ) : (
            <div className="bg-card border border-border rounded-lg p-6 sm:p-8 shadow-sm">
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Your Email (optional) */}
                <div className="space-y-2">
                  <Label htmlFor="email" className="flex items-center gap-2">
                    <Mail className="h-4 w-4" />
                    Your Email <span className="text-muted-foreground text-sm">(optional)</span>
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="your.email@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="bg-input-background"
                  />
                  <p className="text-xs text-muted-foreground">
                    Include your email if you'd like a response
                  </p>
                </div>

                {/* Subject */}
                <div className="space-y-2">
                  <Label htmlFor="subject">Subject</Label>
                  <Input
                    id="subject"
                    type="text"
                    placeholder="Brief description of your feedback"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    maxLength={200}
                    className="bg-input-background"
                  />
                </div>

                {/* Message */}
                <div className="space-y-2">
                  <Label htmlFor="message">
                    Message <span className="text-destructive">*</span>
                  </Label>
                  <textarea
                    id="message"
                    placeholder="Tell us about your experience, suggestions, or issues..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    required
                    maxLength={5000}
                    rows={8}
                    className="flex w-full rounded-md border border-input bg-input-background px-3 py-2 text-base placeholder:text-muted-foreground focus-visible:outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50 resize-none"
                  />
                </div>

                {/* Honeypot: visually hidden and skipped by keyboard and screen readers */}
                <div className="absolute -left-[10000px] top-auto h-px w-px overflow-hidden" aria-hidden="true">
                  <label htmlFor="website">Website</label>
                  <input
                    id="website"
                    name="website"
                    type="text"
                    tabIndex={-1}
                    autoComplete="off"
                    value={website}
                    onChange={(e) => setWebsite(e.target.value)}
                  />
                </div>

                {/* Error Message */}
                {status === "error" && (
                  <div
                    role="alert"
                    className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-md p-3"
                  >
                    {errorMessage}
                  </div>
                )}

                {/* Submit Button */}
                <Button
                  type="submit"
                  className="w-full sm:w-auto"
                  disabled={status === "loading" || !message.trim()}
                >
                  {status === "loading" ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Mail className="h-4 w-4 mr-2" />
                      Send Feedback
                    </>
                  )}
                </Button>
              </form>
            </div>
          )}

          {/* Additional Information */}
          <div className="mt-8 p-4 sm:p-6 bg-muted/50 rounded-lg border border-border/50">
            <h2 className="text-lg mb-2">What kind of feedback are we looking for?</h2>
            <ul className="text-sm text-muted-foreground space-y-2">
              <li className="flex gap-2">
                <span className="text-primary">-</span>
                <span>Bug reports or technical issues</span>
              </li>
              <li className="flex gap-2">
                <span className="text-primary">-</span>
                <span>Feature requests or suggestions</span>
              </li>
              <li className="flex gap-2">
                <span className="text-primary">-</span>
                <span>Questions about the service</span>
              </li>
              <li className="flex gap-2">
                <span className="text-primary">-</span>
                <span>General comments about the website or alerts</span>
              </li>
            </ul>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
