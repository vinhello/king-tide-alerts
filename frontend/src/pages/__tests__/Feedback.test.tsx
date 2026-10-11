import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BrowserRouter } from "react-router-dom";
import Feedback from "../Feedback";

vi.mock("../../services/api", () => ({
  submitFeedback: vi.fn(),
  createCheckoutSession: vi.fn(),
}));

import { submitFeedback } from "../../services/api";

const renderPage = () => render(<BrowserRouter><Feedback /></BrowserRouter>);

describe("Feedback page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the form with the send button disabled until a message is typed", async () => {
    const user = userEvent.setup();
    renderPage();

    const button = screen.getByRole("button", { name: /send feedback/i });
    expect(button).toBeDisabled();

    await user.type(screen.getByLabelText(/message/i), "The path flooded today.");
    expect(button).toBeEnabled();
  });

  it("submits through the API and shows a neutral confirmation", async () => {
    const user = userEvent.setup();
    vi.mocked(submitFeedback).mockResolvedValueOnce({ message: "Thanks, your feedback has been sent." });

    renderPage();
    await user.type(screen.getByLabelText(/message/i), "  The path flooded today.  ");
    await user.type(screen.getByLabelText(/subject/i), "Flooding");
    await user.click(screen.getByRole("button", { name: /send feedback/i }));

    await waitFor(() => {
      expect(screen.getByText(/your feedback has been sent/i)).toBeInTheDocument();
    });
    expect(submitFeedback).toHaveBeenCalledWith({
      message: "The path flooded today.",
      subject: "Flooding",
      email: undefined,
      website: undefined,
    });
    expect(screen.queryByRole("button", { name: /send feedback/i })).not.toBeInTheDocument();
  });

  it("shows a rate limit message when the API returns 429", async () => {
    const user = userEvent.setup();
    vi.mocked(submitFeedback).mockRejectedValueOnce({ response: { status: 429 } });

    renderPage();
    await user.type(screen.getByLabelText(/message/i), "Hello");
    await user.click(screen.getByRole("button", { name: /send feedback/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/too many messages/i);
    });
    // The form stays so the visitor can try again later.
    expect(screen.getByRole("button", { name: /send feedback/i })).toBeInTheDocument();
  });

  it("shows a generic error when the API fails", async () => {
    const user = userEvent.setup();
    vi.mocked(submitFeedback).mockRejectedValueOnce(new Error("network"));

    renderPage();
    await user.type(screen.getByLabelText(/message/i), "Hello");
    await user.click(screen.getByRole("button", { name: /send feedback/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/something went wrong/i);
    });
  });

  it("includes a honeypot field that is hidden from keyboard users", () => {
    renderPage();
    const honeypot = document.querySelector<HTMLInputElement>('input[name="website"]');
    expect(honeypot).not.toBeNull();
    expect(honeypot).toHaveAttribute("tabindex", "-1");
    expect(honeypot?.closest("[aria-hidden='true']")).not.toBeNull();
  });
});
