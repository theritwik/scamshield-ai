import { describe, expect, it } from "vitest";
import { fmtCategory, scoreToSeverity, severityBadgeClass, severityColor } from "./risk";

describe("severity mapping", () => {
  it("matches the shared severity bands", () => {
    expect(scoreToSeverity(0)).toBe("Low");
    expect(scoreToSeverity(24)).toBe("Low");
    expect(scoreToSeverity(25)).toBe("Medium");
    expect(scoreToSeverity(49)).toBe("Medium");
    expect(scoreToSeverity(50)).toBe("High");
    expect(scoreToSeverity(74)).toBe("High");
    expect(scoreToSeverity(75)).toBe("Critical");
    expect(scoreToSeverity(100)).toBe("Critical");
  });

  it("uses red for critical and green for low", () => {
    expect(severityColor("Critical")).toBe("#e02d3c");
    expect(severityColor("Low")).toBe("#22c55e");
  });

  it("returns a badge class for every band", () => {
    for (const s of ["Low", "Medium", "High", "Critical"]) {
      expect(severityBadgeClass(s)).toContain("border");
    }
  });
});

describe("fmtCategory", () => {
  it("humanises snake_case categories", () => {
    expect(fmtCategory("digital_arrest_scam")).toBe("Digital arrest scam");
  });
});
