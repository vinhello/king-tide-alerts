import { describe, it, expect, beforeEach } from "vitest";
import { captureSignupSource, getSignupSource, sourceFromLocation } from "../attribution";

describe("attribution", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("parses UTM parameters, landing path and an external referrer", () => {
    const source = sourceFromLocation(
      "?utm_source=nextdoor&utm_medium=social&utm_campaign=oct-flood",
      "/",
      "https://nextdoor.com/p/abc",
      "https://kingtidealert.com"
    );
    expect(source).toEqual({
      signup_referrer: "https://nextdoor.com/p/abc",
      signup_utm_source: "nextdoor",
      signup_utm_medium: "social",
      signup_utm_campaign: "oct-flood",
      signup_landing_path: "/",
    });
  });

  it("ignores a referrer from our own site and leaves missing values undefined", () => {
    const source = sourceFromLocation("", "/history", "https://kingtidealert.com/", "https://kingtidealert.com");
    expect(source.signup_referrer).toBeUndefined();
    expect(source.signup_utm_source).toBeUndefined();
    expect(source.signup_landing_path).toBe("/history");
  });

  it("truncates oversized values", () => {
    const long = "x".repeat(1000);
    const source = sourceFromLocation(`?utm_source=${long}`, "/", `https://a.com/${long}`, "https://kingtidealert.com");
    expect(source.signup_utm_source?.length).toBe(100);
    expect(source.signup_referrer?.length).toBe(500);
  });

  it("captures once per session and reads it back", () => {
    captureSignupSource();
    const first = getSignupSource();
    expect(first.signup_landing_path).toBeDefined();
    sessionStorage.setItem("kta.signupSource", JSON.stringify({ signup_utm_source: "kept" }));
    captureSignupSource();
    expect(getSignupSource().signup_utm_source).toBe("kept");
  });
});
