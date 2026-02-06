import { useState, type FormEvent } from "react";
import { Mail, MessageCircle } from "lucide-react";
import Header from "../components/Header";
import Footer from "../components/Footer";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";

export default function Feedback() {
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();

    // Create mailto link with subject and body
    const mailtoLink = `mailto:info@kingtidealert.com?subject=${encodeURIComponent(
      subject || "King Tide Alerts Feedback"
    )}&body=${encodeURIComponent(
      message + (email ? `\n\nReply to: ${email}` : "")
    )}`;

    window.location.href = mailtoLink;
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
              Have suggestions, questions, or issues with King Tide Alerts? We'd love to hear from you.
            </p>
          </div>

          {/* Feedback Form */}
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
                <Label htmlFor="subject">
                  Subject
                </Label>
                <Input
                  id="subject"
                  type="text"
                  placeholder="Brief description of your feedback"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
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
                  rows={8}
                  className="flex w-full rounded-md border border-input bg-input-background px-3 py-2 text-base placeholder:text-muted-foreground focus-visible:outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50 resize-none"
                />
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                className="w-full sm:w-auto"
                disabled={!message.trim()}
              >
                <Mail className="h-4 w-4 mr-2" />
                Send Feedback
              </Button>

              <p className="text-xs text-muted-foreground">
                Clicking "Send Feedback" will open your default email client with your message pre-filled.
              </p>
            </form>
          </div>

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
