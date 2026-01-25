import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useSavePreference } from "./useSavePreference";

interface PreferenceData {
  language: string;
  tone: string;
  agentName: string;
  memoryNotes: string;
}

export const useSavePreferencesHandler = (closeSecondScreen: () => void) => {
  const navigate = useNavigate();
  const savePreference = useSavePreference();
  const [error, setError] = useState<string | null>(null);

  const handleSavePreferences = async (
    e: React.FormEvent<HTMLFormElement>,
    data: PreferenceData
  ) => {
    e.preventDefault();
    setError(null);

    try {
      await savePreference.mutateAsync({
        language: data.language,
        tone: data.tone,
        name: data.agentName,
        preference: data.memoryNotes,
      });

      closeSecondScreen();
      navigate("/login");
    } catch (err: any) {
      const message =
        err.response?.data?.message ||
        err.message ||
        "Failed to save preferences";
      setError(message);
    }
  };

  return { handleSavePreferences, error, setError };
};