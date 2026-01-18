import { useMutation } from "@tanstack/react-query";
import api from "../api/axios";

export type SavePreferencePayload = {
  language: string;
  tone: string;
  name: string;
  preference: string;
};

export type SavePreferenceResponse = {
  success: boolean;
  message: string;
};

export const useSavePreference = () => {
  return useMutation<
    SavePreferenceResponse,
    Error,
    SavePreferencePayload
  >({
    mutationFn: async (payload: SavePreferencePayload) => {
      const res = await api.post<SavePreferenceResponse>(
        "/save-preference",
        payload
      );
      return res.data;
    },
  });
};
