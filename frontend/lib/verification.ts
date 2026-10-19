export type VerificationStatus = "SUPPORTED" | "UNSUPPORTED" | "UNKNOWN" | "SKIPPED";

export function verificationLabel(status?: VerificationStatus): string {
  switch (status) {
    case "SUPPORTED": return "Supported by sources";
    case "UNSUPPORTED": return "Answer could not be supported";
    case "UNKNOWN": return "Verification unavailable";
    case "SKIPPED": return "Source check not applicable";
    default: return "Not checked";
  }
}
