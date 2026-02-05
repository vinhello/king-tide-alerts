import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import SubscribeForm from "../SubscribeForm";

// Mock the api module
vi.mock("../../services/api", () => ({
  subscribe: vi.fn(),
}));

import { subscribe } from "../../services/api";

describe("SubscribeForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders form fields correctly", () => {
    render(<SubscribeForm />);
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/notify me via/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /subscribe/i })).toBeInTheDocument();
  });

  it("shows email field when email selected", () => {
    render(<SubscribeForm />);
    // Email is default selection
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/phone/i)).not.toBeInTheDocument();
  });

  it("sms and both options are disabled with coming soon label", () => {
    render(<SubscribeForm />);
    const select = screen.getByLabelText(/notify me via/i);
    const smsOption = select.querySelector('option[value="sms"]') as HTMLOptionElement;
    const bothOption = select.querySelector('option[value="both"]') as HTMLOptionElement;

    expect(smsOption.disabled).toBe(true);
    expect(smsOption.textContent).toContain("coming soon");
    expect(bothOption.disabled).toBe(true);
    expect(bothOption.textContent).toContain("coming soon");
  });

  it("submits successfully and shows confirmation message", async () => {
    const user = userEvent.setup();
    vi.mocked(subscribe).mockResolvedValueOnce({
      id: "123",
      name: "Test",
      email: "test@example.com",
      phone: null,
      notification_preference: "email",
      confirmed: false,
      created_at: new Date().toISOString(),
    });

    render(<SubscribeForm />);

    await user.type(screen.getByLabelText(/name/i), "Test");
    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.click(screen.getByRole("button", { name: /subscribe/i }));

    await waitFor(() => {
      expect(screen.getByText(/check your inbox/i)).toBeInTheDocument();
    });
  });

  it("shows error on failed submission", async () => {
    const user = userEvent.setup();
    vi.mocked(subscribe).mockRejectedValueOnce({
      response: { data: { detail: "Email already subscribed" } },
    });

    render(<SubscribeForm />);

    await user.type(screen.getByLabelText(/name/i), "Test");
    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.click(screen.getByRole("button", { name: /subscribe/i }));

    await waitFor(() => {
      expect(screen.getByText(/email already subscribed/i)).toBeInTheDocument();
    });
  });
});
