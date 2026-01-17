import { useState, useRef, useEffect, useCallback } from "react";
import { useMutation } from "@tanstack/react-query";
import api from "../api/axios";

const fetchTTS = async (text: string, category?: string) => {
    const response = await api.get("/tts", {
        params: {
            text,
            category: category || "default",
        },
        responseType: "blob",
    });
    if (response.data.size === 0) throw new Error("Empty audio blob received");
    return response.data;
};

export const useAudioTTS = (initialCategory: string | null) => {
    const [userInteracted, setUserInteracted] = useState(false);
    const ttsQueue = useRef<string[]>([]);
    const currentAudio = useRef<HTMLAudioElement | null>(null);

    const ttsMutation = useMutation({
        mutationFn: ({ text, category }: { text: string; category?: string }) =>
            fetchTTS(text, category),
        onSuccess: (blob) => {
            if (currentAudio.current) {
                currentAudio.current.pause();
                currentAudio.current.currentTime = 0;
            }

            const url = URL.createObjectURL(blob);
            const audio = new Audio(url);
            currentAudio.current = audio;

            audio.play().then(() => {
                audio.onended = () => {
                    URL.revokeObjectURL(url);
                    if (currentAudio.current === audio) {
                        currentAudio.current = null;
                    }
                };
            });
        },
        onError: (err) => {
            console.error("TTS error:", err);
        },
    });

    const speak = useCallback(
        (text: string, category?: string) => {
            if (!text) return;
            if (!userInteracted) {
                ttsQueue.current.push(text);
                return;
            }
            ttsMutation.mutate({ text, category });
        },
        [userInteracted, ttsMutation]
    );

    useEffect(() => {
        const handleFirstClick = () => setUserInteracted(true);
        document.addEventListener("click", handleFirstClick, { once: true });
        return () => document.removeEventListener("click", handleFirstClick);
    }, []);

    useEffect(() => {
        if (userInteracted && ttsQueue.current.length > 0) {
            ttsQueue.current.forEach((text) => speak(text, initialCategory || "default"));
            ttsQueue.current = [];
        }
    }, [userInteracted, speak, initialCategory]);

    useEffect(() => {
        const handleEscKey = (e: KeyboardEvent) => {
            if (e.key === "Escape" && currentAudio.current) {
                currentAudio.current.pause();
                currentAudio.current.currentTime = 0;
                currentAudio.current = null;
            }
        };
        document.addEventListener("keydown", handleEscKey);
        return () => document.removeEventListener("keydown", handleEscKey);
    }, []);

    return { speak };
};
