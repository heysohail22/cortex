export interface LocalProfile {
  name: string;
  email: string;
}
export const DEFAULT_PROFILE: LocalProfile = {
  name: "My workspace",
  email: "",
};
export const PROFILE_EVENT = "cortex-profile-updated";
export function readProfile(): LocalProfile {
  try {
    const stored = JSON.parse(localStorage.getItem("cortex_profile") || "null");
    return stored &&
      typeof stored.name === "string" &&
      typeof stored.email === "string"
      ? stored
      : DEFAULT_PROFILE;
  } catch {
    return DEFAULT_PROFILE;
  }
}
