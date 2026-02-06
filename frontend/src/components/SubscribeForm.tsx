import { useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle, Loader2 } from "lucide-react";
import type { NotificationPreference, SubscribeRequest } from "../types";
import { subscribe } from "../services/api";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Checkbox } from "./ui/checkbox";

export default function SubscribeForm() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [preference, setPreference] =
    useState<NotificationPreference>("email");
  const [smsConsent, setSmsConsent] = useState(false);
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const showEmail = preference === "email" || preference === "both";
  const showPhone = preference === "sms" || preference === "both";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("loading");
    setErrorMessage("");

    const data: SubscribeRequest = {
      name,
      notification_preference: preference,
    };
    if (preference === "email" || preference === "both") {
      data.email = email;
    }
    if (preference === "sms" || preference === "both") {
      data.phone = phone;
    }

    try {
      await subscribe(data);
      setStatus("success");
    } catch (err: unknown) {
      setStatus("error");
      if (err && typeof err === "object" && "response" in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setErrorMessage(
          axiosErr.response?.data?.detail || "Something went wrong"
        );
      } else {
        setErrorMessage("Something went wrong");
      }
    }
  };

  if (status === "success") {
    return (
      <div className="w-full bg-card rounded-lg border border-border p-6 sm:p-8">
        <div className="flex flex-col items-center text-center gap-4">
          <CheckCircle className="h-10 w-10 sm:h-12 sm:w-12 text-secondary" />
          <h3 className="text-lg sm:text-xl">Check your inbox!</h3>
          <p className="text-sm sm:text-base text-muted-foreground">
            We sent a confirmation {showEmail ? "email" : "message"}. Click the link to activate your alerts.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-card rounded-lg border border-border p-4 sm:p-6">
      <h2 className="text-xl sm:text-2xl mb-4 sm:mb-6">Get Alerts</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Name Field */}
        <div className="space-y-2">
          <Label htmlFor="name">Name *</Label>
          <Input
            id="name"
            type="text"
            placeholder="Your name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>

        {/* Notification Preference */}
        <div className="space-y-2">
          <Label htmlFor="preference">Notify me via *</Label>
          <Select
            value={preference}
            onValueChange={(value: NotificationPreference) => setPreference(value)}
          >
            <SelectTrigger id="preference">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="email">Email</SelectItem>
              <SelectItem value="sms" disabled>
                SMS (coming soon)
              </SelectItem>
              <SelectItem value="both" disabled>
                Both (coming soon)
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Email Field */}
        {showEmail && (
          <div className="space-y-2">
            <Label htmlFor="email">Email *</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
        )}

        {/* Phone Field */}
        {showPhone && (
          <div className="space-y-2">
            <Label htmlFor="phone">Phone *</Label>
            <Input
              id="phone"
              type="tel"
              placeholder="(555) 123-4567"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              required
            />
          </div>
        )}

        {/* SMS Consent */}
        {showPhone && (
          <div className="flex items-start gap-3 pt-2">
            <Checkbox
              id="sms-consent"
              checked={smsConsent}
              onCheckedChange={(checked) => setSmsConsent(checked as boolean)}
              required
            />
            <label
              htmlFor="sms-consent"
              className="text-sm text-muted-foreground leading-snug cursor-pointer"
            >
              I agree to receive SMS alerts and understand that message and data rates may apply.
              I can opt out at any time by texting STOP. See our{" "}
              <Link to="/terms-and-conditions" className="text-primary hover:underline">
                Terms
              </Link>{" "}
              and{" "}
              <Link to="/privacy-policy" className="text-primary hover:underline">
                Privacy Policy
              </Link>
              .
            </label>
          </div>
        )}

        {/* Error Message */}
        {status === "error" && (
          <div className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-md p-3">
            {errorMessage}
          </div>
        )}

        {/* Submit Button */}
        <Button
          type="submit"
          disabled={status === "loading"}
          className="w-full"
        >
          {status === "loading" ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Subscribing...
            </>
          ) : (
            "Subscribe"
          )}
        </Button>
      </form>
    </div>
  );
}
